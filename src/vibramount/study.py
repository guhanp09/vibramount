"""Bounded property sweep, engineering comparison and reproducible figures."""

import argparse
import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import simpson

from vibramount.model import MountSystem, force_response, peak, transmissibility

ROOT = Path(__file__).resolve().parents[2]


def load(path=None):
    config = json.loads(Path(path or ROOT / "configs/baseline.json").read_text())
    lo, hi = config["frequency_hz"]
    if not 0 < lo < hi or config["frequency_samples"] < 101:
        raise ValueError("Frequency band needs positive ordered limits and at least 101 samples")
    if config["max_static_deflection_m"] <= 0 or not 0 < config["max_compressive_strain"] < 1:
        raise ValueError("Invalid compression limits")
    return config


def system(c, k, damping):
    return MountSystem(c["mass_kg"], c["mount_count"], k, damping, c["gravity_m_s2"])


def metrics(c, shape, k, damping, samples=None):
    s = system(c, k, damping)
    f = np.linspace(*c["frequency_hz"], samples or c["frequency_samples"])
    t = transmissibility(f, s)
    rms = np.sqrt(simpson(t**2, x=f) / np.ptp(f))
    peak_f, peak_t = peak(s)
    dynamic_x, support_force = force_response(f, s, c["force_amplitude_n"])
    height = c["designs"][shape]["rubber_height_mm"] / 1000
    strain = s.static_deflection_m / height
    design_load = c["load_factor"] * s.static_load_per_mount_n + support_force.max() / s.mount_count
    d = c["designs"][shape]
    contact_area = (
        np.pi
        / 4
        * (min(d["bottom_diameter_mm"], d["top_diameter_mm"]) ** 2 - d["bore_mm"] ** 2)
        * 1e-6
    )
    feasible = (
        s.static_deflection_m <= c["max_static_deflection_m"]
        and strain <= c["max_compressive_strain"]
        and peak_t <= c["max_peak_transmissibility"]
        and design_load <= c["max_mount_design_load_n"]
    )
    return {
        "shape": shape,
        "stiffness_per_mount_n_m": k,
        "damping_per_mount_ns_m": damping,
        "natural_frequency_hz": float(s.natural_frequency_hz),
        "damping_ratio": float(s.damping_ratio),
        "static_deflection_mm": s.static_deflection_m * 1000,
        "static_load_per_mount_n": s.static_load_per_mount_n,
        "design_load_per_mount_n": float(design_load),
        "nominal_contact_stress_kpa": float(design_load / contact_area / 1000),
        "compression_strain": strain,
        "peak_transmissibility": peak_t,
        "peak_frequency_hz": peak_f,
        "band_rms_transmissibility": float(rms),
        "band_max_transmissibility": float(t.max()),
        "max_dynamic_displacement_mm": float(dynamic_x.max() * 1000),
        "complexity": d["complexity"],
        "feasible": bool(feasible),
    }


def sweep(c):
    def values(key):
        start, stop, step = c["sweep"][key]
        if step <= 0 or stop < start:
            raise ValueError("Invalid sweep bounds")
        return np.arange(start, stop + max(abs(stop), 1) * 1e-12, step)

    rows = [
        metrics(c, name, float(k), float(damping))
        for name in c["designs"]
        for k in values("stiffness_per_mount_n_m")
        for damping in values("damping_per_mount_ns_m")
    ]
    feasible = [r for r in rows if r["feasible"]]
    if not feasible:
        raise ValueError("No mount satisfies the constraints")
    selected = min(feasible, key=lambda r: (r["band_rms_transmissibility"], r["complexity"]))
    return rows, selected


def write_csv(path, rows):
    with path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run(c, out):
    out.mkdir(parents=True, exist_ok=True)
    rows, selected = sweep(c)
    comparison = [
        metrics(c, n, d["stiffness_per_mount_n_m"], d["damping_per_mount_ns_m"])
        for n, d in c["designs"].items()
    ]
    comparison.append(selected | {"shape": "optimized_" + selected["shape"]})
    baseline = comparison[0]
    check = metrics(
        c,
        selected["shape"],
        selected["stiffness_per_mount_n_m"],
        selected["damping_per_mount_ns_m"],
        2001,
    )
    error = abs(check["band_rms_transmissibility"] / selected["band_rms_transmissibility"] - 1)
    summary = {
        "inputs": c,
        "selected": selected,
        "baseline": baseline,
        "candidate_count": len(rows),
        "rms_reduction_pct": 100
        * (1 - selected["band_rms_transmissibility"] / baseline["band_rms_transmissibility"]),
        "band_max_reduction_pct": 100
        * (1 - selected["band_max_transmissibility"] / baseline["band_max_transmissibility"]),
        "frequency_integration_relative_change": error,
        "physical_testing_performed": False,
        "property_provenance": "Assigned dynamic properties; not calculated from rubber geometry",
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    write_csv(out / "comparison.csv", comparison)
    write_csv(out / "parameter_sweep.csv", rows)
    plt.rcParams.update({"axes.grid": True, "grid.alpha": 0.2, "figure.figsize": (8, 4.5)})
    for filename, frequencies, logarithmic in [
        ("frequency_response", np.geomspace(0.5, 150, 1500), True),
        ("operating_band", np.linspace(*c["frequency_hz"], 1001), False),
    ]:
        fig, ax = plt.subplots()
        for row in comparison:
            s = system(c, row["stiffness_per_mount_n_m"], row["damping_per_mount_ns_m"])
            ax.plot(
                frequencies, transmissibility(frequencies, s), label=row["shape"].replace("_", " ")
            )
        if logarithmic:
            ax.set_xscale("log")
            ax.axvspan(*c["frequency_hz"], color="grey", alpha=0.12, label="Operating band")
        ax.set(
            xlabel="Excitation frequency [Hz]",
            ylabel="Transmissibility [−]",
            title="Linear SDOF prediction · base motion / fixed-base harmonic force",
        )
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(out / (filename + ".png"), dpi=160)
        plt.close(fig)
    feasible = [r for r in rows if r["feasible"] and r["shape"] == selected["shape"]]
    fig, ax = plt.subplots()
    scatter = ax.scatter(
        [r["stiffness_per_mount_n_m"] / 1000 for r in feasible],
        [r["damping_per_mount_ns_m"] for r in feasible],
        c=[r["band_rms_transmissibility"] for r in feasible],
        s=12,
        cmap="viridis",
    )
    ax.scatter(
        selected["stiffness_per_mount_n_m"] / 1000,
        selected["damping_per_mount_ns_m"],
        marker="*",
        color="red",
        s=140,
    )
    ax.set(
        xlabel="Per-mount stiffness [kN/m]",
        ylabel="Per-mount viscous damping [N·s/m]",
        title="Feasible property combinations · selected form factor: " + selected["shape"],
    )
    fig.colorbar(scatter, ax=ax, label="Band RMS transmissibility [−]")
    fig.tight_layout()
    fig.savefig(out / "property_sweep.png", dpi=160)
    plt.close(fig)
    report = f"""# VibraMount engineering report

The 24 kg moving assembly uses four equally loaded mounts. The operating-band objective is uniformly weighted RMS transmissibility from 20 to 120 Hz. Dynamic stiffness and damping are assigned inputs, not inferred from geometry.

## Results

| Quantity | Cylindrical reference | Selected {selected["shape"]} form factor |
|---|---:|---:|
| Per-mount stiffness [N/m] | {baseline["stiffness_per_mount_n_m"]:.0f} | {selected["stiffness_per_mount_n_m"]:.0f} |
| Per-mount damping [N·s/m] | {baseline["damping_per_mount_ns_m"]:.0f} | {selected["damping_per_mount_ns_m"]:.0f} |
| Natural frequency [Hz] | {baseline["natural_frequency_hz"]:.3f} | {selected["natural_frequency_hz"]:.3f} |
| Damping ratio | {baseline["damping_ratio"]:.4f} | {selected["damping_ratio"]:.4f} |
| Static deflection [mm] | {baseline["static_deflection_mm"]:.3f} | {selected["static_deflection_mm"]:.3f} |
| Band RMS transmissibility | {baseline["band_rms_transmissibility"]:.5f} | {selected["band_rms_transmissibility"]:.5f} |
| Worst operating-band T | {baseline["band_max_transmissibility"]:.4f} | {selected["band_max_transmissibility"]:.4f} |
| Continuous resonance peak | {baseline["peak_transmissibility"]:.3f} | {selected["peak_transmissibility"]:.3f} |

The predicted RMS reduction is **{summary["rms_reduction_pct"]:.2f}%** and the worst-band reduction **{summary["band_max_reduction_pct"]:.2f}%**, relative to the defined reference. The selected property combination satisfies all configured compression, load and resonance limits. Its design load is {selected["design_load_per_mount_n"]:.2f} N per mount. This is not measured vibration or noise reduction.

The sweep evaluates {len(rows)} combinations. Tapered and stepped geometries can accept the same optimal properties; the taper is selected for lower assembly complexity. The short cylindrical geometry is restricted by its nominal compression-strain limit. There is no assigned geometric performance multiplier.

Doubling frequency samples changes the selected RMS by {error:.3g} relative. Tests independently compare the transfer function with SciPy and check analytical limits. The selected resonance peak is larger than the reference, so startup passage through resonance remains a design consideration.

## Mechanical realization and limits

Three editable FreeCAD assemblies, drawings, STEP and metre-unit STL files are under `cad/exports/`. Split studs avoid a steel bypass across the rubber. Native validity, edit/reopen checks and geometric separation are in each `checks.json`.

Actual mount properties require calibration versus load, frequency and temperature. Equal mount loads, rigid plates, vertical SDOF motion and massless series spacers are assumptions. Plate strength, rubber stresses, bond durability, rocking and noise are not validated. Follow `docs/assembly.md` for proposed measurements. Physical testing was not performed.
"""
    (out / "report.md").write_text(report)
    print(
        json.dumps(
            {k: summary[k] for k in ["selected", "rms_reduction_pct", "candidate_count"]}, indent=2
        )
    )
    return summary


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path)
    p.add_argument("--output", type=Path, default=ROOT / "results")
    a = p.parse_args()
    run(load(a.config), a.output)


if __name__ == "__main__":
    main()
