"""Execute documentation notebooks without modifying their inputs."""

import hashlib
import re
import shutil
import sys
from pathlib import Path

import pytest

import pygaps

EXAMPLES = Path(__file__).resolve().parents[2] / 'docs' / 'examples'
NOTEBOOKS = sorted(EXAMPLES.glob('*.ipynb'))
if not NOTEBOOKS:
    raise FileNotFoundError(f'No documentation notebooks found in {EXAMPLES}.')


def file_hashes(directory):
    return {path.relative_to(directory): hashlib.sha256(path.read_bytes()).hexdigest() for path in directory.rglob('*') if path.is_file()}


def assert_no_error_outputs(notebook):
    for index, cell in enumerate(notebook.cells):
        for output in cell.get('outputs', []):
            assert output.output_type != 'error', f'Cell {index}: {output}'
            if output.output_type == 'stream':
                assert not re.search(
                    r'Traceback \(most recent call last\)|\b(?:\w*Error|Exception):',
                    output.text,
                ), f'Cell {index} printed an unexpected error:\n{output.text}'


@pytest.mark.documentation
@pytest.mark.parametrize('notebook_path', NOTEBOOKS, ids=lambda path: path.stem)
def test_notebook(notebook_path, tmp_path, monkeypatch):
    import nbformat
    from jupyter_client import KernelManager
    from nbclient import NotebookClient

    working = tmp_path / 'examples'
    shutil.copytree(EXAMPLES, working)
    original_inputs = file_hashes(working / 'data')
    source_inputs = file_hashes(EXAMPLES)
    database = Path(pygaps.DATABASE)
    original_database = hashlib.sha256(database.read_bytes()).hexdigest()
    disposable_database = tmp_path / 'default.db'
    shutil.copyfile(database, disposable_database)
    monkeypatch.setenv('MPLBACKEND', 'Agg')

    notebook = nbformat.read(notebook_path, as_version=4)
    nbformat.validate(notebook)
    assert_no_error_outputs(notebook)
    notebook = nbformat.v4.upgrade(notebook)
    for cell in notebook.cells:
        if cell.cell_type == 'code':
            cell.execution_count = None
            cell.outputs = []
    notebook.cells.insert(
        0,
        nbformat.v4.new_code_cell(
            "from pathlib import Path\n"
            "import sys\n"
            f"assert Path(sys.executable).resolve() == Path({sys.executable!r}).resolve()\n"
            "import pygaps, pygaps.data, pygaps.parsing.sqlite\n"
            f"pygaps.DATABASE = Path({str(disposable_database)!r})\n"
            "pygaps.data.DATABASE = pygaps.DATABASE\n"
            "pygaps.parsing.sqlite.DATABASE = pygaps.DATABASE\n"
        ),
    )
    notebook.cells.append(
        nbformat.v4.new_code_cell(
            "import matplotlib.pyplot as plt\nfor number in plt.get_fignums():\n    plt.figure(number).canvas.draw()\nplt.close('all')\n"
        )
    )
    nbformat.validate(notebook)
    manager = KernelManager(kernel_name='python3')
    # Do not let an unrelated system kernelspec select another environment.
    manager.kernel_spec.argv = [
        sys.executable,
        '-m',
        'ipykernel_launcher',
        '-f',
        '{connection_file}',
    ]
    client = NotebookClient(
        notebook,
        km=manager,
        timeout=180,
        allow_errors=False,
        record_timing=False,
        resources={'metadata': {'path': str(working)}},
    )
    try:
        with client.setup_kernel(cwd=str(working), cleanup_kc=True):
            client.execute()
    finally:
        nbformat.write(notebook, tmp_path / 'executed.ipynb')
        assert file_hashes(working / 'data') == original_inputs, 'Notebook modified its input fixtures.'
        assert file_hashes(EXAMPLES) == source_inputs, 'Notebook modified the source examples.'
        assert hashlib.sha256(database.read_bytes()).hexdigest() == original_database, 'Packaged database was modified.'

    assert_no_error_outputs(notebook)
