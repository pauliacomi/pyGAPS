# Core classes: functionality and code assessment

Reviewed 2026-11-02 at `develop` / `a13aa10`. This is an assessment, not an
implementation plan or approval to change scientific behavior.

## Current status: outstanding items

Updated 2026-11-02 on `feature/core-updates`, including the C12 ownership fix.
**14 findings are resolved, 7 core findings remain open,
C10/C18/C19 are transferred to parsing, and C14 is deferred to fitting work.**
The detailed findings retain the original
evidence; resolved findings have resolution notes rather than describing
current defects.

| Priority | Finding | Outstanding work |
|---|---|---|
| High, transferred | [C10](parsing.md#c10-json-and-sqlite-round-trips-can-change-branch-assignments) | Preserve explicit branches in JSON and SQLite; tracked in the parsing review, not this core implementation queue. |
| High | [C11](#c11-distinct-measurements-can-have-the-same-isotherm-identity) | Define lossless record/content identity and a versioned ID migration policy. |
| Medium, deferred | [C14](#c14-model-selection-compares-different-residual-definitions) | Define a common selection objective; tracked in [fitting action points](fitting.md#action-points), not this core implementation queue. |
| Medium, transferred | [C18](parsing.md#c18-json-does-not-round-trip-all-valid-point-isotherm-coordinates) | Preserve coordinate keys and decide index persistence/identity semantics; tracked in the parsing review. |
| Medium, transferred | [C19](parsing.md#c19-database-autoinsert-checks-the-in-memory-registry-not-the-target-db) | Check referenced records in the target database and insert transactionally; tracked in the parsing review. |
| Medium | [C20](#c20-equality-and-hashing-violate-pythons-container-expectations) | Separate alias lookup from equality and choose a safe mutable-object hashing contract. |
| Medium | [C21](#c21-validation-depends-on-construction-path-and-misses-invalid-units) | Apply branch/unit validation consistently across constructors and factories. |
| Medium | [C22](#c22-thermodynamic-fallback-catches-control-flow-and-programming-errors) | Narrow backend exception handling and preserve original failure context. |
| Medium | [C23](#c23-the-documented-vaporisation-property-alias-is-not-read) | Define stored alias precedence/sign convention and diagnose conflicts. |
| Low | [C24](#c24-factory-methods-lose-subclasses-and-leak-a-control-option-into-metadata) | Preserve factory subclasses and keep control options out of metadata. |
| Low | [C25](#c25-type-contracts-and-data-quality-policies-need-clarification) | Correct type contracts and define storage/calculation data-quality policies. |

**Resolved:** C1-C9, C12-C13, C15-C17. Changes cover fractional conversions,
spreading pressure, IAST branches, saturation-pressure units, fitting options,
conversion atomicity/no-ops, data/backend caches, input defaults, pseudo-pressure
selection, inclusive limits, and independent dictionary-supplied materials.

**Validation:** including C12, the implementation passed the full suite with
**1,236 passed, 20 deselected** (two existing BET/GAB warnings).
Ruff and whitespace checks also passed. REFPROP remains
unavailable locally; its backend forwarding is covered by stubs.

## Scope and evidence

The review covers `BaseIsotherm`, `PointIsotherm`, `ModelIsotherm`, `Material`
and `Adsorbate`. It also traces their public conversion, fitting, serialization,
database and IAST paths where needed to establish an effect. It is not a full
review of every model equation, parser, unit converter or prediction algorithm.
The earlier [test-suite review](done/testing.md) provides additional context.

The existing core tests passed: **210 passed** on Windows, Python 3.14.3,
NumPy 2.4.3, pandas 3.0.1, SciPy 1.17.1 and CoolProp 7.2.0. A separate
`coverage run --branch --source=src\pygaps\core -m pytest tests\core -q`,
followed by combining its temporary parallel data, reported **85.0% combined
statement/branch coverage** for the core package. This is coverage from
`tests\core` only, not a measure of correctness or whole-suite coverage.

Findings below were checked with small, isolated runtime examples unless marked
otherwise. Database examples used disposable copies of the packaged database;
no production data were changed. For the failed fractional conversion, a
debugger also confirmed that the data had already changed while the old units
were still recorded. A mocked backend failure was used where explicitly noted;
an actual REFPROP installation was not tested. No source fixes or new
regression tests were made during the original assessment; subsequent fixes
and their validation are recorded above and in the resolution notes.

High means a demonstrated path can silently change scientific results, lose
data identity, or leave misleading state. Medium generally means a narrower
contract failure or a substantial design risk; Low means maintainability or
extensibility. Priority is relative to this review, not a security rating.

## Overall assessment

The separation between shared isotherm metadata, measured points, fitted models,
and material/adsorbate properties is useful. The core suite exercises basic
conversions, branching, fitting and thermodynamic properties, and includes
quantitative model-fit checks and non-default DataFrame indices. A desorption
model converted to points retained its branch in the probe.

The main weakness is that equivalent operations do not consistently share the
same invariants. Conversion logic is repeated across point and model classes;
mutable DataFrames and registries coexist with caches and content-derived
identity; and serialization does not always preserve branch or coordinate
metadata. Several normal-looking calls consequently return plausible but
incorrect numbers. Passing tests do not cover the combinations that expose
these defects.

## High-priority findings

### C1. Fractional loading conversions disagree across access paths

**Evidence.** Use an adsorbent density of 2 g/cm3 and an adsorbate molar
density of 0.05 mol/cm3, consistent with a molar mass of 10 g/mol and liquid
density of 0.5 g/cm3. For a point isotherm with 2 mmol/g at 2 bar,
`loading(loading_basis='fraction', material_basis='volume',
material_unit='cm3')` returns **0.08** at that point, as expected.
`loading_at(2, ...)` returns **0.04** for the same requested output. A Henry
model's `loading_at` returns 0.08.

In the reverse direction, passing the corresponding volume fraction 0.04 at
1 bar to `PointIsotherm.pressure_at` returns **2 bar**, whereas the model
returns **1 bar**. That probe specified `loading_basis='fraction'`,
`loading_unit='cm3'`, `material_basis='volume'` and `material_unit='cm3'`;
the current API requires that nominal loading unit for this dimensionless
input. Separately, starting from a 0.01 mass fraction,
both point and model `loading_at(..., material_basis='volume',
material_unit='cm3')` return about **0.02**, while the correct volume fraction
is **0.04**. The in-place `convert_material` gives 0.04 in this example.

The point interpolator passes the original material basis to loading conversion
after converting the material; the read-only paths also lack the simultaneous
numerator conversion used by the in-place fractional conversion.

**Suggested correction.** Centralize conversion of the numerator and
denominator, explicitly tracking source and target basis/unit. Use it for point
and model reads, interpolation in both directions, and in-place conversion.
Add independent mass/molar/volume fraction oracles, round trips, and parity
tests at measured points, including a non-unit adsorbate density.

**Resolution (feature/core-updates).** Added a shared loading/material
conversion path and used it for point and model reads, interpolation, and
in-place point conversions. Regression tests now cover mass-fraction to
volume-fraction conversion, fraction/percent conversion, reverse pressure
lookup, and point/model parity.

**Sources:** [point read conversion](../../src/pygaps/core/pointisotherm.py#L820),
[point inverse conversion](../../src/pygaps/core/pointisotherm.py#L1023),
[point interpolated loading](../../src/pygaps/core/pointisotherm.py#L1174),
[in-place fractional conversion](../../src/pygaps/core/pointisotherm.py#L570),
[model loading conversion](../../src/pygaps/core/modelisotherm.py#L958).

### C2. Point spreading pressure depends on point order and fails at the origin

**Evidence.** For the same desorption data, pressures `[3, 2, 1]`, loadings
`[9, 4, 1]`, and target pressure 2.5, the method returns **7.59392934**.
Reversing the paired data to ascending pressure returns **3.77484433**, which
also agrees with an independent piecewise-linear integral:
`1 + (3 - 2*log(2)) + (2.5 - 6*log(2.5/2))`. Desorption data are naturally
often recorded in descending order. With pressure/loading `[0, 1, 2]` /
`[0, 1, 4]`, the result at 1.5 is `nan` with divide-by-zero warnings.

The algorithm counts all values below the target but then treats that count as
an ascending prefix; it also divides by the first pressure and takes a log of
pressure ratios without handling zero.

**Suggested correction.** Sort paired branch data locally, define handling of
duplicate/nonfinite pressures, and handle a valid zero origin without dividing
by it. Explicitly reject a nonzero uptake at zero pressure if the chosen
integral would diverge. Test ascending/descending equivalence, the origin,
exact boundaries and both extrapolation policies against an independent
integral. Do not silently sort the stored experimental data.

**Resolution (feature/core-updates).** Integration now sorts paired branch
data locally, accepts a zero-loading origin, and rejects duplicate/nonfinite
pressures, negative pressures, nonfinite loadings, and a divergent nonzero
loading at zero pressure. Henry-law integration below the first positive point
is independent of the interpolation cache. Above the highest pressure, the
current call must explicitly request constant fill or linear extrapolation.
Regression tests cover order invariance without stored-data mutation, the
origin, exact boundaries, fill policies, unit conversion, and invalid inputs.

**Source:** [point spreading-pressure integration](../../src/pygaps/core/pointisotherm.py#L1308).

### C3. IAST can mix adsorption and desorption branches

**Evidence.** The IAST solver forwards `branch` to spreading pressure, but not
to the point-isotherm `loading_at` calls used for its initial guess and final
loading. For two synthetic isotherms with adsorption `q=10p` at pressures
`[0.5, 1, 2]`, desorption `q=p` at `[2, 1, 0.5]`, and partial pressures
`[0.5, 0.5]`, `iast_point(..., branch='des')`
returns **`[5, 5]`** instead of the equal-Henry result **`[0.5, 0.5]`**.
With desorption-only point isotherms it raises a SciPy `ValueError` while
trying to interpolate the empty adsorption branch.

**Suggested correction.** Forward the requested branch to every loading
evaluation in forward and reverse IAST. Add a mixed-branch numerical oracle and
desorption-only regressions; also cover the spreading-pressure corrections in
C2/C13. This is a downstream consumer defect, not solely a core-class defect.

**Resolution (feature/core-updates).** Forward and reverse IAST now pass the
requested branch to every loading evaluation, including the default forward
initial guess. Henry-law oracle tests cover mixed branches, desorption-only
points in descending order with a zero origin, and desorption models, with
default and explicit solver guesses. Reverse results also round-trip through
the gas-fraction wrapper.

**Sources:** [forward initial guess](../../src/pygaps/prediction/iast.py#L378),
[forward loading](../../src/pygaps/prediction/iast.py#L428),
[reverse loading](../../src/pygaps/prediction/iast.py#L626).

### C4. Requested saturation-pressure units can be wrong by 100,000

**Evidence.** With `ads = Adsorbate('custom', saturation_pressure=101325)`,
`ads.saturation_pressure(77, unit='bar', calculate=False)` returns **101325**,
not **1.01325**. The stored-value path ignores `unit`. The subcritical path of
`saturation_pressure_pseudo_dubinin(77, unit='bar')` also drops the unit:
for nitrogen the probe returned **97152.27** instead of **0.9715227 bar**.

**Suggested correction.** Define and document the units of stored values and
convert once at the common output boundary, including the fallback and
subcritical paths. Avoid introducing a double conversion in the existing
backend-failure fallback. Test Pa/bar and another unit for calculated, stored,
fallback and pseudo-helper paths.

**Resolution (feature/core-updates).** Stored saturation pressures are
documented as Pa and now share the calculated path's output conversion.
Backend fallback retrieves Pa to avoid double conversion, and the subcritical
Dubinin helper forwards the requested unit. Deterministic tests cover default
Pa, explicit Pa, bar, and kPa for calculated, stored, fallback, alias, and
subcritical/critical/supercritical pseudo-helper paths.

**Sources:** [stored saturation pressure](../../src/pygaps/core/adsorbate.py#L565),
[subcritical pseudo helper](../../src/pygaps/core/adsorbate.py#L609).

### C5. Model-selection fitting silently discards parameter bounds

**Evidence.** Fitting `q=2p` with
`from_pointisotherm(..., model=['Henry'], param_bounds={'K': [0.1, 0.2]})`
returns `K=2.0` and default bounds `(0, inf)`. The equivalent single-model
call honors the supplied bound and returns approximately `K=0.2`. The
multi-model route also does not forward `param_guess`.

Passing only `{'K': [0.1, 10]}` as bounds to a Langmuir fit raises
`KeyError: 'n_m'`: supplied bounds replace rather than augment defaults. The
direct `guess` path has the same partial-bounds problem and can abort before
trying other candidates.

**Suggested correction.** Forward and validate supported options consistently
for a model list; define how per-model starting guesses are supplied. Merge
partial overrides with each model's default bounds, reject unknown parameters
appropriately, and test the public `model_iso` wrapper as well as direct and
list fitting. Include a fit where the bound changes the result.

**Resolution (feature/core-updates).** Model selection now forwards bounds
and starting guesses, applying flat parameter-name overrides to matching
candidates and rejecting names unknown to all candidates. Partial bounds
retain model defaults, and partial guesses retain automatic values for missing
parameters. Regression tests cover direct construction, point conversion,
explicit/default candidate selection, and the public wrapper, including a
Henry fit constrained from K=2 to K=0.2.

**Sources:** [point-to-model dispatch](../../src/pygaps/core/modelisotherm.py#L325),
[candidate bounds](../../src/pygaps/core/modelisotherm.py#L419),
[model bounds initialization](../../src/pygaps/modelling/base_model.py#L52).

### C6. No-op in-place conversions erase valid unit metadata

**Evidence.** On an absolute bar / mmol per g point isotherm, each of
`convert_pressure(mode_to='absolute')`, `convert_loading(basis_to='molar')`
and `convert_material(basis_to='mass')` leaves the numeric values unchanged but
sets the corresponding unit to `None`. Reconstructing a point isotherm from
the result then raises `ParameterError` because the stored units are invalid.
The convenience `convert` method reaches the same paths.

**Suggested correction.** Resolve omitted destination units to the current
unit when the basis/mode does not change, validate the complete destination
state before mutation, and preserve the no-op state exactly. Test all three
methods and `convert`, including serialization/reconstruction afterward.

**Resolution (feature/core-updates).** Conversion methods now resolve omitted
units before their no-op checks, preserving numeric data, metadata, and cached
interpolators. This includes fractional material bases, whose units are only
relabelled when explicitly requested and valid. Parameterized regressions cover
omitted/basis-only/unit-only/explicit calls through each conversion method and
the convenience method, for physical, fractional, percentage, and relative
representations, followed by reconstruction and JSON round trips.

**Sources:** [pressure metadata update](../../src/pygaps/core/pointisotherm.py#L428),
[loading metadata update](../../src/pygaps/core/pointisotherm.py#L491),
[material metadata update](../../src/pygaps/core/pointisotherm.py#L552).

### C7. A failed fractional conversion leaves partially converted data

**Evidence.** For mass fractions `[0.01, 0.02, 0.03]`, a material density of
2 g/cm3 and an adsorbate without liquid density, converting the material basis
to volume raises `CalculationError`. The data are nevertheless
`[0.02, 0.04, 0.06]`, while the object still says `material_basis='mass'`,
`material_unit='g'`. At the second conversion step the debugger observed
exactly this intermediate state. Existing interpolators are not reset because
the exception occurs before the reset.

**Suggested correction.** Compute all components into temporary values, then
commit data, units and cache invalidation together only after every step
succeeds. Test missing-property and invalid-unit failures after the first
stage, comparing data, metadata and cached results before and after.

**Resolution (feature/core-updates).** C1's shared conversion path already
removed the intermediate assignment: loading/material conversion finishes
before stored data, metadata, or caches change. Dedicated regressions now
verify missing-density and invalid-unit failures after successful conversion
to molar loading, for fractions and percentages with and without cached
interpolators. They check unchanged data, metadata, cache identities, and
subsequent interpolation results. Successful conversions also verify that both
caches are reset and rebuilt with the converted values.

**Source:** [two-stage material conversion](../../src/pygaps/core/pointisotherm.py#L570).

### C8. Direct data edits leave interpolation caches stale

**Evidence.** With pressure/loading `[0, 1, 2]`, `loading_at(1.5)` is 1.5.
After `iso.data().loc[2, 'loading'] = 20`, `loading()` shows `[0, 1, 20]`
but `loading_at(1.5)` still returns **1.5**, rather than **10.5**. The public
API exposes the underlying DataFrame, while the cache key only checks branch,
interpolation kind and fill.

**Suggested correction.** Establish an explicit mutation contract: for
example, use managed updates/versioning, or return copies and provide
cache-invalidating setters with a compatibility path for `data_raw`. Reset
both interpolators whenever data affecting them change. Test edits to pressure,
loading and branch after both caches are built.

**Resolution (feature/core-updates).** ``data()`` now returns independent
copies. ``update_data(frame)`` replaces the complete dataset after validating
required/unique columns and explicit branch values, and resets both caches.
``data_raw`` remains supported without deprecation; callers editing it directly
must invoke ``reset_interpolators()`` afterward. Regressions cover pressure,
loading, and branch edits through both paths and invalid updates.

**Sources:** [data access](../../src/pygaps/core/pointisotherm.py#L678),
[loading interpolator cache](../../src/pygaps/core/pointisotherm.py#L1140),
[pressure interpolator cache](../../src/pygaps/core/pointisotherm.py#L1009).

### C9. Thermodynamic backend caching can use the wrong fluid or backend

**Evidence.** After an adsorbate has cached a nitrogen state, changing
`properties['backend_name']` to oxygen leaves `molar_mass()` at **28.01348**;
a fresh oxygen state gives **31.9988**. In a separate probe, switching from
HEOS to REFPROP and mocking a failed REFPROP `AbstractState` construction
caused the first call to use the stored fallback. The next call returned the
old **HEOS** state while the selected mode remained **REFPROP**: the cache
mode was updated before state construction succeeded.

Additionally, `p_triple` and `compressibility` call `PropsSI` directly with
only the fluid name. A mock confirmed that no selected backend is passed on
these paths. Actual REFPROP results were not tested.

**Suggested correction.** Key the cache by both backend mode and fluid name,
construct a replacement successfully before committing it, and consistently
honor the selected backend in every thermodynamic method. Test name changes,
failed initialization/retry and backend switching with a stub; add a real
REFPROP integration test only where that backend is available.

**Resolution (feature/core-updates).** Backend states are keyed by both mode
and fluid name; replacement state construction succeeds before cache metadata
is committed. Triple pressure and compressibility explicitly qualify their
fluid names with the selected backend. Stub-based regressions cover fluid/mode
changes, repeated failed construction with fallback and subsequent retry, and
HEOS/REFPROP forwarding without requiring REFPROP installation.

**Sources:** [backend cache](../../src/pygaps/core/adsorbate.py#L220),
[triple pressure](../../src/pygaps/core/adsorbate.py#L365),
[compressibility](../../src/pygaps/core/adsorbate.py#L934).

### C10. JSON and SQLite round trips can change branch assignments

**Transferred, not resolved.** Evidence and action points now live in the
[parsing review](parsing.md#c10-json-and-sqlite-round-trips-can-change-branch-assignments).

### C11. Distinct measurements can have the same isotherm identity

**Evidence.** Two otherwise identical point isotherms with loadings
`[1.0, 2.0]` and `[1.0, 2.000000001]` have the same `iso_id` and compare
equal because data are rounded to eight decimal places before hashing. In a
disposable SQLite database, inserting the second after the first raises
`ParsingError` caused by the unique `isotherms.id` constraint. Small absolute
pressures/loadings are especially susceptible to fixed decimal rounding.

**Suggested correction.** Define whether identity means an immutable record
identifier or lossless scientific content, and keep approximate comparison
separate. If content hashes change, version the scheme and plan database
migration/compatibility rather than silently changing existing IDs. Test
sub-1e-8 differences and round trips.

**Sources:** [point data hash](../../src/pygaps/utilities/hashgen.py#L28),
[isotherm equality](../../src/pygaps/core/baseisotherm.py#L259),
[SQLite ID insertion](../../src/pygaps/parsing/sqlite.py#L826).

### C12. Constructing one isotherm can mutate another and the caller's input

**Evidence.** Register a material with density 2 and construct an isotherm
using it. Constructing a second isotherm with
`{'name': <same name>, 'density': 9}` removes `name` from the supplied
dictionary and updates the registered material in place. The first isotherm's
material density becomes **9** as well. This can change later conversions and
content-derived IDs in unrelated objects.

The registry sharing is deliberate in the current implementation, so a change
to ownership semantics needs a compatibility decision; mutating the caller's
dictionary is independently avoidable.

**Suggested correction.** Copy input mappings, and make registry updates
explicit rather than an implicit constructor side effect, or isolate
per-isotherm material properties. Document ownership and add tests with two
isotherms sharing a registered name, including conversion and ID stability.

**Source:** [material setter](../../src/pygaps/core/baseisotherm.py#L211).

**Resolution (feature/core-updates).** Dictionary inputs now create independent,
unregistered materials using registered defaults plus local overrides. The
merged properties are deep-copied, preserving caller input and preventing
nested mutable properties from leaking between the material, registry, and
caller. Overrides replace complete values, not nested fields. Names and
explicit Material instances retain intentional sharing. Global updates must
now be explicit. Regressions cover registered/unregistered inputs, nested
isolation, shared-reference behavior, and point/model conversion and ID
stability when another isotherm is constructed or locally edited.

## Medium-priority findings

### C13. Spreading-pressure bounds depend on earlier interpolation calls

With `q=p` at pressures `[1, 2, 3]`, `spreading_pressure_at(0.5)` initially
returns the intended Henry-region value **0.5**. After `loading_at(2)`, the
same call raises `CalculationError`. Also, after that cached interpolation,
`spreading_pressure_at(4, interp_fill='extrapolate')` raises before honoring
the requested fill. The bounds check consults the *previous* interpolator's
fill rather than the current call and rejects below-first-point values despite
the method's subsequent Henry approximation.

**Suggested correction.** Make the current call's arguments and branch data
determine bounds behavior; explicitly allow the defined low-pressure Henry
segment and apply the requested high-pressure fill. Test call-order
independence and both branches.

**Source:** [spreading-pressure bounds check](../../src/pygaps/core/pointisotherm.py#L1281).

**Resolution (feature/core-updates).** C2 removed the cache-dependent bounds
check. Regression coverage now explicitly exercises both adsorption and
descending desorption with no cache and different cached fills, confirming
Henry-region integration and current-call extrapolation choices.

### C14. Model selection compares different residual definitions

`guess` ranks candidates by their own `model.rmse`. Most loading models report
loading-range-normalized residuals, pressure models use pressure-range
normalization, and Virial reports an unnormalized log-pressure/loading
residual. These are not a common score.

In a deterministic 40-point example, let `p = numpy.geomspace(.01, 10, 40)`
and `q = p * (1 + .2*numpy.sin(numpy.log10(p)) +
.05*numpy.random.default_rng(0).normal(size=40))`. Henry's reported RMSE was
**0.01486** and Virial's **0.05588**, so
`guess(models=['Henry', 'Virial'])` chose Henry.
Evaluated instead using the same normalized pressure residual, Henry scored
**0.01578** and Virial **0.01199**. This does not establish that pressure
residual is the scientifically preferred criterion; it demonstrates that the
advertised “best RMS” selection depends on incomparable native metrics.
Virial is not in the default candidate list, but is accepted in a supplied list.

**Suggested correction.** Specify the selection objective and score every
candidate on the same observations and scale, with a policy for models whose
inverse is unavailable or numerically unreliable. Preserve/report native fit
metrics separately and test candidate ordering on mixed model directions.

**Disposition.** Deferred to the
[fitting assessment action points](fitting.md#action-points); selection scores
are unchanged by the core updates.

**Sources:** [selection](../../src/pygaps/core/modelisotherm.py#L450),
[base fit metric](../../src/pygaps/modelling/base_model.py#L247),
[Virial fit metric](../../src/pygaps/modelling/virial.py#L214).

### C15. The advertised boolean pseudo-pressure option does not work

At 150 K for nitrogen, `convert_pressure(mode_to='relative', pseudo=True)`
raises `CalculationError`, caused by a `ParameterError` saying no
pseudosaturation calculation was specified. Passing the undocumented string
`pseudo='Dubinin'` succeeds and gives about 0.020842 for an initial 1 bar.
The point method and converter describe/type the option as a boolean, while
the adsorbate method requires a named algorithm above the critical temperature.

**Suggested correction.** Agree and document whether `True` selects a default
method or a named method is mandatory; align signatures, validation and
examples across the three layers. Test below/above critical temperature and
unsupported method names without silently changing the scientific method.

**Resolution (feature/core-updates).** The agreed policy is now explicit at
all three layers: False disables pseudo-pressure, and True or 'Dubinin'
selects Dubinin above the critical temperature. Unsupported method names are
rejected even below the critical temperature. Tests cover boolean/named
selection and conversion through the point-isotherm and unit-converter layers.

**Sources:** [point conversion](../../src/pygaps/core/pointisotherm.py#L397),
[pressure converter](../../src/pygaps/units/converter_mode.py#L41),
[adsorbate pseudo selection](../../src/pygaps/core/adsorbate.py#L555).

### C16. Interpolation unit defaults and relative-mode checks are inconsistent

On an absolute-bar point or model isotherm,
`loading_at(2, pressure_mode='absolute')` raises for a missing pressure unit,
although the documented default is the internal unit. Both `pressure_at`
implementations demand a loading unit for `loading_basis='fraction'`, even
though that basis is dimensionless. A relative-pressure Henry model returns
1.0 for `spreading_pressure_at(0.5)` but raises `ParameterError` for the
equivalent explicit `pressure_mode='relative'`; the check tests the stored
mode rather than whether the *input* is absolute.

**Suggested correction.** Normalize inputs consistently: default to the
current unit when it is meaningful, require a unit when converting from an
absolute input to a unitless internal mode, and do not require units for
fraction/percent. Share the validation policy across point/model methods.

**Resolution (feature/core-updates).** Shared input-conversion helpers now
default pressure/loading/material units when the stored mode/basis makes
them meaningful. Dimensionless fraction/percent inputs need no loading unit.
Absolute input to a relative isotherm still requires explicit units; explicit
relative-mode model spreading-pressure calls no longer fail spuriously.
Point/model regressions cover defaults, dimensionless inputs, and required
units for changed physical bases.

**Sources:** [point pressure input](../../src/pygaps/core/pointisotherm.py#L1153),
[point loading input](../../src/pygaps/core/pointisotherm.py#L1038),
[model loading input](../../src/pygaps/core/modelisotherm.py#L826),
[model relative spreading pressure](../../src/pygaps/core/modelisotherm.py#L1038).

### C17. Zero limits are ignored and point/model endpoints differ

For pressures `[0, 1, 2]`, `pressure(limits=(None, 0))` returns all three
points; `loading(limits=(0, 0))` likewise returns all points. The
`limits and any(limits)` check treats zero-valued bounds as absent. The
point class uses inclusive `between`, while a model on `[1, 2, 3]` with
`limits=(1, 3)` returns only `[2]` because its comparisons are strict.

**Suggested correction.** Check each bound against `None`, define one
documented inclusion policy, and apply it to pressure, loading and
supplementary data. Test zero, open-ended, equal and exact-endpoint limits in
both classes.

**Resolution (feature/core-updates).** Zero bounds are no longer treated as
absent, and point/model data access uses inclusive lower and upper endpoints.
Regression coverage includes zero, open-ended, equal, and exact endpoint
limits, including indexed outputs and supplementary point data.

**Sources:** [point limits](../../src/pygaps/core/pointisotherm.py#L767),
[model limits](../../src/pygaps/core/modelisotherm.py#L624).

### C18. JSON does not round-trip all valid point-isotherm coordinates

**Transferred, not resolved.** Evidence and action points now live in the
[parsing review](parsing.md#c18-json-does-not-round-trip-all-valid-point-isotherm-coordinates).

### C19. Database autoinsert checks the in-memory registry, not the target DB

**Transferred, not resolved.** Evidence and action points now live in the
[parsing review](parsing.md#c19-database-autoinsert-checks-the-in-memory-registry-not-the-target-db).

### C20. Equality and hashing violate Python's container expectations

`Adsorbate('Test', alias=['Alias']) == 'alias'` is true, but their hashes
differ and `{adsorbate: 7}.get('alias')` returns `None`. Comparing that
adsorbate with an integer raises `AttributeError` instead of returning
`NotImplemented`/false. Separately, an isotherm put in a set can no longer be
found after its temperature changes because its hash is derived from mutable
content. Material/adsorbate names are mutable too.

**Suggested correction.** Separate alias matching from object equality, return
`NotImplemented` for unrelated types, and make mutable value objects
unhashable or give them a stable immutable identity. Case-insensitive and
multiple-alias equality with arbitrary strings cannot generally satisfy the
hash contract for all those strings. This is an API compatibility decision.

**Sources:** [adsorbate equality/hash](../../src/pygaps/core/adsorbate.py#L155),
[material equality/hash](../../src/pygaps/core/material.py#L64),
[isotherm equality/hash](../../src/pygaps/core/baseisotherm.py#L259).

### C21. Validation depends on construction path and misses invalid units

An array-based `ModelIsotherm(..., branch='bogus')` is accepted, whereas the
DataFrame path rejects it. A point DataFrame with branch values `[2, 2]` is
accepted but has neither an adsorption nor a desorption branch. The
documented `from_pointisotherm(..., branch=None)` instead raises for a
non-singular branch. A fractional isotherm can also be constructed with
`material_unit='bad'`; a later loading conversion raises raw `KeyError`.

**Suggested correction.** Validate branch and unit invariants on all input
paths, reconcile the documented meaning of `None`, and raise contextual
`ParameterError` before mutating state. Include fractional units and explicit
DataFrame branch columns in tests.

**Sources:** [point branch construction](../../src/pygaps/core/pointisotherm.py#L172),
[model branch construction](../../src/pygaps/core/modelisotherm.py#L130),
[material-unit validation](../../src/pygaps/core/baseisotherm.py#L181).

### C22. Thermodynamic fallback catches control-flow and programming errors

The thermodynamic wrappers repeatedly catch `BaseException`. When the backend
property was mocked to raise `KeyboardInterrupt`, `molar_mass()` returned its
stored value instead of allowing the interruption to propagate. The fallback
does log a warning, but it can similarly turn unrelated programming failures
into plausible scientific results; if the stored value is absent, the raised
error chains from the missing property rather than the original backend error.

**Suggested correction.** Catch documented backend failure types, preserve the
original exception context, and let `KeyboardInterrupt`, `SystemExit` and
unrelated failures propagate. Retain the intentionally supported stored-value
fallback, with clear provenance. Test both fallback and propagation.

**Source:** [representative backend fallback](../../src/pygaps/core/adsorbate.py#L327).

### C23. The documented vaporisation-property alias is not read

With `ads = Adsorbate('x', enthalpy_vaporisation=10)`,
`ads.enthalpy_vaporisation(77, calculate=False)` raises `CalculationError` because
the alias delegates to `enthalpy_liquefaction`, which only reads the
`enthalpy_liquefaction` key. The class documents both property names.

**Suggested correction.** Define alias precedence and sign convention, accept
the documented stored names consistently, and diagnose conflicting values.
Test both names, calculated and stored paths, and missing-property errors.

**Sources:** [vaporisation alias](../../src/pygaps/core/adsorbate.py#L843),
[stored liquefaction property](../../src/pygaps/core/adsorbate.py#L925).

## Lower-priority design and maintainability observations

### C24. Factory methods lose subclasses and leak a control option into metadata

`PointSubclass.from_modelisotherm(...)` returns `PointIsotherm`, not the
subclass. `ModelSubclass.from_pointisotherm(..., model='Henry')` returns the
subclass, but the list-model path returns `ModelIsotherm`. Both factories
hard-code the base class in one path. In addition, the list-model result's
`properties` contains `{'plot_fit': False}` because an internal control
argument is passed as ordinary metadata; it can appear in exports and IDs.

**Suggested correction.** Use `cls` consistently and separate control options
from persisted user metadata before invoking the base constructor. Add
subclass and metadata round-trip tests.

**Sources:** [point factory](../../src/pygaps/core/pointisotherm.py#L315),
[model factory](../../src/pygaps/core/modelisotherm.py#L343),
[guess control argument](../../src/pygaps/core/modelisotherm.py#L436).

### C25. Type contracts and data-quality policies need clarification

Pylance reports, among other examples, `reportArgumentType` on the `None`
defaults and `**properties: dict` in `BaseIsotherm`, and `reportReturnType`
because `Material.density` and `molar_mass` are annotated `float` but may
return `None`. Repeated conversion code and loosely typed metadata make it
harder to detect inconsistencies like C1/C16.

The point constructor also accepts a nonfinite primary loading: `[1, nan, 3]`
leads to `loading_at(2) == nan` without an explicit diagnostic. Missing data
may be intentional, so this is a **policy gap**, not a claim that every
nonfinite input must be rejected at construction.

**Suggested correction.** Correct optional/keyword annotations and introduce
small typed conversion/state helpers incrementally. Define when empty,
duplicate, nonfinite or nonphysical primary coordinates may be stored and
what calculation-time validation is required; report failures explicitly.
Keep auxiliary columns' missing-data policy separate.

**Sources:** [base annotations](../../src/pygaps/core/baseisotherm.py#L102),
[optional material properties](../../src/pygaps/core/material.py#L141),
[point construction](../../src/pygaps/core/pointisotherm.py#L120).

## Recommended sequencing and regression coverage

The remaining core work is recommended in this order; compatibility and
scientific-policy decisions still require agreement before implementation.

1. Address identity and hashing (C11, C20) with explicit compatibility and
   database migration decisions. Existing IDs and legacy files need
   compatibility tests.
2. Unify construction validation, narrow thermodynamic fallback handling, and
   reconcile stored-property aliases (C21-C23).
3. Fix factory extensibility/metadata leakage (C24), then improve type
   contracts and agree data-quality policies (C25).

C10, C18 and C19 are tracked separately in the parsing review and should be
coordinated with identity/persistence work. C14 remains a separate fitting
action, not an approved change to ranking.
Preserve the independent scientific oracles and cross-path/failure-state
regressions added for resolved findings. Run affected core tests plus relevant
JSON/SQLite and IAST suites when implementing the remaining fixes.

During the original assessment, one attempted `pytest --cov=pygaps.core`
instrumentation run failed while
importing NumPy with “cannot load module more than once per process.” Its
cause was not investigated; the path-based coverage run above completed.
Only the local Windows/Python 3.14 environment was exercised for these core
updates, not the full
supported Python/OS matrix.
