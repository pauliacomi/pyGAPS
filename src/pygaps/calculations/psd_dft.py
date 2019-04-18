"""
Module contains methods of calculating a pore size distribution starting from a DFT
kernel. Please note that calculation of the DFT/NLDFT/QSDFT kernels are outside the
scope of this program.
"""

import os

import numpy
import pandas
import scipy

from ..utilities.exceptions import CalculationError
from ..utilities.math_utilities import bspline

_KERNELS = {}

INTERNAL = os.path.join(os.path.dirname(__file__),
                        'kernels', 'dft - N2 - carbon.csv')


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
        The distributions for each width.

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
        raise Exception("The length of the pressure and loading arrays"
                        " do not match")

    # get the interpolation kernel
    kernel = _load_kernel(kernel_path)

    # generate the numpy arrays
    kernel_points = numpy.asarray([kernel[size](pressure) for size in kernel])
    pore_widths = numpy.asarray(list(kernel.keys()), dtype='float64')

    # define the minimization function
    def kernel_loading(pore_dist):
        return numpy.multiply(
            kernel_points, pore_dist[:, numpy.newaxis]      # -> multiply each loading with its contribution
        ).sum(axis=0)                                       # -> add the contributions together at each pressure

    def sum_squares(pore_dist):
        return numpy.square(                                                  # -> square the difference
            numpy.subtract(                                                   # -> between calculated and isotherm
                kernel_loading(pore_dist), loading)).sum(axis=0)              # -> then sum the squares together

    # define the constraints (x>0)
    cons = [{
        'type': 'ineq',
        'fun': lambda x: x,
    }]

    # # run the optimisation algorithm
    guess = numpy.array([0 for pore in pore_widths])
    bounds = [(0, None) for pore in pore_widths]
    result = scipy.optimize.minimize(
        sum_squares, guess, method='SLSQP',
        bounds=bounds, constraints=cons, options={'ftol': 1e-04})

    if not result.success:
        raise CalculationError(
            "Minimization of DFT failed with error {}".format(result.message)
        )

    # convert from preponderance to distribution
    final_loading = kernel_loading(result.x)
    pore_dist = result.x[1:] / numpy.diff(pore_widths)
    pore_widths, pore_dist = bspline(pore_widths[1:], pore_dist, degree=bspline_order)

    return pore_widths, pore_dist, final_loading


def _load_kernel(path):
    """
    Load a kernel from disk or from memory.

    Essentially takes a kernel stored as a pressure-loading
    table, then creates a cubic interpolator for each
    isotherm, then storing them as a dictionary of
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
    if path == 'internal':
        path = INTERNAL

    if path in _KERNELS:
        return _KERNELS[path]

    raw_kernel = pandas.read_csv(path, index_col=0)

    # add a 0 in the dataframe for interpolation between lowest values
    raw_kernel = raw_kernel.append(pandas.DataFrame(
        [0 for col in raw_kernel.columns], index=raw_kernel.columns, columns=[0]).transpose())

    kernel = {}
    for pore_size in raw_kernel:
        interpolator = scipy.interpolate.interp1d(
            raw_kernel[pore_size].index,
            raw_kernel[pore_size].values,
            kind='cubic')

        kernel.update({pore_size: interpolator})

    # Save the kernel in memory
    _KERNELS.update({path: kernel})

    return kernel
