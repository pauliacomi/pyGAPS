"""Pore size distribution calculations from an isotherm."""

from ..classes.adsorbate import Adsorbate
from ..graphing.calcgraph import psd_plot
from ..graphing.isothermgraphs import plot_iso
from ..utilities.exceptions import ParameterError
from .models_hk import get_hk_model
from .psd_dft import psd_dft_kernel_fit
from .psd_microporous import psd_horvath_kawazoe

_MICRO_PSD_MODELS = ['HK']
_PORE_GEOMETRIES = ['slit', 'cylinder', 'sphere']


def micropore_size_distribution(isotherm, psd_model, pore_geometry='slit',
                                verbose=False, **model_parameters):
    """
    Calculate the microporous size distribution using a 'classical' model.

    Parameters
    ----------
    isotherm : Isotherm
        Isotherm for which the pore size distribution will be calculated.
    psd_model : str
        The pore size distribution model to use.
    pore_geometry : str
        The geometry of the adsorbent pores.
    verbose : bool
        Prints out extra information on the calculation and graphs the results.

    Other Parameters
    ----------------
    adsorbate_model : dict
        The adsorbate model to use for PSD, If null, properties are taken
        from the adsorbate in the list.
    adsorbent_model : str or dict
        The adsorbent model to use for PSD, It defaults to Carbon(HK).

    Returns
    -------
    dict
        A dictionary with the pore widths and the pore distributions, of the form:

            - ``pore_widths`` (array) : the widths of the pores
            - ``pore_distribution`` (array) : contribution of each pore width to the
              overall pore distribution

    Notes
    -----
    Calculates the pore size distribution using a 'classical' model which attempts to
    describe the adsorption in a pore of specific width w at a relative pressure p/p0
    as a single function :math:`p/p0 = f(w)`. This function uses properties of the
    adsorbent and adsorbate as a way of determining the pore size distribution.

    Currently, the methods provided are:

        - the HK, or Horvath-Kawazoe method

    A common mantra of data processing is: "garbage in = garbage out". Only use methods
    when you are aware of their limitations and shortcomings.

    See Also
    --------
    pygaps.calculations.psd_microporous.psd_horvath_kawazoe : the HK, of Horvath-Kawazoe method

    """
    # Function parameter checks
    if psd_model is None:
        raise ParameterError("Specify a model to generate the pore size"
                             " distribution e.g. psd_model=\"BJH\"")
    if psd_model not in _MICRO_PSD_MODELS:
        raise ParameterError("Model {} not an option for psd.".format(psd_model),
                             "Available models are {}".format(_MICRO_PSD_MODELS))
    if pore_geometry not in _PORE_GEOMETRIES:
        raise ParameterError(
            "Geometry {} not an option for pore size distribution.".format(
                pore_geometry),
            "Available geometries are {}".format(_PORE_GEOMETRIES))
    if not isinstance(isotherm.adsorbate, Adsorbate):
        raise ParameterError("Isotherm adsorbate is not known, cannot calculate PSD.")

    adsorbent_model = model_parameters.get('adsorbent_model')
    if adsorbent_model is None:
        adsorbent_model = 'Carbon(HK)'

    # Get adsorbate properties
    adsorbate_properties = model_parameters.get('adsorbate_model')
    if adsorbate_properties is None:
        adsorbate_properties = {
            'molecular_diameter': isotherm.adsorbate.get_prop('molecular_diameter'),
            'polarizability': isotherm.adsorbate.get_prop('polarizability'),
            'magnetic_susceptibility': isotherm.adsorbate.get_prop('magnetic_susceptibility'),
            'surface_density': isotherm.adsorbate.get_prop('surface_density'),
            'liquid_density': isotherm.adsorbate.liquid_density(isotherm.t_iso),
            'adsorbate_molar_mass': isotherm.adsorbate.molar_mass(),
        }

    # Read data in
    loading = isotherm.loading(branch='ads',
                               loading_basis='molar',
                               loading_unit='mmol')
    pressure = isotherm.pressure(branch='ads',
                                 pressure_mode='relative')

    # Adsorbent model definitions
    adsorbent_properties = get_hk_model(adsorbent_model)

    # Call specified pore size distribution function
    if psd_model == 'HK':
        pore_widths, pore_dist = psd_horvath_kawazoe(
            loading, pressure, isotherm.t_iso, pore_geometry,
            adsorbate_properties, adsorbent_properties)

    # Package the results
    result_dict = {
        'pore_widths': pore_widths,
        'pore_distribution': pore_dist,
    }

    if verbose:
        psd_plot(pore_widths, pore_dist, log=False, right=2.5, method=psd_model)

    return result_dict


def dft_size_distribution(isotherm, kernel_path, verbose=False, bspline_order=2, **model_parameters):
    """
    Calculate the pore size distribution using a DFT kernel from a PointIsotherm.

    Parameters
    ----------
    isotherm : PointIsotherm
        The isotherm for which the pore size distribution will be calculated.
    kernel_path : str
        The path to the kernel used.
    bspline_order : int
        The smoothing order of the b-splines fit to the data.
        If set to 0, data will be returned as-is.

    Returns
    -------
    dict
        A dictionary with the pore widths and the pore distributions, of the form:

            - ``pore_widths`` (array) : the widths of the pores
            - ``pore_distribution`` (array) : contribution of each pore width to the
              overall pore distribution

    Notes
    -----
    *Description*

    Density Functional Theory (DFT) along with its extensions (NLDFT, QSDFT, etc)
    have emerged as the most powerful methods of describing adsorption on surfaces
    and in pores [#]_, [#]_. The theory allows the prediction of molecular behaviour solely
    on the basis of quantum mechanical considerations, and does not require other
    properties besides the electron structure and positions of the atoms involved.
    Calculations of large systems of atoms, such as those involved in adsorption
    in pores is a computationally intensive task, with modern computing power
    significantly improving the scales on which the modelling can be applied.

    The theory can be used to model adsorption in a simplified pore of a particular
    width which yields the the adsorption isotherm on a material comprised solely
    on pores of that width. The calculation is then repeated on pores of different
    sizes, to obtain a 'DFT kernel' or a collection of ideal isotherms on a
    distribution of pores. The generation of this kernel should be judicious, as
    both the adsorbent and the adsorbate must be modelled accurately. As it is a
    field in of in itself, the DFT calculations themselves are outside the scope
    of this program.

    Using the kernel, the isotherm obtained through experimental means can be
    modelled. The contributions of each kernel isotherm to the overall data is
    determined through a minimisation function. The contributions and their
    corresponding pore size form the pore size distribution of the material.

    The program accepts kernel files in a CSV format with the following structure:

    .. csv-table::
       :header: Pressure(bar), Pore size 1(nm), Pore size 2(nm), ..., Pore size y(nm)

        p1,l11,l21,...,ly1
        p2,l12,l22,...,ly2
        p3,l13,l23,...,ly3
        ...,...,...,...,...
        px,l1x,l2x,...,lyz

    The kernel should have sufficient points for a good interpolation as well as
    have a range of pressures that is wide enough to cover possible experimental
    values.

    *Limitations*

    The accuracy of predicting pore size through DFT kernels is only as good as
    the kernel itself, which should be tailored to the adsorbate, adsorbent and
    experimental conditions used.

    The isotherm used to calculate the pore size distribution should have enough
    datapoints and pressure range in order to cover adsorption in the entire range
    of pores the material has.

    See Also
    --------
    pygaps.calculations.psd_dft.psd_dft_kernel_fit : fitting of isotherm data with a DFT kernel

    References
    ----------
    .. [#] A New Analysis Method for the Determination of the Pore Size Distribution of Porous
       Carbons from Nitrogen Adsorption Measurements; Seaton, Walton, and Quirke; Carbon,
       Vol. 27, No. 6, pp. 853-861, 1989
    .. [#] Pore Size Distribution Analysis of Microporous Carbons: A Density Functional
       Theory Approach; Lastoskie, Gubbins, and Quirke; J. Phys. Chem. 1993, 97, 4786-4796

    """
    # Check kernel
    if kernel_path is None:
        raise ParameterError(
            "A path to the kernel to be used must be specified."
            "Use 'internal' to use the internal kernel (USE JUDICIOUSLY).")
    if not isinstance(isotherm.adsorbate, Adsorbate):
        raise ParameterError("Isotherm adsorbate is not known, cannot calculate PSD.")

    # Read data in
    loading = isotherm.loading(branch='ads',
                               loading_basis='molar',
                               loading_unit='mmol')
    pressure = isotherm.pressure(branch='ads',
                                 pressure_mode='relative')

    # Call the DFT function
    pore_widths, pore_dist, dft_loading = psd_dft_kernel_fit(
        pressure, loading, kernel_path, bspline_order)  # mmol/g

    # Convert to volume units
    pore_dist = pore_dist * max(loading) * isotherm.adsorbate.molar_mass() \
        / isotherm.adsorbate.liquid_density(isotherm.t_iso) / 1000

    # Package the results
    result_dict = {
        'pore_widths': pore_widths,
        'pore_distribution': pore_dist,
    }

    if verbose:
        params = {
            'plot_type': 'isotherm',
            'branch': 'ads',
            'logx': True,
            'fig_title': 'DFT Fit',
            'lgd_keys': ['material_name'],
            'y1_line_style': dict(markersize=5, linewidth=0)
        }
        ax = plot_iso(isotherm, **params)
        ax.plot(pressure, dft_loading, 'r-')
        psd_plot(pore_widths, pore_dist, method='DFT')

    return result_dict
