"""
Contains dictionaries for use in the Horvath-Kawazoe method
"""

_ADSORBENT_MODELS = ['Carbon(HK)', 'OxideIon(SF)']

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
