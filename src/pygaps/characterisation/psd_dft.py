"""
Module contains methods of calculating a pore size distribution starting from a DFT
kernel. Please note that calculation of DFT/NLDFT/QSDFT kernels is outside the
scope of this program.
"""

from pathlib import Path

import numpy
import pandas

from .. import scipy
from ..core.adsorbate import Adsorbate
from ..graphing.calc_graphs import psd_plot
from ..graphing.isotherm_graphs import plot_iso
from ..graphing.mpl_styles import POINTS_ALL_STYLE
from ..utilities.exceptions import CalculationError
from ..utilities.exceptions import ParameterError
from ..utilities.math_utilities import bspline

_KERNELS = {
    'DFT-N2-77K-carbon-slit':
    Path(__file__).parent / 'kernels' / 'DFT-N2-77K-carbon-slit.csv',
}

_LOADED = {}  # We will keep loaded kernels here


def psd_dft(
    isotherm,
    kernel='DFT-N2-77K-carbon-slit',
    branch='ads',
    p_limits=None,
    bspline_order=2,
    kernel_units=None,
    verbose=False,
):
    """
    Calculate the pore size distribution using a DFT kernel from a PointIsotherm.

    Parameters
    ----------
    isotherm : PointIsotherm
        The isotherm for which the pore size distribution will be calculated.
    kernel : str
        The name of the kernel, or the path where it can be found.
    branch : {'ads', 'des'}, optional
        Branch of the isotherm to use. It defaults to adsorption.
    p_limits : [float, float]
        Pressure range in which to calculate PSD, defaults to entire isotherm.
    bspline_order : int
        The smoothing order of the b-splines fit to the data.
        If set to 0, data will be returned as-is.
    kernel_units : dict
        A dictionary of kernel basis and units, contains ``loading_basis``,
        ``loading_unit``, ``material_basis``, ``material_unit``, ``pressure_mode``
        and "pressure_unit". Defaults to mmol/g in relative pressure.
    verbose : bool
        Prints out extra information on the calculation and graphs the results.

    Returns
    -------
    dict
        A dictionary with the pore widths and the pore distributions, of the form:

            - ``pore_widths`` (array) : the widths of the pores
            - ``pore_distribution`` (array) : contribution of each pore width to the
              overall pore distribution

    Notes
    -----
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
    of pores.

    See Also
    --------
    pygaps.characterisation.psd_dft.psd_dft_kernel_fit : backend function for DFT kernel fitting

    References
    ----------
    .. [#] A New Analysis Method for the Determination of the Pore Size Distribution of Porous
       Carbons from Nitrogen Adsorption Measurements; Seaton, Walton, and Quirke; Carbon,
       Vol. 27, No. 6, pp. 853-861, 1989
    .. [#] Pore Size Distribution Analysis of Microporous Carbons: A Density Functional
       Theory Approach; Lastoskie, Gubbins, and Quirke; J. Phys. Chem. 1993, 97, 4786-4796

    """
    # Check kernel
    if kernel is None:
        raise ParameterError(
            "An existing kernel name or a path to a user kernel to be used must be specified."
        )
    if not isinstance(isotherm.adsorbate, Adsorbate):
        raise ParameterError(
            "Isotherm adsorbate is not known, cannot calculate PSD."
        )

    # Get an internal kernel, otherwise assume it is a path
    if kernel in _KERNELS:
        kernel_path = _KERNELS[kernel]
    else:
        kernel_path = kernel

    # Get units
    if kernel_units is None:
        kernel_units = {}

    loading_basis = kernel_units.get('loading_basis', 'molar')
    loading_unit = kernel_units.get('loading_unit', 'mmol')
    material_basis = kernel_units.get('material_basis', 'mass')
    material_unit = kernel_units.get('material_unit', 'g')
    pressure_mode = kernel_units.get('pressure_mode', 'relative')
    pressure_unit = kernel_units.get('pressure_unit', None)

    # Read data in
    loading = isotherm.loading(
        branch=branch,
        loading_basis=loading_basis,
        loading_unit=loading_unit,
        material_basis=material_basis,
        material_unit=material_unit
    )
    pressure = isotherm.pressure(
        branch=branch,
        pressure_mode=pressure_mode,
        pressure_unit=pressure_unit
    )
    if loading is None:
        raise ParameterError(
            "The isotherm does not have the required branch "
            "for this calculation"
        )
    # If on an desorption branch, data will be reversed
    if branch == 'des':
        loading = loading[::-1]
        pressure = pressure[::-1]

    # Determine the limits
    if not p_limits:
        p_limits = (None, None)
    minimum = 0
    maximum = len(pressure)
    if p_limits[0]:
        minimum = numpy.searchsorted(pressure, p_limits[0])
    if p_limits[1]:
        maximum = numpy.searchsorted(pressure, p_limits[1])
    if maximum - minimum < 3:  # (for 3 point minimum)
        raise CalculationError(
            "The isotherm does not have enough points (at least 3) "
            "in the selected region."
        )
    pressure = pressure[minimum:maximum]
    loading = loading[minimum:maximum]

    # Call the DFT function
    pore_widths, pore_dist, pore_load_cum = psd_dft_kernel_fit(
        pressure, loading, kernel_path, bspline_order
    )  # mmol/g

    dpore_widths = numpy.ediff1d(pore_widths, to_begin=pore_widths[0])
    pore_vol_cum = numpy.cumsum(pore_dist * dpore_widths)

    if verbose:
        params = {
            'branch': branch,
            'logx': True,
            'fig_title': 'DFT Fit',
            'lgd_keys': ['material'],
            'y1_line_style': POINTS_ALL_STYLE,
            'loading_basis': loading_basis,
            'loading_unit': loading_unit,
            'material_basis': material_basis,
            'material_unit': material_unit,
            'pressure_mode': pressure_mode,
            'pressure_unit': pressure_unit,
        }
        ax = plot_iso(isotherm, **params)
        ax.plot(pressure, pore_load_cum, 'r-')
        psd_plot(
            pore_widths, pore_dist, pore_vol_cum=pore_vol_cum, method='DFT'
        )

    return {
        'pore_widths': pore_widths,
        'pore_distribution': pore_dist,
        'pore_volume_cumulative': pore_vol_cum,
    }


def psd_dft_kernel_fit(pressure, loading, kernel_path, bspline_order=2):
    r"""
    Fit a DFT kernel on experimental adsorption data.

    Parameters
    ----------
    loading : array
        Adsorbed amount in mmol/g.
    pressure : array
        Relative pressure.
    kernel_path : str
        The location of the kernel to use.
    bspline_order : int
        The smoothing order of the b-splines fit to the data.
        If set to 0, data will be returned as-is.

    Returns
    -------
    pore widths : array
        The widths of the pores.
    pore_dist : array
        The distributions for each width (dV/dw).
    pore_load_cum : array
        Cumulative pore loading.

    Notes
    -----
    The function will take the data in the form of pressure and loading. It will
    then load the kernel either from disk or from memory and define a minimsation
    function as the sum of squared differences of the sum of all individual kernel
    isotherm loadings multiplied by their contribution as per the following function:

    .. math::

        f(x) = \sum_{p=p_0}^{p=p_x} (n_{p,exp} - \sum_{w=w_0}^{w=w_y} n_{p, kernel} X_w )^2

    The function is then minimised using the `scipy.optimise.minimise` module, with the
    constraint that the contribution of each kernel isotherm cannot be negative.

    """
    # Parameter checks
    if len(pressure) != len(loading):
        raise Exception(
            "The length of the pressure and loading arrays"
            " do not match"
        )

    # get the interpolation kernel
    kernel = _load_kernel(kernel_path)

    # generate the numpy arrays
    try:
        kernel_points = numpy.asarray([
            kernel[size](pressure) for size in kernel
        ])
    except ValueError:
        raise CalculationError(
            "Could not get kernel values at isotherm points. "
            "Does your kernel pressure range apply to this isotherm?"
        )
    pore_widths = numpy.asarray(list(kernel.keys()), dtype='float64')

    # define the minimization function
    def kernel_loading(pore_dist):
        return numpy.multiply(
            kernel_points,
            pore_dist[:, numpy.newaxis
                      ]  # -> multiply each loading with its contribution
        ).sum(axis=0)  # -> add the contributions together at each pressure

    def sum_squares(pore_dist):
        return numpy.square(  # -> square the difference
            numpy.subtract(  # -> between calculated and isotherm
                kernel_loading(pore_dist),
                loading)).sum(axis=0)  # -> then sum the squares together

    # define the constraints (x>0)
    cons = [{
        'type': 'ineq',
        'fun': lambda x: x,
    }]

    # # run the optimisation algorithm
    guess = numpy.array([0 for pore in pore_widths])
    bounds = [(0, None) for pore in pore_widths]
    result = scipy.optimize.minimize(
        sum_squares,
        guess,
        method='SLSQP',
        bounds=bounds,
        constraints=cons,
        options={'ftol': 1e-04}
    )

    if not result.success:
        raise CalculationError(
            f"Minimization of DFT failed with error: {result.message}"
        )

    # convert from preponderance to distribution
    final_loading = kernel_loading(result.x)
    pore_dist = result.x / numpy.ediff1d(pore_widths, to_begin=pore_widths[0])
    pore_widths, pore_dist = bspline(
        pore_widths, pore_dist, degree=bspline_order
    )

    return pore_widths, pore_dist, final_loading


def _load_kernel(path):
    """
    Load a kernel from disk or from memory.

    Essentially takes a kernel stored as a pressure-loading
    table, creates an interpolator for each
    isotherm, then stores them as a dictionary of
    pore-size keys to interpolator values.

    Parameters
    ----------
    path : str
        Path to the kernel to load in .csv form.

    Returns
    -------
    dict
        The kernel with its pore size components as keys.
    """
    if path in _LOADED:
        return _LOADED[path]

    raw_kernel = pandas.read_csv(path, index_col=0)

    # add a 0 in the dataframe for interpolation between lowest values
    raw_kernel = raw_kernel.append(
        pandas.DataFrame([0 for col in raw_kernel.columns],
                         index=raw_kernel.columns,
                         columns=[0]).transpose()
    )

    kernel = {}
    for pore_size in raw_kernel:
        interpolator = scipy.interp.interp1d(
            raw_kernel[pore_size].index,
            raw_kernel[pore_size].values,
            kind='cubic'
        )

        kernel.update({pore_size: interpolator})

    # Save the kernel in memory
    _LOADED[path] = kernel

    return kernel
