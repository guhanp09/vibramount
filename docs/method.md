# Dynamics and assumptions

All baseline values are illustrative engineering assumptions, not measurements or catalog ratings. The moving assembly is 24 kg including the isolated plate and attached hardware. Four equally loaded mounts support a rigid plate; rocking, lateral motion, support flexibility and imbalance eccentricity are excluded.

## SDOF equations

For n identical parallel mounts, K=n·k and C=n·c. The natural frequency is fn=sqrt(K/m)/(2π), damping ratio ζ=C/(2sqrt(Km)), and static deflection δ=mg/K. Static load per mount is mg/n.

For prescribed harmonic base motion y, m·ẍ+C(ẋ−ẏ)+K(x−y)=0. The absolute displacement ratio is

T=|X/Y|=sqrt[(1+(2ζr)²)/((1−r²)²+(2ζr)²)], r=f/fn.

This tends to one at zero frequency and falls below one only above r=√2. Extra damping suppresses resonance but increases high-frequency transmission. The continuous peak uses r_peak²=2/(1+sqrt(1+8ζ²)); undamped resonance is unbounded.

For the separate fixed-base loading model, m·ẍ+C·ẋ+K·x=F0 exp(iωt). Then |X|=F0/|K−mω²+iCω| and |Ft|=|K+iCω|·|X|. Its force-transmission ratio has the same algebraic T, but the input/output quantities differ. The study uses an illustrative constant 25 N force amplitude; it does not infer a compressor's actual unbalance spectrum or sound level.

The objective is RMS T over a uniformly weighted 20–120 Hz frequency band, integrated with SciPy Simpson quadrature. This weighting is an explicit design choice, not an operating-duty distribution. The bounded sweep uses k=15–35 kN/m per mount in 0.5 kN/m steps and c=40–180 N·s/m in 5 N·s/m steps.

Constraints are static compression ≤4 mm, nominal static rubber strain ≤15%, resonance peak ≤5, and design load per mount ≤150 N. Design load is 1.5 times static load plus the maximum operating-band harmonic transmitted force per mount. The strain and load limits are assumptions requiring hardware confirmation. Ties in performance prefer lower manufacturing complexity.

## Geometry versus assigned properties

Cylinder, taper and stepped shapes have separate assigned stiffness/damping reference points. These values are not calculated from shape or a rubber modulus. All shapes share the same property-search bounds. Their different rubber heights affect the compression-strain constraint, not an invented shape-performance multiplier. A selected shape is a compatible form factor for the optimized dynamic properties; it does not prove that tapering rubber creates those properties.

The stepped design has two equal Kelvin–Voigt stages separated by a nominally massless spacer. A constant equivalent KV model is valid only when the stages have equal relaxation times c/k. Each stage has twice the equivalent per-mount k and c. The model checks this condition. Real spacer mass, internal modes, temperature dependence and frequency-dependent rubber properties require additional characterization; the step model is not a general two-degree-of-freedom prediction.

## Verification and physical validation

Tests compare the formula with SciPy's independent transfer-function frequency response, check force balance, series compliance, scaling, resonance, limits, invalid inputs, and optimization constraints. Frequency integration is repeated at twice the sampling density. CAD validity, hole clearance, steel load-path separation, native reopen and editable-height recomputation are checked with FreeCAD. These checks are numerical/geometry verification, not experimental validation.

Reference: [Purdue University, vibration isolation](https://www.purdue.edu/freeform/ervibrations/chapter-v-animations/vibration-isolation/) explains the base-motion transfer function and damping tradeoff. [SciPy frequency response](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.freqresp.html) supplies the independent numerical implementation used in tests.
