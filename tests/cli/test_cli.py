import os
import subprocess

import pytest

import pygaps
import pygaps.parsing as pgp


def capture(command, **extra):
    """Run and capture the output of a subprocess."""
    # TODO remove on python 3.7+
    command = map(str, command)

    proc = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        **extra,
    )
    out, err = proc.communicate()
    return out, err, proc.returncode


@pytest.mark.cli
class TestCLI():
    def test_call(self):

        command = ["pygaps", "--help"]
        out, err, exitcode = capture(command)
        print(out, err)
        assert exitcode == 0

    def test_default(self, basic_pointisotherm, tmp_path_factory):

        tempdir = tmp_path_factory.mktemp('cli')

        path = tempdir / 'isotherm.json'
        basic_pointisotherm.to_json(path)

        command = ["pygaps", path]
        out, err, exitcode = capture(command)
        print(out, err)
        assert exitcode == 0

        path = tempdir / 'isotherm.csv'
        basic_pointisotherm.to_csv(path)

        command = ["pygaps", path]
        out, err, exitcode = capture(command)
        print(out, err)
        assert exitcode == 0

        path = tempdir / 'isotherm.xls'
        basic_pointisotherm.to_xl(path)

        command = ["pygaps", path]
        out, err, exitcode = capture(command)
        print(out, err)
        assert exitcode == 0

    def test_plot(self, basic_pointisotherm, tmp_path_factory):

        path = tmp_path_factory.mktemp('cli') / 'isotherm.json'
        basic_pointisotherm.to_json(path)

        my_env = os.environ.copy()
        my_env["MPLBACKEND"] = "Agg"

        command = ["pygaps", "--plot", path]
        out, err, exitcode = capture(command, env=my_env)
        print(out, err)
        assert exitcode == 0

    def test_characterize(self, basic_pointisotherm, tmp_path_factory):

        path = tmp_path_factory.mktemp('cli') / 'isotherm.json'
        basic_pointisotherm.adsorbate = 'N2'
        basic_pointisotherm.to_json(path)

        command = ["pygaps", "-ch", "a_bet", path]
        out, err, exitcode = capture(command)
        print(out, err)
        assert exitcode == 0

    def test_model(self, basic_pointisotherm, tmp_path_factory):

        tempdir = tmp_path_factory.mktemp('cli')
        path = tempdir / 'isotherm.json'
        basic_pointisotherm.to_json(path)

        command = ["pygaps", "-md", "guess", path]
        out, err, exitcode = capture(command)
        print(out, err)
        assert exitcode == 0

        outpath = tempdir / 'model.json'
        command = ["pygaps", "-md", "guess", "-o", outpath, path]
        out, err, exitcode = capture(command)
        print(out, err)
        assert exitcode == 0

        assert isinstance(pgp.isotherm_from_json(outpath), pygaps.ModelIsotherm)

    def test_convert(self, basic_pointisotherm, tmp_path_factory):

        tempdir = tmp_path_factory.mktemp('cli')
        path = tempdir / 'isotherm.json'
        outpath = tempdir / 'model.json'
        basic_pointisotherm.adsorbate = 'N2'
        basic_pointisotherm.to_json(path)

        command = ["pygaps", "-cv", "pressure_mode=relative", "-o", outpath, path]
        out, err, exitcode = capture(command)
        print(out, err)
        assert exitcode == 0

        assert pgp.isotherm_from_json(outpath).pressure_mode == 'relative'
