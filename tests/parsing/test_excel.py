"""Tests excel parsing."""

import math

import pandas
import pytest

import pygaps.parsing as pgp
from pygaps.core.modelisotherm import ModelIsotherm
from pygaps.core.pointisotherm import PointIsotherm

from .conftest import DATA_JSON
from .conftest import DATA_XL


def _close(a, b, rel=1e-15):
    """Recursively compare values, allowing for xlsx's 16-digit float precision."""
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_close(a[k], b[k], rel) for k in a)
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(_close(x, y, rel) for x, y in zip(a, b))
    if isinstance(a, bool) or isinstance(b, bool):
        return a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(a, b, rel_tol=rel) or (math.isnan(a) and math.isnan(b))
    return a == b


def assert_xlsx_roundtrip(original, restored):
    """Check an isotherm survived an xlsx round-trip."""
    assert type(original) is type(restored)
    assert original.iso_id == restored.iso_id
    assert _close(original.to_dict(), restored.to_dict())
    if isinstance(original, PointIsotherm):
        pandas.testing.assert_frame_equal(
            original.data_raw.reset_index(drop=True),
            restored.data_raw.reset_index(drop=True),
            rtol=1e-12,
            check_dtype=False,
        )
    if isinstance(original, ModelIsotherm):
        assert _close(original.model.to_dict(), restored.model.to_dict())


@pytest.mark.parsing
class TestExcel:
    """All testing of Excel interface"""

    def test_excel_isotherm(self, basic_isotherm, tmp_path_factory):
        """Test creation/read of point isotherm excel file."""
        path = tmp_path_factory.mktemp('excel') / 'baseisotherm.xlsx'
        pgp.isotherm_to_xl(basic_isotherm, path=path)
        isotherm = pgp.isotherm_from_xl(path)
        assert_xlsx_roundtrip(basic_isotherm, isotherm)

    def test_excel_isotherm_material(self, basic_isotherm, basic_material, tmp_path_factory):
        """Test creation/read of point isotherm excel file."""
        path = tmp_path_factory.mktemp('excel') / 'isotherm_mat.xlsx'
        basic_isotherm.material = basic_material
        pgp.isotherm_to_xl(basic_isotherm, path=path)
        isotherm = pgp.isotherm_from_xl(path)
        assert_xlsx_roundtrip(basic_isotherm, isotherm)

    def test_excel_pointisotherm(self, basic_pointisotherm, tmp_path_factory):
        """Test creation/read of point isotherm excel file."""
        path = tmp_path_factory.mktemp('excel') / 'pointisotherm.xlsx'
        pgp.isotherm_to_xl(basic_pointisotherm, path=path)
        isotherm = pgp.isotherm_from_xl(path)
        assert_xlsx_roundtrip(basic_pointisotherm, isotherm)

    def test_excel_modelisotherm(self, basic_modelisotherm, tmp_path_factory):
        """Test creation/read of model isotherm excel file."""
        path = tmp_path_factory.mktemp('excel') / 'modelisotherm.xlsx'
        pgp.isotherm_to_xl(basic_modelisotherm, path=path)
        isotherm = pgp.isotherm_from_xl(path)
        assert_xlsx_roundtrip(basic_modelisotherm, isotherm)

    @pytest.mark.parametrize("path", DATA_XL)
    def test_excel_read(self, path):
        """Test read excel files."""
        isotherm = pgp.isotherm_from_xl(path=path)
        assert isotherm

    @pytest.mark.parametrize("path", DATA_XL)
    def test_excel_xls_to_xlsx(self, path, tmp_path):
        """Test legacy .xls files read the same after conversion to .xlsx."""
        isotherm = pgp.isotherm_from_xl(path=path)
        isotherm.to_xl(tmp_path / 'converted.xlsx')
        assert_xlsx_roundtrip(isotherm, pgp.isotherm_from_xl(tmp_path / 'converted.xlsx'))

    def test_excel_write_xls_renamed(self, basic_pointisotherm, tmp_path):
        """Test a .xls output path is written as .xlsx with a warning."""
        with pytest.warns(UserWarning, match=r"\.xls"):
            pgp.isotherm_to_xl(basic_pointisotherm, path=tmp_path / 'legacy.xls')
        assert not (tmp_path / 'legacy.xls').exists()
        assert_xlsx_roundtrip(basic_pointisotherm, pgp.isotherm_from_xl(tmp_path / 'legacy.xlsx'))

    @pytest.mark.parametrize("path_json", DATA_JSON)
    def test_excel_write_read(self, path_json, tmp_path_factory):
        """Test various parsings in excel files."""
        isotherm = pgp.isotherm_from_json(path_json)
        path = tmp_path_factory.mktemp('excel') / path_json.with_suffix(".xlsx").name
        pgp.isotherm_to_xl(isotherm, path)
        isotherm2 = pgp.isotherm_from_xl(path)
        assert_xlsx_roundtrip(isotherm, isotherm2)
