# Documentation review

The findings below record the baseline at `bd71495`; cited line numbers refer
to that revision and may have moved. See the remediation summary at the end
for the implemented changes and their validation.

## Scope and evidence

Reviewed `develop` at `bd71495` on 2026-11-01. The review inventoried the
documentation sources and all 16 example notebooks, and examined the manual,
reference entry points, contributor guidance, Sphinx configuration, Read the
Docs configuration, and documentation CI. Affected Python docstrings and APIs
were checked against their implementations. This is not a verification of every
scientific formula or every generated API docstring.

Checks used Windows, Python 3.14.3, the frozen `docs` dependency group, Sphinx
9.1.0, nbsphinx 0.9.8, Matplotlib 3.10.8, and Pandoc 3.9:

- The CI-style doctest build exited successfully with **0 tests** and two
  warnings. The HTML build exited successfully with 15 warnings. Rebuilding
  HTML with `-W` exited 1. Builds used `-j 2`, rather than CI's `-j auto`, and
  wrote to temporary directories.
- All notebooks were executed with fresh kernels and copied example files.
  Their default database was redirected to a separate copy for each notebook.
  Three stopped with cell exceptions; two others completed but emitted error
  output. Execution used nbclient 0.10.4 with a 90-second cell timeout,
  `allow_errors=False`, and `MPLBACKEND=Agg`; saved outputs were cleared in
  memory. This does not establish that they work on the entire CI matrix.
- The documented CLI conversion completed successfully on an example JSON
  isotherm and produced the requested pressure and loading units.
- Link checking exited 1 on a Stack Overflow HTTP 403. That may be bot
  blocking, not a dead link; no dead-link claim is made from this result.
  The hosted Read the Docs and Binder builds were not run.

For the Sphinx doctest and HTML checks, the following PowerShell commands
reproduce the setup after replacing both paths with disposable locations and
installing Pandoc:

```powershell
$env:UV_PROJECT_ENVIRONMENT = 'C:\path\to\disposable-venv'
$env:MPLBACKEND = 'Agg'
$build = 'C:\path\to\build-output'
uv sync --frozen --no-default-groups --group docs --python 3.14
uv run --no-sync sphinx-build -E -j 2 -b doctest docs "$build\doctest"
uv run --no-sync sphinx-build -E -j 2 -b html docs "$build\html"
uv run --no-sync sphinx-build -E -j 2 -W -b html docs "$build\strict-html"
```

Do not execute the notebooks against original files or the bundled database
until D1 and D3 are addressed.

Priorities below are assessments of documentation impact: **P1** indicates a
data-safety or scientific-interpretation risk, or a major validation gap;
**P2** indicates a broken workflow or significant missing guidance; **P3**
indicates a narrower infrastructure issue.

## Data safety and scientific correctness

### D1 - The database tutorial can overwrite user data, and "permanent" storage is misleading (P1)

The [material](../manual/material.rst#L136) and
[adsorbate](../manual/adsorbate.rst#L197) manuals recommend the internal
database for permanent storage. The
[database notebook](../examples/database.ipynb#L330) overwrites and then deletes
a material using the default database; running cells against an existing
same-named material can destroy its contents. The default database is a
[packaged resource](../../src/pygaps/data/__init__.py#L20), not a user-owned
data directory. It may be read-only, replaced on reinstall or upgrade, or
temporary for some resource loaders.

Use a user-owned database copy from the **start** of the tutorial, including
every write and delete. Explain its backup and lifecycle, and qualify claims
that changes to the bundled database are permanent.

### D2 - Database path guidance is wrong, and a positional path can target the wrong database (P1)

The [database manual](../manual/sqlitedb.rst#L50) says every database function
takes its path as the first argument and locates the bundled database under
`pygaps/database`. Write functions actually take the object first, and the
resource is `pygaps.data/default.db`. More seriously, the
[connection decorator](../../src/pygaps/parsing/sqlite.py#L29) selects
`db_path` only from keyword arguments.

In an isolated test with two database copies,
`material_to_db(material, external_path)` inserted into the default copy,
whereas `material_to_db(material, db_path=external_path)` inserted into the
external copy. Document the keyword form explicitly and separately fix or
restrict the positional API so it cannot silently write to another database.

### D3 - The parsing notebook exports over its input files (P1)

The [AIF](../examples/parsing.ipynb#L143),
[JSON](../examples/parsing.ipynb#L214),
[Excel](../examples/parsing.ipynb#L309), and
[CSV](../examples/parsing.ipynb#L378) examples pass each source path back to
the corresponding export function. Once these cells are reached, the original
inputs are overwritten. A copied AIF fixture changed its SHA-256 after the
documented import/export sequence, including metadata and formatting changes.

Write round-trip examples to a separate temporary or explicitly named output
directory, and warn before replacing existing data. The earlier failure in D11
currently prevents a clean top-to-bottom run from reaching these cells.

### D4 - The isotherm manual confuses critical and saturation pressure, and adsorbent and adsorbate density (P1)

The [relative-pressure explanation](../manual/isotherm.rst#L482) says the
critical pressure at the experiment temperature is required. Relative pressure
uses the **saturation pressure at that temperature**, as the
[implementation](../../src/pygaps/units/converter_mode.py#L113) and the
[units manual](../manual/units.rst#L39) describe. For nitrogen at 77 K, the
review environment gave approximately 0.972 bar saturation pressure versus
33.96 bar critical pressure; they are not interchangeable.

The same page's [loading-basis explanation](../manual/isotherm.rst#L507)
calls for the density of the *adsorbent*. The loading converter uses the
[adsorbate's gas or liquid density](../../src/pygaps/units/converter_mode.py#L238);
material-basis conversion is the separate case requiring material properties.
Correct both explanations and distinguish loading and material bases.

### D5 - The Whittaker reference gives an incorrect single-site Langmuir expression (P1)

The [Whittaker docstring](../../src/pygaps/characterisation/enth_sorp_whittaker.py#L99)
states that the Langmuir adsorption potential reduces to
`RT ln(P0 / K)`. Its preceding general expression reduces instead to
`RT ln(P0 * K)` for one site. This also agrees with
[Langmuir's correction](../../src/pygaps/modelling/langmuir.py#L157) and the
[implemented potential](../../src/pygaps/characterisation/enth_sorp_whittaker.py#L351).
For `K=1e-5 Pa^-1`, `P0=1e5 Pa`, and `RT=1`, the implementation returns 0;
the documented quotient gives `ln(1e10)` and is not dimensionless.

Correct the rendered derivation and check the multi-site statement separately;
this finding establishes the single-site inconsistency, not a full theory audit.

### D6 - Initial-enthalpy input units are off by a factor of 1,000 (P1)

The public [initial-enthalpy docstring](../../src/pygaps/characterisation/enth_sorp_initial.py#L43)
says the input is in `kJ/mmol`. The routine compares its numeric input directly
with [liquefaction enthalpy](../../src/pygaps/characterisation/enth_sorp_initial.py#L181),
which the [adsorbate API](../../src/pygaps/core/adsorbate.py#L882) returns in
`kJ/mol`; the [graph label](../../src/pygaps/graphing/labels.py#L37) also uses
`kJ/mol`. No enthalpy-unit conversion is applied to the input column.

Clarify the expected input and output units and verify the fitting bounds in
those units. Following the existing `kJ/mmol` instruction changes the numeric
scale by 1,000 relative to `kJ/mol`.

### D7 - Isotherm IDs are not exact uniqueness checks (P1)

The [uniqueness section](../manual/isotherm.rst#L555) presents `iso_id` and
equality as identifying the isotherm's data without mentioning that point data
is [rounded to eight decimal places before hashing](../../src/pygaps/utilities/hashgen.py#L30).
Two otherwise identical point isotherms with first loadings `1.0` and
`1.000000001` produced the same ID and compared equal. The ID is also used for
database storage.

Document the precision and collision limitations, and separately decide whether
the identity policy is appropriate for database deduplication. Do not describe
the current comparison as exact data identity.

## Validation and executable examples

### D8 - Documentation CI succeeds without executing the examples (P1)

[CI](../../.github/workflows/CI.yaml#L41) runs Sphinx's doctest builder, but the
observed result is zero tests. The ordinary `code:: python` blocks are not
doctests. [nbsphinx](../conf.py#L18) uses its default automatic execution
policy; all 16 notebooks have saved execution counts or outputs, so this build
renders those outputs rather than rerunning the code. A saved
`CalculationError` is even present in the generated enthalpy page.

First make the examples safe for isolated execution (D1 and D3). Then add
meaningful doctests or example tests and execute notebooks on disposable data in
CI. Treat unexpected error outputs as failures, including errors caught and
printed by notebook cells; merely switching nbsphinx to always execute would
currently risk modifying real files or the bundled database.

### D9 - IAST examples import a removed module (P2)

All four snippets in the [IAST manual](../manual/iast.rst#L51) and the
[IAST notebook](../examples/iast.ipynb#L36) use `import pygaps.iast as pgi`.
Fresh execution raises `ModuleNotFoundError: No module named 'pygaps.iast'`.
The functions are exported from [pygaps.prediction](../../src/pygaps/prediction/__init__.py).

Update the import throughout the manual and notebook, refresh saved outputs,
and execute the actual mixture examples.

### D10 - The enthalpy notebook calls an obsolete API and publishes a traceback (P2)

The [enthalpy notebook](../examples/enthalpy_sorption.ipynb#L130) calls
`pygaps.characterisation.isosteric_enthalpy`, which no longer exists; fresh
execution stops with `AttributeError`. The current export is
`enthalpy_sorption_clapeyron` in
[characterisation/__init__.py](../../src/pygaps/characterisation/__init__.py).
The notebook also contains a saved Toth fitting `CalculationError` that appears
in the successful HTML build.

Update the calls and their result handling, then make the fitting examples
reproducible or clearly explain a deliberately demonstrated failure.

### D11 - The parsing notebook passes lists to `next()` (P2)

Four cells in the [parsing notebook](../examples/parsing.ipynb#L119) construct
`isotherms` as a list and then call `next(isotherms)`. The first fails with
`TypeError: 'list' object is not an iterator`; later JSON, Excel, and CSV cells
repeat the same pattern. Fix the list access and handle an empty input
collection, then address the destructive exports in D3 before rerunning it.

### D12 - Two notebooks complete while displaying failures (P2)

The [alpha-s example](../examples/alphas.ipynb#L60) catches and prints an
interpolation-range error for the supplied MCM-41 and SiO2 datasets instead of
producing the first demonstrated result. The
[plotting example](../examples/plotting.ipynb#L214) emits
`ValueError: At least one value in the dash list must be positive` when its
`linewidth=0` figure is rendered with Matplotlib 3.10.8. Saving that figure
directly reproduced the same error.

Use compatible overlapping data/ranges and a supported no-line style, or
explain intentional failures. Validate rendered outputs, not just notebook
process exit status.

### D13 - Several copied Python snippets are syntactically invalid or use the wrong converter arguments (P2)

The [ModelIsotherm constructor](../manual/isotherm.rst#L241) is missing commas
after `param_guess` and `param_bounds`; both calls in the
[modelling guide](../manual/modelling.rst#L90) omit the comma after
`branch='ads'`. Several [adsorbate](../manual/adsorbate.rst#L71) and
[material](../manual/material.rst#L78) Python blocks include output lines
beginning `>>`, which are not Python syntax.

The [low-level loading and material examples](../manual/units.rst#L221) pass
`mode_from`/`mode_to`, but those functions require `basis_from`/`basis_to`.
Correcting only those names still raises `AttributeError` because the
cross-basis examples omit the required adsorbate or material. Make the blocks
executable with explicit supporting objects, and use valid interactive prompts
or separate output from copyable code.

### D14 - Material property and list examples use the wrong API (P2)

The [material manual](../manual/material.rst#L88) presents `molar_mass` and
`density` as methods and calls `my_material.molar_mass()`. They are
[properties](../../src/pygaps/core/material.py#L134); the shown call raises
`TypeError: 'int' object is not callable` for the supplied example. The
[list example](../manual/material.rst#L122) uses `pyGAPS.MATERIAL_LIST`
instead of the imported lowercase `pygaps`, raising `NameError`.

Correct both examples and the reference roles so readers can copy them.

### D15 - The modelling guide reverses branch capabilities and supplies loading as pressure (P2)

The [overview](../manual/modelling.rst#L35) says the former, `ModelIsotherm`,
can contain both branches and the latter, `PointIsotherm`, contains one model
branch. The classes are reversed in that sentence.

The [comparison example](../manual/modelling.rst#L167) passes
`point_isotherm.loading()` as `x_points`, although `x_points` represents
pressure in the default plot. With pressures `[0.1, 0.2, 0.3, 0.4]` and
loadings `[1, 2, 3, 4]`, the documented call fails interpolation above the
pressure range. Even when it does not fail, it evaluates at the wrong
coordinates. Use the appropriate pressure points or the loading-specific
parameter.

### D16 - Passing a PointIsotherm as model evaluation points is not generally supported as claimed (P2)

The [modelling guide](../manual/modelling.rst#L190) says a `PointIsotherm` can
be supplied as `pressure_points` when converting a model to points. That works
in the native-loading branch, but the
[native-pressure branch](../../src/pygaps/core/pointisotherm.py#L285) passes
the object directly to the inverse calculation. A Virial model reproduces
`TypeError: float() argument must be a string or a real number, not
'PointIsotherm'`.

Qualify the documented contract or repair and test the implementation for
native-pressure models. Numerical inverse limitations also need their own
validation; simply replacing the object with an array is not a general fix.

### D17 - Enthalpy return and prediction contracts disagree (P2)

The rendered Clausius-Clapeyron reference
[documents `std_errors`](../../src/pygaps/characterisation/enth_sorp_clapeyron.py#L48),
but the [function returns `std_errs`](../../src/pygaps/characterisation/enth_sorp_clapeyron.py#L153).
The [prediction docstring](../../src/pygaps/prediction/enthalpy_to_isotherm.py#L48)
documents the keyword `temperature_predicted` and a dictionary containing
`loading` and `isosteric_enthalpy`. The actual keyword is
`temperature_prediction`, and the implementation requires
`loading` and `enthalpy_sorption`; the documented keyword raises `TypeError`
and the documented dictionary raises `ParameterError`.

In particular, the Clausius-Clapeyron result's `isosteric_enthalpy` key cannot
be passed directly as claimed. Align the public contract and docs, or provide a
tested adapter; correcting only a name in the prose does not resolve the
cross-function incompatibility.

### D18 - The reference omits or misclassifies public APIs (P2)

The [model registry](../../src/pygaps/modelling/__init__.py#L16) contains
`DSToth` and `ChemiPhysisorption`, neither of which appears in the
[model reference](../reference/fitting.rst); the
[manual's model list](../manual/modelling.rst#L46) also omits those models and
Virial. Public [enthalpy-based prediction functions](../../src/pygaps/prediction/__init__.py#L10)
and [initial-enthalpy functions](../../src/pygaps/characterisation/__init__.py#L13)
are absent from the corresponding reference pages.

The [apparatus reference](../reference/parsing.rst#L28) uses `automodule` on
the `isotherm_from_commercial` function. The generated section has prose but
no callable signature, and its
[docstring](../../src/pygaps/parsing/__init__.py#L37) lists only three
manufacturers although the manual and implementation include SMS DVS and
Quantachrome. Add the missing public entries and document the callable as a
function with the current options.

## Setup, build, and publication infrastructure

### D19 - Contributor setup does not enter the clone or select the development branch (P2)

[CONTRIBUTING](../../CONTRIBUTING.rst#L48) clones the fork but never changes
into it before `uv sync --all-groups`; from the original directory uv cannot
find the project's `pyproject.toml`. The
[README](../../README.rst#L185) and
[installation page](../installation.rst#L26) say their clone commands install
the development branch, but the repository's recorded default branch is
`master`, and neither command selects `develop`.

Add the directory change and explicit branch selection. Also include the
actual local Sphinx build command and Pandoc prerequisite together. The
contributor instruction to [run all tests](../../CONTRIBUTING.rst#L76) should
explain that [pytest defaults](../../pyproject.toml#L168) exclude `network`
tests and how to opt into them.

### D20 - Existing Sphinx warnings are not a build gate (P2)

The standard HTML build returns success with 15 warnings, including an
unresolved `isosteric_enthalpy_raw` reference, unresolved `t.Callable` and
pandas type references, and unreferenced footnotes. Adding `-W` reproduced
exit status 1. [CI](../../.github/workflows/CI.yaml#L43) does not treat warnings
as errors, so reference regressions can be published unnoticed.

Fix or deliberately configure the known warnings before enforcing a
warning-clean build. External link checking is explicitly
[non-blocking](../../.github/workflows/CI.yaml#L46); its observed HTTP 403 may
be transient or bot-related and should not be classified as a broken link
without independent confirmation.

### D21 - Read the Docs and CI install different dependency groups (P2)

[Read the Docs](../../.readthedocs.yaml#L17) selects the `docs` group using
`uv sync`; the [documented Read the Docs behavior](https://docs.readthedocs.com/platform/stable/config-file/v2.html)
corresponds to `uv sync --group docs`, which also includes uv's default `dev`
group. That group includes tests, docs, Ruff, and Pylint in
[pyproject.toml](../../pyproject.toml#L58). CI instead uses
`--no-default-groups --group docs --frozen`.

On the reviewed Windows interpreter, the former dry run selected 106 packages
including pytest, Ruff, and Pylint, versus 94 in the CI-like environment. This
is a reproducibility and maintenance difference, not a reproduced hosted-build
failure. Align the intended groups and lock policy, or document why they
differ.

### D22 - Notebook source links point at the wrong branch and the nbviewer link fails in the browser (P2)

[Sphinx configuration](../conf.py#L51) assigns `master` to every development
release's `release_ref`. The built `4.6.2.dev52` pages consequently link their
source and Binder launch to `master`, not the reviewed `develop` content. This
is not merely theoretical: the parsing notebook differs between those branches
in its Excel extensions and fixtures.

The same [notebook prolog](../conf.py#L167) calls jQuery's `$` without loading
jQuery. Serving the generated page produced `ReferenceError: $ is not defined`
and no nbviewer link in the browser. Resolve source/Binder links to the
actual documentation revision and replace the jQuery dependency or load it
explicitly.

### D23 - Malformed math directives produce broken scientific reference text (P2)

The [Whittaker docstring](../../src/pygaps/characterisation/enth_sorp_whittaker.py#L95)
uses `..math::` rather than `.. math::`; the successful HTML build displays
`..math::` as a definition-list term and drops the TeX backslashes from the
pseudo-saturation formula. Other affected directives occur in that module and
the [prediction module](../../src/pygaps/prediction/enthalpy_to_isotherm.py#L34).
The general Toth expression in
[Langmuir's docstring](../../src/pygaps/modelling/langmuir.py#L160) also has a
malformed `\frac` expression.

Correct the directives and TeX, then inspect the rendered equations as well as
the Sphinx exit code.

### D24 - The optional spelling build cannot use the declared docs environment (P3)

Setting `SPELLCHECK` makes [conf.py](../conf.py#L33) load
`sphinxcontrib.spelling`, but that extension is absent from the declared
[docs dependencies](../../pyproject.toml#L47). With the frozen docs group,
`SPELLCHECK=1` caused Sphinx to exit 2 with `No module named
'sphinxcontrib.spelling'`. Either provide and document a separate spelling
environment, including its system dictionary requirements, or remove the
unsupported switch.

## Suggested order

1. Make database and parsing examples non-destructive; correct the scientific
   pressure, enthalpy, and identity guidance.
2. Repair the failing examples and API contracts, then add isolated executable
   documentation checks.
3. Clean Sphinx warnings and align publication/setup paths, followed by
   reference completeness and optional tooling.

## Remediation summary

Implemented on `feature/docs-remediation`:

| Findings | Changes |
| --- | --- |
| D1-D3 | Database examples use disposable user-owned copies and explicit path keywords; parsing exports go to separate temporary destinations. SQLite connection routing now honors positional paths as well as keywords. |
| D4-D7 | Corrected saturation-pressure and density explanations, adsorption-potential equations, enthalpy units, and identity precision guarantees. Hashing and database identity behavior are unchanged. |
| D9-D15 | Repaired obsolete imports/calls, list access, plotting and interpolation examples, executable snippets, material properties, and modelling guidance. Refreshed outputs in the six affected notebooks. |
| D16-D17 | Normalized isotherm-based evaluation coordinates for both model directions, including vectorized Virial inversion. Prediction accepts Clausius-Clapeyron results and the existing enthalpy key, converts native loading units, preserves branch selection, and rejects conflicting enthalpy aliases. |
| D18-D19 | Completed model/enthalpy/prediction references and callable signatures; corrected clone/branch instructions and documented build, notebook, network-test, and optional spelling commands. |
| D8, D20-D24 | Added dedicated isolated notebook CI, meaningful doctests, warning-as-error builds, consistent frozen docs-only installs, revision-pinned notebook links, a static nbviewer link, valid rendered mathematics, and an optional spelling dependency group. |

Validation after implementation:

- **578 focused runtime tests passed**, with one network test deselected.
  The existing BET/GAB zero-loading numerical warnings remain.
- **19 documentation tests passed**: all 16 notebooks executed in fresh
  kernels, plus three build-configuration checks. Tests validate saved and
  freshly generated output, reject error outputs and printed tracebacks,
  render outstanding figures, and verify that example inputs, source files,
  and the packaged database retain their hashes.
- A new frozen **docs-only environment** installed 94 packages. Both the
  doctest and HTML builders passed with `-W`; **two doctests passed** and
  the builds emitted no warnings.
- Browser checks found no JavaScript errors on the IAST page and confirmed
  revision-pinned source, Binder, and nbviewer links. The fitting reference
  rendered 158 equations and the enthalpy reference 33, without MathJax
  error nodes or literal malformed math directives.
- Repository Ruff checks and `git diff --check` passed.
- The optional spelling builder runs successfully with the separate group
  and the `en_GB` dictionary. It still reports spelling candidates; a
  scientific-word dictionary/editorial cleanup is not part of this change.

Hosted Read the Docs and Binder builds were not executed locally. External
link checking remains non-blocking because remote services can reject bots;
the original HTTP 403 observation is not reclassified as a dead link.
