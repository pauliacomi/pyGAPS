"""
Dictionaries or generators which provide properties
for use in the Horvath-Kawazoe method.
"""

from ..utilities.exceptions import ParameterError

HK_KEYS = {
    'molecular_diameter': 'nm',
    'polarizability': 'nm3',
    'magnetic_susceptibility': 'nm3',
    'surface_density': 'molecules/m2',
}

PROPERTIES_CARBON = {
    'molecular_diameter': 0.34,  # nm
    'polarizability': 1.02E-3,  # nm3
    'magnetic_susceptibility': 1.35E-7,  # nm3
    'surface_density': 3.845E19,  # molecules/m2
}

PROPERTIES_AlSi_OXIDE_ION = {
    'molecular_diameter': 0.276,  # nm
    'polarizability': 2.5E-3,  # nm3
    'magnetic_susceptibility': 1.3E-8,  # nm3
    'surface_density': 1.315E19,  # molecules/m2
}

PROPERTIES_AlPh_OXIDE_ION = {
    'molecular_diameter': 0.260,  # nm
    'polarizability': 2.5E-3,  # nm3
    'magnetic_susceptibility': 1.3E-8,  # nm3
    'surface_density': 1.000E19,  # molecules/m2
}

_ADSORBENT_MODELS = {
    'Carbon(HK)': PROPERTIES_CARBON,
    'AlSiOxideIon': PROPERTIES_AlSi_OXIDE_ION,
    'AlPhOxideIon': PROPERTIES_AlPh_OXIDE_ION,
}


def get_hk_model(model):
    """
    Get the adsorbent model for HK PSD.

    The ``model`` parameter is a string which names the parameters which should be returned.
    Alternatively, a user can implement their own adsorbent model, by passing a dict.

    Parameters
    ----------
    model : `str` or `dict`
        Name of the model to use or a dict with the parameters.

    Returns
    -------
    dict
        A dict with parameters for the HK model.

    Raises
    ------
    ParameterError
        When string is not in the dictionary of models.
    """
    # If the model is a string, get a model from the _ADSORBENT_MODELS
    if isinstance(model, str):
        if model not in _ADSORBENT_MODELS:
            raise ParameterError(
                f"Model ({model}) is not an option for pore size distribution.",
                f"Available models are {_ADSORBENT_MODELS.keys()}"
            )

        return _ADSORBENT_MODELS[model]

    # If the model is an dictionary, use it as is
    if isinstance(model, dict):
        for key in HK_KEYS.items():
            if key[0] not in model.keys():
                raise ParameterError(
                    f"The passed dictionary must contain the parameter {key[0]} "
                    f"in the units of {key[1]}"
                )

        return model

    # Raise error if anything else is passed
    raise ParameterError(
        f"Model parameters ({model}) not an option for pore size distribution. ",
        f"Available models are {_ADSORBENT_MODELS.keys()}."
        " Or pass a dictionary with the required parameters"
    )
