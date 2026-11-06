import numpy as np
import pytest
from scipy import signal

from vibramount.model import MountSystem, equivalent_series, force_response, peak, transmissibility
from vibramount.study import load, metrics, sweep, system


@pytest.fixture
def mount():
    return MountSystem(24, 4, 25000, 100)


def test_stiffness_load_and_static_equilibrium(mount):
    assert mount.stiffness_n_m == 100000
    assert mount.static_deflection_m * mount.stiffness_n_m == pytest.approx(24 * 9.80665)
    assert 4 * mount.static_load_per_mount_n == pytest.approx(24 * 9.80665)


def test_natural_frequency_scaling(mount):
    heavier = MountSystem(96, 4, 25000, 100)
    stiffer = MountSystem(24, 4, 100000, 100)
    assert heavier.natural_frequency_hz == pytest.approx(mount.natural_frequency_hz / 2)
    assert stiffer.natural_frequency_hz == pytest.approx(mount.natural_frequency_hz * 2)


def test_low_and_high_frequency_limits(mount):
    assert transmissibility(0, mount) == 1
    r = 1e7
    assert transmissibility(r * mount.natural_frequency_hz, mount) == pytest.approx(
        2 * mount.damping_ratio / r, rel=1e-6
    )


def test_transfer_function_matches_scipy(mount):
    f = np.geomspace(0.1, 1000, 200)
    tf = signal.TransferFunction(
        [mount.damping_ns_m, mount.stiffness_n_m],
        [mount.mass_kg, mount.damping_ns_m, mount.stiffness_n_m],
    )
    _, h = signal.freqresp(tf, 2 * np.pi * f)
    assert transmissibility(f, mount) == pytest.approx(abs(h), rel=1e-12)


def test_force_interpretation_has_independent_dimensional_balance(mount):
    f = np.array([0.0, 20.0, 60.0, 120.0])
    displacement, support = force_response(f, mount, 25.0)
    assert displacement[0] == pytest.approx(25 / mount.stiffness_n_m)
    assert support / 25 == pytest.approx(transmissibility(f, mount))
    assert np.all(displacement >= 0)


def test_damping_tradeoff_and_isolation_boundary():
    light, heavy = MountSystem(24, 4, 25000, 40), MountSystem(24, 4, 25000, 150)
    assert peak(heavy)[1] < peak(light)[1]
    assert transmissibility(100, heavy) > transmissibility(100, light)
    assert transmissibility(np.sqrt(2) * light.natural_frequency_hz, light) == pytest.approx(1)


def test_analytical_peak_matches_dense_frequency_scan(mount):
    frequency, value = peak(mount)
    f = np.linspace(0.7, 1.2, 10001) * mount.natural_frequency_hz
    assert value == pytest.approx(transmissibility(f, mount).max(), rel=1e-7)
    assert frequency < mount.natural_frequency_hz


def test_undamped_resonance():
    s = MountSystem(24, 4, 25000, 0)
    assert np.isinf(transmissibility(s.natural_frequency_hz, s))
    assert np.isinf(peak(s)[1])


@pytest.mark.parametrize(
    "args",
    [
        (-1, 4, 25000, 100),
        (24, 0, 25000, 100),
        (24, 4, -1, 100),
        (24, 4, 25000, -1),
        (float("nan"), 4, 25000, 100),
    ],
)
def test_invalid_parameters(args):
    with pytest.raises(ValueError):
        MountSystem(*args)


def test_invalid_frequency(mount):
    with pytest.raises(ValueError):
        transmissibility([-1, 20], mount)


def test_series_reduction_matches_complex_compliance():
    k, c = equivalent_series([32000, 32000], [180, 180])
    assert k == 16000 and c == 90
    omega = np.array([1.0, 100.0, 700.0])
    actual = 1 / (2 / (32000 + 1j * omega * 180))
    assert actual == pytest.approx(k + 1j * omega * c)
    with pytest.raises(ValueError, match="relaxation"):
        equivalent_series([30000, 30000], [100, 200])


def test_optimization_constraints_and_resolution():
    c = load()
    rows, winner = sweep(c)
    baseline = c["designs"]["cylindrical"]
    reference = metrics(
        c, "cylindrical", baseline["stiffness_per_mount_n_m"], baseline["damping_per_mount_ns_m"]
    )
    assert len(rows) == 3567
    assert winner["feasible"] and winner["shape"] == "tapered"
    assert winner["band_rms_transmissibility"] < reference["band_rms_transmissibility"]
    assert winner["static_deflection_mm"] <= 4
    assert winner["peak_transmissibility"] <= 5
    assert winner["compression_strain"] <= 0.15
    fine = metrics(
        c,
        winner["shape"],
        winner["stiffness_per_mount_n_m"],
        winner["damping_per_mount_ns_m"],
        2001,
    )
    assert fine["band_rms_transmissibility"] == pytest.approx(
        winner["band_rms_transmissibility"], rel=1e-5
    )
    assert system(c, 15000, 65).static_deflection_m < 0.004
