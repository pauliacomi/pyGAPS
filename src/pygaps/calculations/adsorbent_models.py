"""
Contains dictionaries for use in the Horvath-Kawazoe method
"""


def get_adsorbent_model(model):
    """
    Gets the adsorbent model for HK psd

    The ``model`` parameter is a string which names the parameters which should be returned.
    Alternatively, a user can implement their own adsorbent model, by passing a dict.

    Parameters
    ----------
    model : obj(`str`) or obj(`dict`)
        Name of the model to use or a dict with the parameters.

    Returns
    -------
    dict
        A dict with parameters for the HK model.

    Raises
    ------
    Exception
        When string is not in the dictionary of models.
    """
    # If the model is a string, get a model from the _THICKNESS_MODELS
    if isinstance(model, str):
        if model not in _ADSORBENT_MODELS:
            raise Exception("Model {} not an option for t-plot.".format(model),
                            "Available models are {}".format(_ADSORBENT_MODELS.keys()))
        else:
            a_model = _ADSORBENT_MODELS[model]

    # If the model is an isotherm, transform it into a thickness curve
    elif isinstance(model, dict):
        a_model = model

    # Raise error if anything else is passed
    else:
        raise Exception("Model {} not an option for t-plot.".format(model),
                        "Available models are {}".format(_ADSORBENT_MODELS))

    return a_model


PROPERTIES_CARBON = dict(
    molecular_diameter=0.34,            # nm
    polarizability=1.02E-30,            # m3
    magnetic_susceptibility=1.35E-34,   # m3
    surface_density=3.845E19,           # molecules/m2
)

PROPERTIES_OXIDE_ION = dict(
    molecular_diameter=0.276,            # nm
    polarizability=2.5E-30,            # m3
    magnetic_susceptibility=1.3E-34,   # m3
    surface_density=1.315E19,           # molecules/m2
)


_ADSORBENT_MODELS = {'Carbon(HK)': PROPERTIES_CARBON,
                     'OxideIon(SF)': PROPERTIES_OXIDE_ION}
