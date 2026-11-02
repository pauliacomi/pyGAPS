# Model fitting and inverse-function issues

This report records findings from the P0-5 test work on `feature/test-improvements`.
Scientific production fixes require separate approval. Review documents are excluded
from implementation commits.

## Evidence and scope

Measurements used Windows, Python 3.14, pytest 9.2.0 and the frozen project dependencies.
The fitting probe used 64 logarithmically spaced positive native-input points and
63 distinct geometric-midpoint evaluation points. Initial guesses alternate factors
of 1.2 and 0.8 on the known parameters; the solver budget is 2,000 evaluations.
The current findings do not establish behavior across the entire CI matrix.

## Findings

### F1: ChemiPhysisorption parameters are not individually identifiable

**Classification:** Structural property; not a demonstrated implementation bug.

At one temperature, `n_m2` and `Ea` enter the loading equation only as
`n_m2 * exp(-Ea / RT)`.
Increasing `Ea` by `RT` while multiplying `n_m2` by `e` produced exactly the same
loading on a 50-point pressure grid from 0.001 to 100.

**Test implication:** Assert curve accuracy and effective chemisorption capacity,
not independent recovery of both parameters. This does not establish extrapolation
to other temperatures or identify an activation energy from a single isotherm.

**Source:** [chemiphysisorption.py](../../src/pygaps/modelling/chemiphysisorption.py),
`ChemiPhysisorption.loading`.

### F2: Historical complex-model parameters can produce inaccurate local optima

**Classification:** Observed optimizer sensitivity; not proof of an incorrect equation.

Using the historical `MODEL_DATA` parameters, the bounded probe converged with:

| Model | Maximum held-out relative error | Reported RMSE |
| --- | --- | --- |
| DSToth | 0.02291 | 0.001553 |
| ChemiPhysisorption | 0.003720 | 0.0006335 |

DSToth's historical sites have nearby affinities `K1=3`, `K2=2`.
ChemiPhysisorption's historical chemical amplitude is small because `Ea/RT=4`.
These are unsuitable as the sole deterministic parameter-recovery cases.

Keeping the same grids and perturbations, separate fitting-only parameters
`K1=0.2`, `K2=5` for DSToth, and additionally `Ea=1000` for
ChemiPhysisorption, gave maximum held-out relative errors below `7e-16`.
No historical scientific reference values or tolerances were changed.
This demonstrates successful recovery on better-conditioned examples, not general
reliability of the default optimizer on all valid datasets.

**Test implication:** Use deliberate nondegenerate fit cases without loosening
prediction accuracy. Preserve this limitation for future multi-start/conditioning work.

**Sources:** [conftest.py](../../tests/modelling/conftest.py),
[base_model.py](../../src/pygaps/modelling/base_model.py).

### F3: WVST inverse fails at a valid positive input

**Classification:** Reproduced numerical inverse failure; candidate scientific fix.

With `n_m=30`, `K=2`, `L1v=2`, `Lv1=1`, the forward calculation gives
`pressure(20) = 74.19245718150573`.
Calling `loading(74.19245718150573)` raises `CalculationError` rather than
returning 20. The same inversion fails in an array containing the forward
pressures for loadings `[0.2, 1, 20]`.
Loadings 0.2 and 1 individually invert successfully.

**Relevant implementation:** The numerical root starts at zero without restricting
trial values to the physical loading interval. This is an implementation observation,
not a verified complete diagnosis.

**Test implication:** Do not describe a small-input inverse smoke test as broad
positive-domain validation. Keep native pressure-fit accuracy independent of this failure.

**Source:** [wvst.py](../../src/pygaps/modelling/wvst.py), `WVST.loading`.

### F4: JensenSeaton array inversion is sensitive after an accurate fit

**Classification:** Reproduced numerical inverse failure; broader diagnosis pending.

On the 64-point pressure fit grid from 0.001 to 100, using the historical
parameters, fitting achieves maximum held-out relative loading error below `2e-15`.
The fitted `t` is approximately `0.9999999999999977`.
Inverting the 63 held-out loading values together raises `CalculationError`
and emits an invalid-power `RuntimeWarning`.

A smaller three-element vector at pressures `[1, 10, 100]`, with `t=1-1e-12`,
inverts successfully, so vector length/domain and numerical solver behavior matter.
Do not generalize this finding to all arrays or all scalar calls.

**Test implication:** Quantitative native loading-fit assertions can succeed while
inverse behavior is unreliable. Any regression reproducer needs a precise dataset;
platform-dependent convergence should not become an unexplained CI failure.

**Source:** [jensenseaton.py](../../src/pygaps/modelling/jensenseaton.py),
`JensenSeaton.pressure` and `JensenSeaton.loading`.

### F5: Virial inverse has array and low-input accuracy limitations

**Classification:** Array capability limitation and observed scalar accuracy limitation.

With historical parameters `K=5`, `A=0.001`, `B=0.0001`, `C=0.0001`:

- `loading(pressure(0.2))` returns approximately `0.1999784514`;
  the relative error is `1.07743e-4`, exceeding the proposed fit prediction target.
- Inverting forward pressures for `[0.2, 1, 2]` as an array raises `ValueError`:
  the minimizer's objective must return a scalar.

The inverse docstring describes scalar inputs, so the array result alone does not
prove a violation of its documented public contract. The native `pressure` fit
supports arrays and remains quantitatively accurate.

**Test implication:** Do not apply an assumed generic array-inverse contract or
silently loosen the fit-accuracy target to accommodate this separate numerical routine.

**Source:** [virial.py](../../src/pygaps/modelling/virial.py), `Virial.loading`.

## Test-infrastructure corrections, not model defects

- The old fit tests left range metadata at NaN defaults, making the base model's
  otherwise successful fit report NaN RMSE. Initialize real ranges in quantitative tests.
- Several old fit datasets contain fewer informative points than parameters.
  Use dense grids rather than treating an underdetermined fit as parameter recovery.
- Virial minimizes log-pressure/loading residuals and reports their unnormalized RMS;
  other models normalize native-response RMS by the corresponding response range.
  Verify the actual metric rather than imposing a single formula on every model.
- DA's historical `m=3` lies at its upper bound. A generic 20% upward perturbation
  is an invalid initial guess, not a scientific failure. Use an interior fitting-only
  value `m=2.5`.

## Decisions and follow-up

### Action points

- **C14 (from the core review): use a common model-selection score.**
  `ModelIsotherm.guess` currently compares incompatible native RMSE values:
  loading-normalized, pressure-normalized, and Virial's log-pressure/loading
  residual. Define the scientific selection objective before changing ranking.
  Evaluate every candidate on the same observations and scale, define how
  unavailable or unreliable inverses are handled, retain native fit metrics
  separately, and test mixed pressure/loading-direction candidates. Include
  the deterministic Henry/Virial counterexample in
  [the core assessment](core.md#c14-model-selection-compares-different-residual-definitions).
  This action remains deferred; the core updates do not change selection scores.

### Existing fitting-test decisions

P0-5 curve accuracy and identifiable parameter recovery are approved.
No production correction or tolerance relaxation is approved.
The user chose to document/defer the newly observed inverse failures to P2-4,
without adding strict-xfail inverse regressions under P0-5.
P0-5 checks all 18 native-direction fits and scalar/array round trips for the ten
analytical inverse implementations. Numerical inverse routines are not claimed
to satisfy that expanded round-trip contract.

The fitting-only datasets, parameter perturbations and identifiable-recovery rules
are implemented in [conftest.py](../../tests/modelling/conftest.py) and
[test_models_isotherm.py](../../tests/modelling/test_models_isotherm.py).
Historical equation-reference data and tolerances are unchanged.

Quantitative fit/recovery, initial-guess, analytical inverse and public-integration
tests also pass on Python 3.10 with pytest 9.1.0 (185 focused tests).
These passing supported-runtime checks do not validate or repair the deferred
numerical inverse findings above.
