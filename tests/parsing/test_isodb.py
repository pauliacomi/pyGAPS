"""Tests NIST ISODB interaction."""

import json
import logging
from types import SimpleNamespace
from unittest.mock import Mock

import numpy
import pytest
import requests

import pygaps
import pygaps.parsing.isodb as isodb

from .conftest import PARSING_PATH


@pytest.fixture
def nist_data():
    """Load the existing recorded NIST response without making a request."""
    path = PARSING_PATH / 'nist' / 'nist_iso.json'
    return json.loads(path.read_text(encoding='utf-8'))


@pytest.mark.parsing
class TestISODB:
    def test_get_isotherm(self, monkeypatch, nist_data):
        get = Mock(return_value=SimpleNamespace(text=json.dumps(nist_data)))
        monkeypatch.setattr(requests, 'get', get)

        isotherm = isodb.isotherm_from_isodb(nist_data['filename'])

        get.assert_called_once_with(
            f"https://adsorption.nist.gov/isodb/api/isotherm/{nist_data['filename']}.json",
            timeout=5,
        )
        assert isinstance(isotherm, pygaps.PointIsotherm)
        assert isotherm.material.name == nist_data['adsorbent']['name']
        assert isotherm.adsorbate == nist_data['adsorbates'][0]['name'].lower()
        assert isotherm.temperature == nist_data['temperature']
        assert isotherm.temperature_unit == 'K'
        assert isotherm.pressure_mode == 'absolute'
        assert isotherm.pressure_unit == 'bar'
        assert isotherm.loading_basis == 'molar'
        assert isotherm.loading_unit == 'mol'
        assert isotherm.material_basis == 'molar'
        assert isotherm.material_unit == 'mol'
        assert isotherm.properties['nist_hash'] == nist_data['adsorbent']['hashkey']
        assert isotherm.properties['DOI'] == nist_data['DOI']
        assert isotherm.properties['iso_type'] == nist_data['category']
        assert isotherm.properties['iso_ref'] == nist_data['isotherm_type']
        assert len(isotherm.data_raw) == len(nist_data['isotherm_data'])
        numpy.testing.assert_allclose(
            isotherm.pressure(),
            [point['pressure'] for point in nist_data['isotherm_data']],
            rtol=0,
            atol=0,
        )
        numpy.testing.assert_allclose(
            isotherm.loading(),
            [point['total_adsorption'] for point in nist_data['isotherm_data']],
            rtol=0,
            atol=0,
        )

    @pytest.mark.parametrize(
        'error, warning',
        [
            pytest.param(requests.exceptions.Timeout, 'Connection timeout', id='timeout'),
            pytest.param(requests.exceptions.ConnectionError, 'Connection error', id='connection'),
        ],
    )
    def test_request_failure(self, monkeypatch, caplog, error, warning):
        get = Mock(side_effect=error)
        monkeypatch.setattr(requests, 'get', get)

        with caplog.at_level(logging.WARNING, logger=pygaps.logger.name):
            assert isodb.isotherm_from_isodb('unavailable') is None

        get.assert_called_once_with(
            'https://adsorption.nist.gov/isodb/api/isotherm/unavailable.json',
            timeout=5,
        )
        assert [record.getMessage() for record in caplog.records if record.name == pygaps.logger.name] == [warning]

    def test_parse_failure(self, monkeypatch, caplog):
        get = Mock(return_value=SimpleNamespace(text='<html>Service unavailable</html>'))
        monkeypatch.setattr(requests, 'get', get)

        with caplog.at_level(logging.WARNING, logger=pygaps.logger.name):
            assert isodb.isotherm_from_isodb('invalid-response') is None

        get.assert_called_once_with(
            'https://adsorption.nist.gov/isodb/api/isotherm/invalid-response.json',
            timeout=5,
        )
        assert [record.getMessage() for record in caplog.records if record.name == pygaps.logger.name] == [
            'Could not parse isotherm. Check if the service is up.'
        ]

    @pytest.mark.network
    def test_get_isotherm_live(self):
        isotherm = isodb.isotherm_from_isodb('10.1002adfm.201200084.Isotherm3')

        assert isinstance(isotherm, pygaps.PointIsotherm)
        assert isotherm.material.name
        assert isotherm.adsorbate.name
        assert isotherm.temperature > 0
        assert not isotherm.data_raw.empty
        assert len(isotherm.pressure()) == len(isotherm.loading()) == len(isotherm.data_raw)
        assert numpy.isfinite(isotherm.pressure()).all()
        assert numpy.isfinite(isotherm.loading()).all()
