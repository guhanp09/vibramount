# VibraMount engineering report

The 24 kg moving assembly uses four equally loaded mounts. The operating-band objective is uniformly weighted RMS transmissibility from 20 to 120 Hz. Dynamic stiffness and damping are assigned inputs, not inferred from geometry.

## Results

| Quantity | Cylindrical reference | Selected tapered form factor |
|---|---:|---:|
| Per-mount stiffness [N/m] | 25000 | 15000 |
| Per-mount damping [N·s/m] | 100 | 65 |
| Natural frequency [Hz] | 10.273 | 7.958 |
| Damping ratio | 0.1291 | 0.1083 |
| Static deflection [mm] | 2.354 | 3.923 |
| Band RMS transmissibility | 0.10122 | 0.05872 |
| Worst operating-band T | 0.3948 | 0.2131 |
| Continuous resonance peak | 4.030 | 4.748 |

The predicted RMS reduction is **41.99%** and the worst-band reduction **46.04%**, relative to the defined reference. The selected property combination satisfies all configured compression, load and resonance limits. Its design load is 89.59 N per mount. This is not measured vibration or noise reduction.

The sweep evaluates 3567 combinations. Tapered and stepped geometries can accept the same optimal properties; the taper is selected for lower assembly complexity. The short cylindrical geometry is restricted by its nominal compression-strain limit. There is no assigned geometric performance multiplier.

Doubling frequency samples changes the selected RMS by 7.81e-10 relative. Tests independently compare the transfer function with SciPy and check analytical limits. The selected resonance peak is larger than the reference, so startup passage through resonance remains a design consideration.

## Mechanical realization and limits

Three editable FreeCAD assemblies, drawings, STEP and metre-unit STL files are under `cad/exports/`. Split studs avoid a steel bypass across the rubber. Native validity, edit/reopen checks and geometric separation are in each `checks.json`.

Actual mount properties require calibration versus load, frequency and temperature. Equal mount loads, rigid plates, vertical SDOF motion and massless series spacers are assumptions. Plate strength, rubber stresses, bond durability, rocking and noise are not validated. Follow `docs/assembly.md` for proposed measurements. Physical testing was not performed.
