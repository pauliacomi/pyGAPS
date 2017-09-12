==========
Quickstart
==========

Creating an isotherm
--------------------

First, to use pyGAPS in a python or jupyther project, import it::

    import pygaps

The backbone of the framework is the PointIsotherm class. This class stores the isotherm
data, isotherm properties such as material and adsorbate with which it was measured, as well
as providing easy interaction with the framework calculations. There are several ways to create
a PointIsotherm object:

    - a pandas.DataFrame
    - a json string or file
    - parsing excel files
    - parsing csv files
    - from an sqlite database

If using a pandas DataFrame, first the two components of the isotherm should be created:
a dictionary with the parameters and a DataFrame with the data.

The isotherm parameters dictionary has to have at least four specific components: the sample
name, the sample batch, the adsorbent used and the temperature (in K) at which the data was
recorded::

    isotherm_parameters = {
        'sample_name' : 'carbon',
        'sample_batch' : 'X1',
        'adsorbate' : 'nitrogen',
        't_exp' : 77,
    }

The pandas DataFrame which contains the data should have at least two columns: the pressures
at which each point was recorded, and the loadings for each point. Other data columns, such
as calorimetry data, magnetic field strengths, or other simultaneous measurements are also
supported.::

    isotherm_data = pandas.DataFrame({
        'pressure' : [1, 2, 3, 4, 5, 3, 2]
        'loading' : [1, 2, 3, 4, 5, 3, 2]
    })

With these two components, the isotherm can be created::

    isotherm = pygaps.PointIsotherm(
        isotherm_data,
        loading_key='loading',
        pressure_key='pressure',
        isotherm_parameters
    )

The `loading_key` and `pressure_key` parameters specify which column in the DataFrame
contain which data of the isotherm. By default, the loading is read in *mmmol/g* and the
pressure is read in *bar*, although these settings can be changed.

To see a summary of the isotherm as well as a graph, use the included function::

    isotherm.print_info()

Now that the PointIsotherm is created, we are ready to do some analysis.


Isotherm analysis with pyGAPS
-----------------------------

The framework has several isotherm analysis tools which are commonly used to characterise
porous materials such as:

    - BET surface area
    - the t-plot method
    - the :math:`\\alpha_s` method
    - mesoporous PSD (pore size distribution) calculations
    - microporous PSD calculations
    - DFT kernel fitting PSD methods
    - isosteric heat of adsorption calculation

From a PointIsotherm object, it's easy to start a characterisation. For example, to get
a dictionary with all the parameters of the BET surface area analysis, use::

    result_dict = pygaps.area_BET(isotherm)

If in an interactive environment, such as iPython or jupyther, it is useful to see the
details of the calculation directly. To do this, increase the verbosity of the method::

    result_dict = pygaps.t_plot(isotherm, verbose=True)

Depending on the method, different parameters can be passed to change the way the
calculations are performed. For example, if a mesoporous size distribution is
desired using the Dollimore-Heal method on the adsorption branch of the isotherm,
assuming the pores are cylindrical, one side open and that adsorbate thickness can
be described by a Halsey-type thickness curve, the code will look like::

    result_dict = pygaps.mesopore_size_distribution(
        isotherm,
        psd_model='DH',
        pore_geometry='cylindrical',
        thickness_model='Halsey',
        verbose=True
    )

For more information on how to use each method, check the detailed manual.

.. caution::
   The results obtained using these tools are only as good as the data and settings
   chosen. Errors are thrown wherever possible, but the user should be aware of the
   theory and applicability behind the methods. A couple of examples where there's a
   high posibility of the results being a waste of CPU cycles:

    - Using isotherms measured at high temperatures and pressures where the difference
      between *excess* and *absolute* adsorption becomes significant.

    - Using a provided model with a wrong adsorbate or temperature range, for
      example using the Halsey thickness curve on anything else besides nitrogen at 77K
      or the internal DFT kernel on isotherms measured on MOFs.

    - Assuming the BET surface area has physical significance when applied on an
      ultramicroporpus adsorbent. (it is still useful as a fingerprinting tool)


Isotherm modelling with pyGAPS
------------------------------

The framework comes with functionality to model point isotherm data with common
isotherm models such as:

    - Henry
    - Langmuir
    - Double/Triple site Langmuir
    - Temkin
    - FH-VST

The modelling is done through the ModelIsotherm class. The class is similar to the
PointIsotherm class, and shares the same ability to store parameters. However, instead of
data, it stores model coefficients for the model it's describing.

To create a ModelIsotherm, the same parameters dictionary / pandas DataFrame procedure can
be used. But, assuming we've already created a PointIsotherm object, we can use it to instantiate
the ModelIsotherm instead. To do this we use the class method::

    model_iso = pygaps.ModelIsotherm.from_pointisotherm(isotherm, model='Langmuir')

A minimisation procedure will then attempt to fit the model's parameters to the isotherm points.
If successful, the ModelIsotherm is returned.

In case the model which best fits the data is desired, the class method can also be passed a
bool which allows the ModelIsotherm to select the best fitting model. This means that all
models available will be calculated and the best one will be returned and will of course
take more processing power.

    model_iso = pygaps.ModelIsotherm.from_pointisotherm(isotherm, guess_model=True)

More advanced settings can also be specified, such as the optimisation model to be used in the
optimisation routine or the initial parameter guess.

To print the model parameters use the internal print function. The calculation of loading
made with the model can be accessed by using the loading function::

    # Prints isotherm parameters and model info
    model_iso.print_info()

    # Returns the loading at 1 bar calculated with the model
    model_iso.loading_at(1)

    # Returns the loading in the range 0-1 bar calculated with the model
    pressure = [0:0.1:1]
    model_iso.loading_at(pressure)


Using models for IAST calculations
----------------------------------


Graphing
--------

pyGAPS makes graphing both PointIsotherm and ModelIsotherm objects easy to facilitate
visual observations, inclusion in publications and consistency. Plotting an isotherm is
as simple as::

    pygaps.plot_iso([isotherm])

Many settings can be specified to change the look and feel of the graphs. More settings
can be found in the manual.
