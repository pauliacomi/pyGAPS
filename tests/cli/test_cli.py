import os
import subprocess

import pytest

import pygaps


def capture(command, **extra):
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

    def test_default(self, basic_pointisotherm, tmpdir_factory):

        tempdir = tmpdir_factory.mktemp('cli')

        path = tempdir.join('isotherm.json').strpath
        basic_pointisotherm.to_json(path)

        command = ["pygaps", path]
        out, err, exitcode = capture(command)
        print(out, err)
        assert exitcode == 0

        path = tempdir.join('isotherm.csv').strpath
        basic_pointisotherm.to_csv(path)

        command = ["pygaps", path]
        out, err, exitcode = capture(command)
        print(out, err)
        assert exitcode == 0

        path = tempdir.join('isotherm.xls').strpath
        basic_pointisotherm.to_xl(path)

        command = ["pygaps", path]
        out, err, exitcode = capture(command)
        print(out, err)
        assert exitcode == 0

    def test_plot(self, basic_pointisotherm, tmpdir_factory):

        path = tmpdir_factory.mktemp('cli').join('isotherm.json').strpath
        basic_pointisotherm.to_json(path)

        my_env = os.environ.copy()
        my_env["MPLBACKEND"] = "Agg"

        command = ["pygaps", "--plot", path]
        out, err, exitcode = capture(command, env=my_env)
        print(out, err)
        assert exitcode == 0

    def test_characterize(self, basic_pointisotherm, tmpdir_factory):

        path = tmpdir_factory.mktemp('cli').join('isotherm.json').strpath
        basic_pointisotherm.adsorbate = 'N2'
        basic_pointisotherm.to_json(path)

        command = ["pygaps", "-ch", "a_bet", path]
        out, err, exitcode = capture(command)
        print(out, err)
        assert exitcode == 0

    def test_model(self, basic_pointisotherm, tmpdir_factory):

        tempdir = tmpdir_factory.mktemp('cli')
        path = tempdir.join('isotherm.json').strpath
        basic_pointisotherm.to_json(path)

        command = ["pygaps", "-md", "guess", path]
        out, err, exitcode = capture(command)
        print(out, err)
        assert exitcode == 0

        outpath = tempdir.join('model.json').strpath
        command = ["pygaps", "-md", "guess", "-o", outpath, path]
        out, err, exitcode = capture(command)
        print(out, err)
        assert exitcode == 0

        assert isinstance(
            pygaps.isotherm_from_json(outpath), pygaps.ModelIsotherm
        )

    def test_convert(self, basic_pointisotherm, tmpdir_factory):

        tempdir = tmpdir_factory.mktemp('cli')
        path = tempdir.join('isotherm.json').strpath
        outpath = tempdir.join('model.json').strpath
        basic_pointisotherm.adsorbate = 'N2'
        basic_pointisotherm.to_json(path)

        command = [
            "pygaps", "-cv", "pressure_mode=relative", "-o", outpath, path
        ]
        out, err, exitcode = capture(command)
        print(out, err)
        assert exitcode == 0

        assert pygaps.isotherm_from_json(outpath).pressure_mode == 'relative'
