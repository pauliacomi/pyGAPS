"""Tests AIF interaction."""

import json
import pathlib
import textwrap
from copy import deepcopy

import pandas
import pytest
from gemmi import cif

import pygaps
import pygaps.parsing as pgp
from pygaps.utilities.exceptions import ParsingError

from .conftest import DATA_AIF
from .conftest import DATA_JSON
from .conftest import PARSING_PATH

DATA_AIF_PATH = PARSING_PATH / 'aif'
AIF_DICTIONARY = pathlib.Path(pgp.__file__).parent / 'aif_dictionary.json'


def _strip_serialized_aif_fields(data_dict):
    data_dict = deepcopy(data_dict)
    for key in [
        'audit_aif_version',
        'audit_creation_method',
        'audit_creation_software',
        'exptl_method',
        'exptl_isotherm_type',
        'units_composition_type',
        'units_concentration',
    ]:
        data_dict.pop(key, None)

    for section in ('material', 'adsorbate'):
        section_dict = data_dict.get(section)
        if not isinstance(section_dict, dict):
            continue
        section_dict = section_dict.copy()
        name = section_dict.pop('name', None)
        if name is not None:
            data_dict[section] = name
        else:
            data_dict.pop(section)
        for key, value in section_dict.items():
            data_dict[f'{section}_{key}'] = value

    def remove_none_values(value):
        if isinstance(value, dict):
            return {
                key: remove_none_values(item)
                for key, item in value.items()
                if item is not None
            }
        if isinstance(value, list):
            return [remove_none_values(item) for item in value if item is not None]
        return value

    data_dict = remove_none_values(data_dict)
    return data_dict


@pytest.mark.parsing
class TestAIF():
    """Test AIF-related functionality."""
    def test_aif_writes_v1_fields(self, basic_pointisotherm):
        """Test that the writer emits v1.0 fields alongside pyGAPS extras."""
        aif_text = pgp.isotherm_to_aif(basic_pointisotherm)

        assert "_audit_aif_version v1.0" in aif_text
        assert "_adsorptive_name" in aif_text
        assert "_adsnt_material_name" in aif_text
        assert "_units_sorbed_amount" in aif_text
        assert "_pygaps_pressure_mode" in aif_text
        assert "_exptl_method" in aif_text
        assert "_exptl_method unspecified" in aif_text

    def test_aif_roundtrips_adsorbate_details(self, basic_pointisotherm):
        """The v1.0 writer preserves supported Adsorbate properties."""
        details = {
            'info': 'ethane',
            'inchi': 'InChI=1S/C2H6',
            'cas': '74-84-0',
            'smiles': 'CC',
            'formula': 'C2H6',
            'molar_mass': 30.07,
            'kinetic_diameter': 0.44,
            'quadrupole_moment': 0.1,
        }
        basic_pointisotherm.adsorbate = pygaps.Adsorbate('Custom adsorptive', **details)
        basic_pointisotherm.properties['units_quadrupole_moment'] = 'Debye·Å'

        aif_text = pgp.isotherm_to_aif(basic_pointisotherm)
        restored = pgp.isotherm_from_aif(aif_text)

        quadrupole_units = cif.read_string(aif_text).sole_block().find_value(
            '_units_quadrupole_moment'
        )
        assert quadrupole_units == "'Debye·Å'"
        for key, value in details.items():
            aif_key = 'molecular_weight' if key == 'molar_mass' else key
            tag = f"_adsorptive_{aif_key}"
            assert tag in aif_text
            assert restored.adsorbate.properties[aif_key] == value

    def test_aif_omits_quadrupole_without_units(self, basic_pointisotherm, caplog):
        """Do not write a quadrupole value without the required unit."""
        basic_pointisotherm.adsorbate = pygaps.Adsorbate('Custom adsorptive', quadrupole_moment=1.52)

        aif_text = pgp.isotherm_to_aif(basic_pointisotherm)

        assert '_adsorptive_quadrupole_moment' not in aif_text
        assert 'quadrupole_moment was not written' in caplog.text

    def test_aif_writes_legacy_fields(self, basic_pointisotherm):
        """Test that the legacy writer uses legacy metadata, units, and loop tags."""
        aif_text = pgp.isotherm_to_aif(basic_pointisotherm, version='d546195')

        assert "_audit_aif_version d546195" in aif_text
        assert "_exptl_adsorptive" in aif_text
        assert "_units_loading" in aif_text
        assert "_adsorp_amount" in aif_text
        assert "_adsorptive_name" not in aif_text
        assert "_units_sorbed_amount" not in aif_text

        round_tripped = pgp.isotherm_from_aif(aif_text)
        assert round_tripped.material == basic_pointisotherm.material
        assert round_tripped.adsorbate == basic_pointisotherm.adsorbate
        assert round_tripped.temperature == basic_pointisotherm.temperature
        assert round_tripped.data_raw.to_dict('list') == basic_pointisotherm.data_raw.to_dict('list')

    def test_aif_reads_v1_hybrid_with_extra_fields(self):
        """Test that v1.0 files still accept legacy aliases and keep unknown data."""
        aif_text = textwrap.dedent(
            """
            data_example
            _audit_aif_version 1.0
            _audit_creation_method pyGAPS
            _exptl_adsorptive N2
            _exptl_temperature 77.0
            _sample_material_id 'UiO-66(Zr)'
            _exptl_operator 'PI'
            _units_temperature 'K'
            _units_pressure bar
            _units_loading 'mmol/g'
            _pygaps_pressure_mode 'absolute'
            _pygaps_pressure_unit 'bar'
            _pygaps_material_basis 'mass'
            _pygaps_material_unit 'g'
            _pygaps_loading_basis 'molar'
            _pygaps_loading_unit 'mmol'
            _pygaps_temperature_unit 'K'
            _pygaps_extra_meta 'keep-me'

            loop_
            _adsorp_pressure
            _adsorp_amount
            _adsorp_p0
            _adsorp_fugacity_component_1
            1.0 2.0 3.0 4.0
            """
        ).strip()

        isotherm = pgp.isotherm_from_aif(aif_text)

        assert isotherm.material == 'UiO-66(Zr)'
        assert isotherm.adsorbate == 'N2'
        assert isotherm.properties['extra_meta'] == 'keep-me'
        assert 'pressure_saturation' in isotherm.data_raw.columns
        assert 'fugacity_component_1' in isotherm.data_raw.columns

        round_tripped = pgp.isotherm_to_aif(isotherm)
        assert '_adsorp_p0' in round_tripped
        assert '_adsorp_fugacity_component_1' in round_tripped

    def test_aif_baseisotherm(self, basic_isotherm, tmp_path_factory):
        """Test creation/read of BaseIsotherm AIF"""
        path = tmp_path_factory.mktemp('aif') / 'baseisotherm.aif'
        pgp.isotherm_to_aif(basic_isotherm, path)
        isotherm = pgp.isotherm_from_aif(path)
        assert _strip_serialized_aif_fields(isotherm.to_dict()) == _strip_serialized_aif_fields(basic_isotherm.to_dict())

    @pytest.mark.parametrize("version", ["v1.0", "d546195"])
    @pytest.mark.parametrize("property_name", ["dataset_id", "data0", "model_note", "model_parameter_notes"])
    @pytest.mark.parametrize("fixture_name", ["basic_isotherm", "basic_pointisotherm", "basic_modelisotherm"])
    def test_aif_type_detection_ignores_metadata(self, request, fixture_name, version, property_name):
        """Only actual data loops or a model name should select a specialised isotherm."""
        isotherm = request.getfixturevalue(fixture_name)
        isotherm.properties[property_name] = 'keep-me'
        restored = pgp.isotherm_from_aif(pgp.isotherm_to_aif(isotherm, version=version))

        assert type(restored) is type(isotherm)
        assert restored.properties[property_name] == 'keep-me'

    @pytest.mark.parametrize("from_file", [False, True])
    @pytest.mark.parametrize("block_count", [0, 2])
    def test_aif_requires_single_block(self, tmp_path, from_file, block_count):
        """Empty and multi-block documents should raise an actionable parsing error."""
        source = "\n".join(f"data_block_{index}\n_tag value" for index in range(block_count))
        if from_file:
            path = tmp_path / 'blocks.aif'
            path.write_text(source)
            source = path

        with pytest.raises(ParsingError, match=f"AIF file should have a single block; found {block_count}"):
            pgp.isotherm_from_aif(source)

    @pytest.mark.parametrize("fixture_name", ["basic_isotherm", "basic_pointisotherm", "basic_modelisotherm"])
    @pytest.mark.parametrize("method", [{}, {"experimental_method": "unspecified"},
                                      {"experimental_method": "volumetric"},
                                      {"experimental_method": None}, {"experimental_method": ""}])
    def test_aif_method_roundtrip_identity(self, request, fixture_name, method):
        """A generated method must not alter metadata or identity on re-import."""
        isotherm = request.getfixturevalue(fixture_name)
        isotherm.properties.update(method)
        original = deepcopy(isotherm.to_dict())
        aif_text = pgp.isotherm_to_aif(isotherm)
        restored = pgp.isotherm_from_aif(aif_text)

        assert restored.to_dict() == original
        assert restored == isotherm
        assert isotherm.to_dict() == original
        restored_again = pgp.isotherm_from_aif(pgp.isotherm_to_aif(restored))
        assert restored_again == isotherm

    def test_aif_method_without_generated_marker(self, basic_isotherm):
        """An unmarked unspecified method from an existing file is real metadata."""
        basic_isotherm.properties['experimental_method'] = 'unspecified'
        text = pgp.isotherm_to_aif(basic_isotherm)
        assert pgp.isotherm_from_aif(text).properties['experimental_method'] == 'unspecified'

    def test_aif_generated_method_override(self, basic_isotherm):
        """Explicit reader overrides take precedence over the restored method."""
        text = pgp.isotherm_to_aif(basic_isotherm)
        restored = pgp.isotherm_from_aif(text, experimental_method='simulation')
        assert restored.properties['experimental_method'] == 'simulation'

    def test_aif_generated_method_edited(self, basic_isotherm):
        """A method edited after export should not be replaced by the saved state."""
        text = pgp.isotherm_to_aif(basic_isotherm)
        text = text.replace('_exptl_method unspecified', '_exptl_method simulation')
        restored = pgp.isotherm_from_aif(text)
        assert restored.properties['experimental_method'] == 'simulation'
        assert 'original_experimental_method' not in restored.properties

    @pytest.mark.parametrize("marker", ["[]", '{"unexpected": true}', "invalid"])
    def test_aif_invalid_method_marker(self, basic_isotherm, marker):
        """Malformed writer state should produce an explicit parsing error."""
        text = pgp.isotherm_to_aif(basic_isotherm)
        document = cif.read_string(text)
        document.sole_block().set_pair('_pygaps_original_experimental_method', cif.quote(marker))
        with pytest.raises(ParsingError, match="Invalid _pygaps_original_experimental_method marker"):
            pgp.isotherm_from_aif(document.as_string())

    def test_aif_pointisotherm(self, basic_pointisotherm, tmp_path_factory):
        """Test creation of the PointIsotherm AIF."""
        path = tmp_path_factory.mktemp('aif') / 'pointisotherm.aif'
        pgp.isotherm_to_aif(basic_pointisotherm, path)
        isotherm = pgp.isotherm_from_aif(path)
        assert _strip_serialized_aif_fields(isotherm.to_dict()) == _strip_serialized_aif_fields(basic_pointisotherm.to_dict())

    def test_aif_modelisotherm(self, basic_modelisotherm, tmp_path_factory):
        """Test creation/read of ModelIsotherm AIF."""
        path = tmp_path_factory.mktemp('aif') / 'modelisotherm.aif'
        pgp.isotherm_to_aif(basic_modelisotherm, path)
        isotherm = pgp.isotherm_from_aif(path)
        assert _strip_serialized_aif_fields(isotherm.to_dict()) == _strip_serialized_aif_fields(basic_modelisotherm.to_dict())

    def test_aif_isotherm_mat(self, basic_pointisotherm, basic_material, tmp_path_factory):
        """Test serialisation of material properties into AIF."""
        path = tmp_path_factory.mktemp('aif') / 'isotherm_mat.aif'
        basic_pointisotherm.material = basic_material
        pgp.isotherm_to_aif(basic_pointisotherm, path)
        isotherm = pgp.isotherm_from_aif(path)
        assert _strip_serialized_aif_fields(isotherm.to_dict()) == _strip_serialized_aif_fields(basic_pointisotherm.to_dict())

    @pytest.mark.parametrize("path", DATA_AIF)
    def test_aif_read(self, path):
        """Test reading of some AIFs."""
        isotherm = pgp.isotherm_from_aif(path)
        assert isotherm

    @pytest.mark.parametrize(
        "name, material, adsorbate, temperature, columns", [
            ("01_basic_n2_77K.aif", "Zeolite-13X", "nitrogen", 77.35, ["pressure_saturation"]),
            ("02_full_featured.aif", "UiO-66-NH2", "carbon dioxide", 298.15,
             ["pressure_saturation", "loading_excess", "enthalpy"]),
            ("03_high_pressure_ch4.aif", "AX-21", "methane", 298.15, ["loading_excess", "loading_absolute"]),
            ("04_water_vapor.aif", "Silica-Gel-Type-A", "water", 298.15, ["pressure_saturation"]),
            ("05_simulation_gcmc.aif", "MOF-5", "carbon dioxide", 298.15, []),
            ("06_co2_calorimetry.aif", "MIL-53(Al)", "carbon dioxide", 298.15, ["enthalpy", "enthalpy_integral"]),
            ("AC Ar 77K.aif", "unknown", "argon", 87.0, ["pressure_saturation"]),
            ("DMOF C2H6 298K.aif", "DMOF", "ethane", 298.15, ["pressure_saturation"]),
        ]
    )
    def test_aif_read_values(self, name, material, adsorbate, temperature, columns):
        """Test that v1.0 and legacy AIFs are read into the expected values."""
        isotherm = pgp.isotherm_from_aif(DATA_AIF_PATH / name)

        assert str(isotherm.material) == material
        assert isotherm.adsorbate == adsorbate
        assert isotherm.temperature == pytest.approx(temperature)
        assert set(columns) <= set(isotherm.other_keys)
        for unit in ('material_basis', 'material_unit', 'loading_unit'):
            assert unit not in isotherm.material.properties

    def test_aif_read_v1_details(self):
        """Test adsorbent/adsorptive details, ordering and extra loops of a v1.0 file."""
        isotherm = pgp.isotherm_from_aif(DATA_AIF_PATH / "02_full_featured.aif")

        # adsorbent
        assert isotherm.material.properties['batch'] == 'UiO66NH2-full-01'
        assert isotherm.material.properties['molar_mass'] == pytest.approx(1746.23)
        assert isotherm.material.properties['activation_time'] == pytest.approx(16.0)

        # adsorptive details are passed to the adsorbate, the internal one is untouched
        assert isotherm.adsorbate.properties['cas'] == '124-38-9'
        assert isotherm.adsorbate.properties['smiles'] == 'O=C=O'
        assert isotherm.adsorbate.backend_name == pygaps.Adsorbate.find('CO2').backend_name
        assert 'cas' not in pygaps.Adsorbate.find('CO2').properties

        # units
        assert isotherm.pressure_unit == 'Pa'
        assert isotherm.loading_unit == 'mmol'
        assert isotherm.material_unit == 'g'

        # branches
        assert isotherm.has_branch('ads') and isotherm.has_branch('des')
        assert list(isotherm.pressure(branch='ads', indexed=True)) == sorted(
            isotherm.pressure(branch='ads', indexed=True)
        )

        # analysis loops are kept as rows
        fits = isotherm.properties['analysis_fit']
        assert [fit['model'] for fit in fits] == ['Langmuir', 'DSL', 'Toth']
        params = isotherm.properties['analysis_fit_param']
        assert params[0] == {'index': 1, 'name': 'q_max', 'value': 5.67, 'uncertainty': 0.12, 'unit': 'mmol/g'}
        assert isotherm.properties['analysis_bet_area'] == pytest.approx(1045.0)

    def test_aif_read_v1_loops_and_values(self):
        """Test STAR quoting, null values, index ordering and non-isotherm loops."""
        aif_text = textwrap.dedent(
            """
            data_example
            _audit_aif_version 1.0
            _exptl_method "volumetric"
            _exptl_temperature 298.0
            _exptl_operator ?
            _adsnt_material_name "MOF 5"
            _adsorptive_name "Carbon Dioxide"
            _units_temperature K
            _units_pressure "kPa"
            _units_sorbed_amount "mmol/g"

            loop_
            _adsorptive_component_index
            _adsorptive_component_name
            1 "Carbon Dioxide"

            loop_
            _adsorp_index
            _adsorp_pressure
            _adsorp_amount
            _adsorp_amount_uncertainty
            _adsorp_amount_component_1
            2 20.0 2.0 0.2 2.0
            1 10.0 1.0 0.1 1.0
            3 30.0 ? 0.3 3.0

            loop_
            _adsorp_transient_point_index
            _adsorp_transient_elapsed_time
            1 0.0
            1 5.0
            """
        ).strip()

        isotherm = pgp.isotherm_from_aif(aif_text)

        assert str(isotherm.material) == 'MOF 5'
        assert 'experimental_operator' not in isotherm.properties
        assert isotherm.pressure_unit == 'kPa'

        data = isotherm.data_raw
        assert list(data['pressure']) == [10.0, 20.0, 30.0]
        assert 'index' not in data.columns
        assert list(data['loading_uncertainty']) == [0.1, 0.2, 0.3]
        assert list(data['loading_component_1']) == [1.0, 2.0, 3.0]
        assert data['loading'].isna().sum() == 1

        assert isotherm.properties['adsorptive_component'] == [{'index': 1, 'name': 'Carbon Dioxide'}]
        assert 'components' not in isotherm.adsorbate.properties
        assert isotherm.properties['adsorp_transient'] == [
            {'point_index': 1, 'elapsed_time': 0.0},
            {'point_index': 1, 'elapsed_time': 5.0},
        ]

    def test_aif_read_versions(self):
        """Test explicit, unprefixed and unknown version handling."""
        path = DATA_AIF_PATH / "01_basic_n2_77K.aif"
        assert pgp.isotherm_from_aif(path, version='1.0')
        assert pgp.isotherm_from_aif(path, version='v1.0')
        assert pgp.isotherm_from_aif(path, version='unknown-version')

    def test_aif_write_precision(self):
        """Test that data is written to significant figures, not decimal places."""
        isotherm = pygaps.PointIsotherm(
            pressure=[1e-12, 1.23456789012e-9, 100.0, 1.5e7],
            loading=[2e-11, 0.123456789, 1.0, 12345678.9],
            material='M',
            adsorbate='nitrogen',
            temperature=77,
        )
        aif_text = pgp.isotherm_to_aif(isotherm)
        data = pgp.isotherm_from_aif(aif_text).data_raw

        assert list(data['pressure']) == pytest.approx([1e-12, 1.2345679e-9, 100.0, 1.5e7], rel=1e-12)
        assert list(data['loading']) == pytest.approx([2e-11, 0.12345679, 1.0, 12345679.0], rel=1e-12)
        assert data['pressure'].dtype == float

    def test_aif_write_list_properties(self):
        """Test that list and dict properties survive a round-trip."""
        properties = {
            'numbers': [1, 2.5],
            'strings': ['a b', "it's", 'say "hi"'],
            'mapping': {'a': 1, 'b': [1, 2], 'c': None},
            'empty': [],
            'bracket_text': '[not a list',
        }
        isotherm = pygaps.PointIsotherm(
            pressure=[1, 2], loading=[1, 2], material='M', adsorbate='nitrogen', temperature=77, **properties
        )
        round_tripped = pgp.isotherm_from_aif(pgp.isotherm_to_aif(isotherm))

        for key, value in properties.items():
            assert round_tripped.properties[key] == value

    def test_aif_read_legacy_list_properties(self):
        """Test that lists written by older pyGAPS versions are still read."""
        aif_text = pgp.isotherm_to_aif(
            pygaps.PointIsotherm(pressure=[1, 2], loading=[1, 2], material='M', adsorbate='nitrogen', temperature=77)
        )
        aif_text = aif_text.replace("_pygaps_temperature_unit K", "_pygaps_temperature_unit K\n_pygaps_old '[1 2]'")
        assert pgp.isotherm_from_aif(aif_text).properties['old'] == [1, 2]

    def test_aif_write_row_loops(self):
        """Test that AIF loops read as rows are written back as loops."""
        isotherm = pgp.isotherm_from_aif(DATA_AIF_PATH / "02_full_featured.aif")
        aif_text = pgp.isotherm_to_aif(isotherm)

        assert "_analysis_fit_model" in aif_text
        assert "_analysis_fit_param_value" in aif_text
        assert "_analysis_bet_area" in aif_text
        assert "_pygaps_analysis" not in aif_text

        round_tripped = pgp.isotherm_from_aif(aif_text)
        for key in ('analysis_fit', 'analysis_fit_param', 'analysis_bet_area'):
            assert round_tripped.properties[key] == isotherm.properties[key]

        # legacy AIF has no analysis categories, rows are kept as pyGAPS loops
        aif_text = pgp.isotherm_to_aif(isotherm, version='d546195')
        assert "_pygaps_analysis_fit.model" in aif_text
        round_tripped = pgp.isotherm_from_aif(aif_text)
        assert round_tripped.properties['analysis_fit'] == isotherm.properties['analysis_fit']

    def test_aif_write_custom_row_loops(self):
        """Test that pyGAPS row lists are written as namespaced loops."""
        rows = [{'Step': 1, 'note': 'a b', 'value_1': 1.5}, {'Step': 2, 'note': None, 'value_1': 2.5}]
        isotherm = pygaps.PointIsotherm(
            pressure=[1, 2], loading=[1, 2], material='M', adsorbate='nitrogen', temperature=77, my_Rows=rows
        )
        aif_text = pgp.isotherm_to_aif(isotherm)
        assert "_pygaps_my_Rows.Step" in aif_text

        round_tripped = pgp.isotherm_from_aif(aif_text)
        assert round_tripped.properties['my_Rows'] == rows

    def test_aif_write_dependent_units(self):
        """Test that units required by dimensional values are written."""
        isotherm = pygaps.PointIsotherm(
            isotherm_data=pandas.DataFrame({
                'pressure': [1, 2],
                'loading': [1, 2],
                'enthalpy': [30, 25],
            }),
            pressure_key='pressure',
            loading_key='loading',
            material={'name': 'M', 'mass': 0.1, 'density': 1.2, 'molar_mass': 100, 'activation_time': 12},
            adsorbate='nitrogen',
            temperature=77,
            units_mass='mg',
        )
        aif_text = pgp.isotherm_to_aif(isotherm)

        assert "_units_mass mg" in aif_text
        assert "_units_density g/cm3" in aif_text
        assert "_units_molecular_weight g/mol" in aif_text
        assert "_units_time h" in aif_text
        assert "_units_enthalpy kJ/mol" in aif_text
        assert aif_text.index("_units_enthalpy") < aif_text.index("loop_")

        # defaults written by pyGAPS are not read back as metadata, explicit ones are
        round_tripped = pgp.isotherm_from_aif(aif_text)
        assert round_tripped.properties['units_mass'] == 'mg'
        for key in ('units_density', 'units_molecular_weight', 'units_time', 'units_enthalpy'):
            assert key not in round_tripped.properties

        # the legacy dictionary has no molecular weight units
        aif_text = pgp.isotherm_to_aif(isotherm, version='d546195')
        assert "_units_molecular_weight" not in aif_text
        assert "_units_enthalpy kJ/mol" in aif_text

    @pytest.mark.parametrize("name", [None, *[path.name for path in sorted(DATA_AIF_PATH.glob('0*.aif'))]])
    def test_aif_write_schema(self, name, basic_pointisotherm):
        """Test that written v1.0 files satisfy the AIF dictionary."""
        jsonschema = pytest.importorskip('jsonschema')

        schema = json.loads((AIF_DICTIONARY).read_text(encoding='utf-8'))
        types = {}
        for definition in schema['definitions'].values():
            types.update({tag: info.get('type') for tag, info in definition.get('properties', {}).items()})

        def typed(tag, value):
            if cif.is_null(value):
                return None
            value = cif.as_string(value)
            if types.get(tag) in ('number', 'integer'):
                return float(value)
            return value

        isotherm = pgp.isotherm_from_aif(DATA_AIF_PATH / name) if name else basic_pointisotherm
        isotherm.material.properties.update({'mass': 0.1, 'density': 1.2, 'activation_time': 2})
        block = cif.read_string(pgp.isotherm_to_aif(isotherm)).sole_block()

        # loops are validated through their first value
        document = {}
        for item in block:
            if item.pair is not None:
                document[item.pair[0]] = typed(*item.pair)
            elif item.loop is not None:
                for column, tag in enumerate(item.loop.tags):
                    document[tag] = typed(tag, item.loop[0, column])
        document = {tag: value for tag, value in document.items() if value is not None}

        errors = [error.message for error in jsonschema.Draft201909Validator(schema).iter_errors(document)]
        assert errors == []

    @pytest.mark.parametrize(
        "loop, missing", [
            ("_adsorp_index\n_adsorp_fugacity\n_adsorp_amount\n1 1.0 1.0", "_adsorp_pressure"),
            ("_adsorp_index\n_adsorp_pressure\n_adsorp_amount_excess\n1 1.0 1.0", "_adsorp_amount"),
            ("_desorp_index\n_desorp_pressure\n_desorp_amount_component_1\n1 1.0 1.0", "_desorp_amount"),
        ]
    )
    def test_aif_read_unsupported_data(self, loop, missing):
        """Test that data loops without pressure or total amount raise a specific error."""
        aif_text = textwrap.dedent(
            """
            data_example
            _audit_aif_version v1.0
            _exptl_method volumetric
            _exptl_temperature 298.0
            _adsnt_material_name M
            _adsorptive_name nitrogen
            _units_temperature K
            _units_pressure bar
            _units_sorbed_amount mmol/g
            loop_
            """
        ).strip() + "\n" + loop

        with pytest.raises(ParsingError, match=f"missing the required column\\(s\\) {missing}"):
            pgp.isotherm_from_aif(aif_text)

    @pytest.mark.parametrize("use_pygaps_units", [True, False])
    @pytest.mark.parametrize("path_json", DATA_JSON)
    def test_aif_write_read(self, use_pygaps_units, path_json, tmp_path_factory):
        """Test various parsings in AIF files."""
        isotherm = pgp.isotherm_from_json(path_json)

        # round the iso dataframe to the parser precision
        isotherm.data_raw = isotherm.data_raw.round(pgp._PARSER_PRECISION)

        path = tmp_path_factory.mktemp('aif') / path_json.with_suffix(".aif").name
        pgp.isotherm_to_aif(isotherm, path)
        if use_pygaps_units:
            isotherm2 = pgp.isotherm_from_aif(path)
        else:
            if isotherm.loading_basis == 'volume_liquid':
                # TODO expected to fail at the moment
                return
            isotherm2 = pgp.isotherm_from_aif(path, _parse_units=True)
        assert _strip_serialized_aif_fields(isotherm2.to_dict()) == _strip_serialized_aif_fields(isotherm.to_dict())
