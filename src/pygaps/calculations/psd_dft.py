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

_KERNELS = {}

INTERNAL = os.path.join(os.path.dirname(__file__),
                        'kernels', 'dft - N2 - carbon.csv')


def psd_dft_kernel_fit(pressure, loading, kernel_path):
    """
    Fits a DFT kernel on experimental adsorption data.

    Parameters
    ----------
    loading : array
        Adsorbed amount in mmol/g.
    pressure : array
        Relative pressure.
    kernel_path : str
        The location of the kernel to use.

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

        f(x) = \\sum_{p=p_0}^{p=p_x} (n_{p,exp} - \\sum_{w=w_0}^{w=w_y} n_{p, kernel} X_w )^2

    The function is then minimised using the `scipy.optimise.minimise` module, with the
    constraint that the contribution of each isotherm cannot be negative.

    """
    # Parameter checks
    if len(pressure) != len(loading):
        raise Exception("The length of the pressure and loading arrays"
                        " do not match")

    # get the interpolation kernel
    kernel = _load_kernel(kernel_path)

    # generate the pandas array
    kernel_points = []
    for psize in kernel:
        kernel_points.append(kernel.get(psize)(pressure))

    pore_widths = numpy.array(list(kernel.keys())).astype(float)

    points_arr = pandas.DataFrame(
        kernel_points,
        index=pore_widths,
        columns=pressure)

    # define the minimization function
    def sum_squares(pore_dist):
        return (points_arr.multiply(pore_dist, axis=0)
                # -> multiply each loading with its contribution
                .sum()
                # -> add the contributions together at each pressure
                .subtract(loading)
                # -> difference between calculated and isotherm
                .pow(2)
                # -> square the difference
                .sum()
                # -> sum of squares together
                )

    # define the constraints (x>0)
    cons = [{
        'type': 'ineq',
        'fun': lambda x: x,
    }]

    # run the optimisation algorithm
    guess = [0 for pore in points_arr.index]
    bounds = [(0, None) for pore in points_arr.index]
    result = scipy.optimize.minimize(
        sum_squares, guess, method='SLSQP',
        bounds=bounds, constraints=cons)

    if not result.success:
        raise CalculationError(
            "Minimization of DFT failed with error {1}".format(result.message)
        )

    pore_dist = result.x

    return pore_widths, pore_dist


def _load_kernel(path):
    """
    Loads a kernel from disk or from memory.

    Parameters
    ----------
    path : str
        Path to the kernel to load in .csv form.

    Returns
    -------
    array
        The kernel.
    """
    if path == 'internal':
        path = INTERNAL

    if path in _KERNELS:
        return _KERNELS[path]

    else:
        raw_kernel = pandas.read_csv(path, index_col=0)

        # add a 0 in the dataframe for interpolation between lowest values
        raw_kernel = raw_kernel.append(pandas.DataFrame(
            [0 for col in raw_kernel.columns], index=raw_kernel.columns, columns=[0]).transpose())

        kernel = dict()
        for pore_size in raw_kernel:
            interpolator = scipy.interpolate.interp1d(
                raw_kernel[pore_size].index,
                raw_kernel[pore_size].values,
                kind='cubic')

            kernel.update({pore_size: interpolator})

        # Save the kernel in memory
        _KERNELS.update({path: kernel})

    return kernel
