
Changelog
=========

2.0.2 (2019-12-18)
------------------

New features:

 * Added fluids to database: n-pentane, n-hexane, n-octane, o-xylene, m-xylene, p-xylene,
   cyclohexane, hydrogen sulfide and sulfur hexafluoride.

Fixes:

 * Converting Adsorbates to a dictionary now correctly outputs the list of aliases.
 * Changed stored critical point molar mass values for some adsorbates.

2.0.1 (2019-07-08)
------------------

 * Fixed error in dft kernel acquisition.
 * Removed duplicate plot generation from virial initial henry.
 * Fixed Appveyor testing.

2.0.0 (2019-07-08)
------------------

Major pyGAPS release following peer review on related manuscript.
Several breaking changes with previous codebase, in particular
with basic isotherm parameters and module structure.
Several function names and parameters have changed as well.

Breaking changes:

 * Renamed isotherm parameter `t_iso` to `temperature` for clarity.
 * Renamed isotherm parameter `material_name` to `material`.
 * Made `material_batch` an optional parameter.
 * Renamed the `pytest.calculations` submodule to
   `pytest.characterisation`.
 * Placed all isotherm models in a `pytest.modelling` submodule.

New features:

* The isotherm branches are now saved in the file representation
  (JSON, CSV, Excel).
* Not specifying units now raises a warning.
* After attempting a model fit or guess for the creation of a
  ModelIsotherm, a fit graph is now plotted alongside the data to
  be modelled.
* Added a new parameters named logy1 and logy2 to
  set the plotting vertical axes to be logarithmic.
* To remove the legend now set the lgd_pos to None

* Pore size distribution improvements:

    * Changed names of PSD functions to `psd_microporous`,
      `psd_mesoporous` and `psd_dft`, respectively.
    * Simplified functions for ease of use and understanding.
    * Added cumulative pore volume to the return dictionary of all
      psd functions.
    * Generalized Kelvin methods (psd_mesoporous) to other
      pore geometries, such as slit and sphere.
    * Added a new Kelvin function, the Kelvin Kruck-Jaroniec-Sayari
      correction (use with `kelvin_function='Kelvin-KJS'`
    * Corrected a conversion error in the DFT fitting routing.
    * Changed HK dictionary name OxideIon(SF) -> 'AlSiOxideIon'
    * Added a new HK dictionary 'AlPhOxideIon'



1.6.1 (2019-05-09)
------------------

New features:

* Simplified the slope method for Henry's constant
  calculation

Bugfixes:

* Ensured that model initial fitting guess cannot be
  outside the bounds of the variables.

1.6.0 (2019-05-08)
------------------

New features:

* Added a function to get isotherms from the NIST ISODB,
  ``pygaps.load_nist_isotherm`` which takes the ISODB filename
  as an argument.
* Added hexane as an adsorbate in the database.
* Isotherm adsorbate is now a pygaps.Adsorbate object and
  can be accessed directly for all attributes
  (only when available in the internal database, otherwise still a string).
* ModelIsotherms can now be saved and imported from JSON, CSV and Excel.
* Added a ``marker`` option to the ``plot_iso`` function
  which acts similar to the ``color`` parameter and allows
  simple selection of the marker style.
* Added three new isotherm models: Freundlich, Dubinin-Radushkevich and
  Dubinin-Astakov. They can be used for fitting by specifying
  `Freundlich`, `DR` or `DA` as the model, respectivelly.
* Faster performance of some models due to analytical calculations,
  as well as more thorough testing
* Isotherm modelling backend is now more robust.
* Added an isotherm ``plot`` function to plot an individual isotherm.
* Added functions to import and export JSON files directly from a
  file: ``isotherm_from_jsonf`` and ``isotherm_to_jsonf``.
* Added github issue templates.
* Removed some plotting styles.

Breaking changes:

* Deprecated and removed the MADIREL excel format.
* Renamed ``isosteric_heat`` functions as ``isosteric_enthalpy`` for
  more correct nomenclature.
* Some model parameters have been renamed for consistency.

Bugfixes:

* REFPROP backend now correctly accessible
  (it was previously impossible to activate).
* Fixed issue in excel import which could lead to
  incorrect import.
* Some of the adsorbate values in the database were incorrect.
  They have been now updated.
* Fixed secondary data not being automatically plotted
  when ``print_info`` called.


1.5.0 (2019-03-12)
------------------

New features:

* Increased number of adsorbates available in pyGAPS to 40.
* New material characterisation functions: Dubinin-Radushkevich
  (dr_plot) and Dubinin-Astakov (da_plot) plots.
* Added a new way to create an isotherm, from an two arrays of pressure
  and loading (the old DataFrame method is still valid but changed:
  check breaking changes).
* Made adsorbates searchable by a list of aliases rather than a single name.
* Exposed the CoolProp backend on adsorbate objects for convenience, it is
  accessible through the adsorbate.backend property.
* Streamlined the internal database functions.
* Updated NIST json import to new format.
  Cannot import multicomponent isotherms.
* Functions which generate matplotlib graphs now can take an Ax as parameter
  (similar to behaviour of pandas) to plot on existing figures.
* Changed behaviour of ModelIsotherm.guess function to accept a list of
  models to attempt to guess for.
* Added b-spline smoothing to output of dft fitting.

Breaking changes:

* The Sample class is now renamed as Material.
* Isotherm creation parameters have changed from 'sample_name', 'sample_batch'
  and 't_exp' to 'material_name', 'material_batch' and 't_iso'.
* Backend database has been simplified. Many required fields are no longer
  present and left to the discretion of the user.
* Several database functions have been renamed.
  All functions switched: 'sample' -> 'material' and 'experiment' -> 'isotherm'.
* When passing a DataFrame for isotherm creation, it now has to be specified as
  the parameter 'isotherm_data'.
* Isotherm unique ID is now generated on the fly (previously generated at
  each isotherm modification). It also now takes into account only the
  required parameters for each isotherm ( 'sample_name', 'sample_batch',
  't_exp' and 'adsorbate') as well as the model name, if the
  isotherm is a ModelIsotherm.
* Renamed Adsorbate.from_list() method to Adsorbate.find()

Bugfixes:

* Fixed issue in CSV import which read all values as strings (instead of floats/bools)
* Fixed an issue with Excel import of bools, as they were previously read as 1/0
* Fixed a bug where the automatic branch detection was not working when the
  DataFrame passed had a non-standard index.
* Fixed not being able to call _repr_ on an isotherm.


1.4.0 (2018-11-10)
------------------

New features:

* Added the GAB isotherm model

Bugfixes:

* Improved pore size distribution calculations to display cumulative pore
  volume when called.
* Fixed the "all-nol" selection parameter for legend display in isotherm
  graphs.

1.3.0 (2018-08-13)
------------------

New features:

* Added an excel import which can take Micromeritics or
  Belsorp report (.xls) files. Micromeritics code was
  taken from the `official python repo <https://github.com/Micromeritics/micromeritics>`_.
* Added an import option which can read and import Belsorp
  data (.DAT) files.
* Improved plotting functions to allow for more customisation
  over how the graph looks.
* The extra arguments to print_info() are now passed to the plotting
  function allowing for styles such as :issue:`8`.

Breaking changes:

* The unique isotherm ID is now generated only on a small subset of
  properties instead of all isotherm properties.
* The isotherm 'other_properties' subdictionary has been removed.
  Instead, all isotherm properties are now direct members of the
  class.
* When plotting, isotherm branches are now defined as 'ads', 'des'
  'all' (both branches) and 'all-nol' (both branches without
  legend entry) instead of a list of branches.
* Plot types are now universal. Any property can be plotted
  against any other property by specifying the x_data,
  y1_data and y2_data.

Bugfixes:

* Fixed 'source' not being recognised as an isotherm field
* Re-worked plot_iso color selection to avoid errors (:issue:`10`)
* Re-worked plot_isp legend placement to ensure no overlap
* Added correct common name for ethylene, propylene, methanol
  and ethanol in the database
* Renamed some model parameters for consistency
* A lot of typo fixes


1.2.0 (2018-02-19)
------------------

New features:

* The plotting legend now works with any isotherm attribute specified
* Changed model parent class to print out model name when displayed
* Added Toth and Jensen-Seaton models to the IAST calculation
  (spreading pressure is computed
  numerically using scipy.integrate.quad, :issue:`7`)

Bugfixes:

* Fixed an issue where the returned IAST selectivity v pressure
  data would not include all pressures
* Changed sqlite retrieval order to improve performance (:issue:`2`)
* Fixed an error where IAST vle data was plotted opposite to the graph axes
* Fixed a mistake in the Jensen-Seaton equation
* Fixed a mistake in the FH-VST equation

1.1.1 (2018-02-11)
------------------

New features:

* Allowed for branch selection for isosteric heat and fixed
  an error where this was an issue (:issue:`3`)

Bugfixes:

* Fixed an issue when plotting isotherms with and without
  secondary data simultaneously
* Fixed error with magnitude of polarizability of adsorbate
  from database in microporous PSD


1.1.0 (2018-01-24)
------------------

* Automatic travis deployment to PyPI
* Improved enthalpy modelling for initial enthalpy determination
* Improved documentation

1.0.1 (2018-01-08)
------------------

* Fixed wrong value of polarizability for nitrogen in database
* Added a check for initial enthalpy when the isotherm is measured
  in supercritical mode

1.0.0 (2018-01-01)
------------------

* Improved unit management by adding a unit/basis for both the
  adsorbent (ex: amount adsorbed per g, kg or cm3 of material
  are all valid) and loading (ex: mmol, g, kg of gas adsorbed
  per amount of material are all valid)
* Separated isotherm models so that they can now be easily
  created by the used.
* Added new isotherm models: Toth, Jensen-Seaton, W-VST, FH-VST.
* Made creation of classes (Adsorbate/Sample/Isotherms) more
  intuitive.
* Many small fixes and improvements

0.9.3 (2017-10-24)
------------------

* Added unit_adsorbate and basis_loading as parameters for an isotherm,
  although they currently do not have any influence on data processing

0.9.2 (2017-10-24)
------------------

* Slightly changed json format for efficiency

0.9.1 (2017-10-23)
------------------

* Better examples
* Small fixes and improvements

0.9.0 (2017-10-20)
------------------

* Code is now in mostly working state.
* Manual and reference are built.


0.1.0 (2017-07-27)
------------------

* First release on PyPI.
