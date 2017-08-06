"""
This test module has tests relating to classes
"""

import pytest
import pandas
import adsutils


def test_isotherm_created(basic_isotherm):
    "Checks isotherm can be created from test data"

    return basic_isotherm


@pytest.mark.parametrize('missing_param',
                         ['sample_name', 'sample_batch', 't_exp', 'gas']
                         )
def test_isotherm_miss_param(isotherm_data, missing_param):
    "Tests exception throw for missing required attributes"
    data = isotherm_data
    del data.info[missing_param]

    with pytest.raises(Exception):
        adsutils.PointIsotherm(
            data.isotherm_df,
            loading_key=data.loading_key,
            pressure_key=data.pressure_key,
            other_keys=data.other_keys,
            **data.info)

    return


@pytest.mark.parametrize('missing_key',
                         ['loading_key', 'pressure_key']
                         )
def test_isotherm_miss_key(isotherm_data, missing_key):
    "Tests exception throw for missing data primary key (loading/pressure)"
    data = isotherm_data
    setattr(data, missing_key, None)

    with pytest.raises(Exception):
        adsutils.PointIsotherm(
            data.isotherm_df,
            loading_key=data.loading_key,
            pressure_key=data.pressure_key,
            other_keys=data.other_keys,
            **data.info)

    return


def test_isotherm_ret_funcs(isotherm_data, basic_isotherm):
    "Checks that all the functions in pointIsotherm return their specified parameter"

    data = isotherm_data
    isotherm = basic_isotherm

    assert set(isotherm.pressure_all()) == set(
        [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 4.0, 2.0])
    assert set(isotherm.loading_all()) == set(
        [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 4.0, 2.0])
    assert set(isotherm.other_key_ads(data.other_key)) == set([
        5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0])

    assert isotherm.has_ads()
    assert isotherm.has_des()

    assert isotherm.adsdata().equals(pandas.DataFrame({
        data.pressure_key: [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        data.loading_key: [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        data.other_keys[data.other_key]: [5.0, 5.0, 5.0, 5.0, 5.0, 5.0],
    }))

    assert isotherm.desdata().equals(pandas.DataFrame({
        data.pressure_key: [4.0, 2.0],
        data.loading_key: [4.0, 2.0],
        data.other_keys[data.other_key]: [5.0, 5.0],
    }, index=[6, 7]))

    assert set(isotherm.pressure_ads()) == set([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    assert set(isotherm.loading_ads()) == set([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    assert set(isotherm.other_key_ads(data.other_key)
               ) == set([5.0, 5.0, 5.0, 5.0, 5.0, 5.0])
    assert set(isotherm.pressure_des()) == set([4.0, 2.0])
    assert set(isotherm.loading_des()) == set([4.0, 2.0])
    assert set(isotherm.other_key_des(data.other_key)) == set([5.0, 5.0])

    return
