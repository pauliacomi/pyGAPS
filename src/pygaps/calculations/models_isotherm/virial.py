"""
Virial isotherm model
"""

import matplotlib.pyplot as plt
import numpy
import scipy

from ...utilities.exceptions import CalculationError
from .model import IsothermModel


class Virial(IsothermModel):
    """

    A virial isotherm model with 3 factors.

    .. math::

        p = n \\exp{(-\\ln{K_H} + An + Bn^2 + Cn^3)}

    Notes
    -----

    A virial isotherm model attempts to fit the measured data to a factorized
    exponent relationship between loading and pressure.

    .. math::

        p = n \\exp{(K_1n^0 + K_2n^1 + K_3n^2 + K_4n^3 + ... + K_i n^{i-1})}

    It has been applied with success to describe the behaviour of standard as
    well as supercritical isotherms. The factors are usually empirical,
    although some relationship with physical can be determined:
    the first constant is related to the Henry constant at zero loading, while
    the second constant is a measure of the interaction strength with the surface.

    .. math::

        K_1 = -\\ln{K_{H,0}}

    In practice, besides the first constant, only 2-3 factors are used.

    """

    #: Name of the model
    name = 'Virial'
    calculates = 'pressure'

    def __init__(self):
        """
        Instantiation function
        """

        self.params = {"K": numpy.nan, "A": numpy.nan,
                       "B": numpy.nan, "C": numpy.nan}

    def loading(self, pressure):
        """
        Function that calculates loading.

        Careful!
        For the Virial model, the loading has to
        be computed numerically.

        Parameters
        ----------
        pressure : float
            The pressure at which to calculate the loading.

        Returns
        -------
        float
            Loading at specified pressure.
        """

        def fun(x):
            return (self.pressure(x) - pressure)**2

        opt_res = scipy.optimize.minimize(fun, pressure, method='Nelder-Mead')

        if not opt_res.success:
            raise CalculationError("""
            Root finding for failed. Error: \n\t{}
            """.format(opt_res.message))

        return opt_res.x

    def pressure(self, loading):
        """
        Function that calculates pressure as a function
        of loading.

        The Virial model calculates the pressure directly.

        Parameters
        ----------
        loading : float
            The loading at which to calculate the pressure.

        Returns
        -------
        float
            Pressure at specified loading.
        """
        return loading * numpy.exp(-numpy.log(self.params['K']) + self.params['A'] * loading
                                   + self.params['B'] * loading**2 + self.params['C'] * loading**3)

    def spreading_pressure(self, pressure):
        """
        Function that calculates spreading pressure by solving the
        following integral at each point i.

        .. math::

            \\pi = \\int_{0}^{p_i} \\frac{n_i(p_i)}{p_i} dp_i

        The integral for the Virial model cannot be solved analytically
        and must be calculated numerically.

        Parameters
        ----------
        pressure : float
            The pressure at which to calculate the spreading pressure.

        Returns
        -------
        float
            Spreading pressure at specified pressure.
        """
        raise NotImplementedError

    def default_guess(self, data, loading_key, pressure_key):
        """
        Returns initial guess for fitting

        Parameters
        ----------
        data : pandas.DataFrame
            Data of the isotherm.
        loading_key : str
            Column with the loading.
        pressure_key : str
            Column with the pressure.

        Returns
        -------
        dict
            Dictionary of initial guesses for the parameters.
        return None
        """
        saturation_loading, langmuir_k = super(Virial, self).default_guess(
            data, loading_key, pressure_key)

        return {"K": saturation_loading * langmuir_k,
                "A": 0, "B": 0, "C": 0}

    def fit(self, loading, pressure, param_guess, optimization_method=None, verbose=False):
        """
        Fit model to data using nonlinear optimization with least squares loss
        function. Assigns parameters to self

        Parameters
        ----------
        loading : ndarray
            The loading for each point.
        pressure : ndarray
            The pressures of each point.
        optimization_method : str
            Method in SciPy minimization function to use in fitting model to data.
        verbose : bool, optional
            Prints out extra information about steps taken.
        """
        if verbose:
            print("Attempting to model using {}".format(self.name))

        ln_p_over_n = numpy.log(numpy.divide(pressure, loading))

        full_info = numpy.polyfit(loading, ln_p_over_n, 3, full=True)
        virial_constants = full_info[0]

        self.params['K'] = numpy.exp(-virial_constants[3])
        self.params['A'] = virial_constants[2]
        self.params['B'] = virial_constants[1]
        self.params['C'] = virial_constants[0]

        rmse = numpy.sqrt(full_info[1] / len(pressure))

        # logging for debugging
        if verbose:
            print("Model {0} success, rmse is {1}".format(
                self.name, rmse))
            print("Virial coefficients:", full_info[0])
            print("Residuals:", full_info[1])
            print("Rank:", full_info[2])
            print("Singular values:", full_info[3])
            print("Conditioning threshold:", full_info[4])
            xp = numpy.linspace(0, numpy.amax(loading), 100)
            virial_func = numpy.poly1d(virial_constants)
            plt.plot(loading, ln_p_over_n, '.', xp, virial_func(xp), '-')
            plt.title("Virial fit")
            plt.xlabel("Loading")
            plt.ylabel("ln(p/n)")
            plt.show()

        return rmse
