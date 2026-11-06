"""Linear vertical SDOF dynamics; SI units throughout."""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class MountSystem:
    mass_kg: float
    mount_count: int
    stiffness_per_mount_n_m: float
    damping_per_mount_ns_m: float
    gravity_m_s2: float = 9.80665

    def __post_init__(self):
        values = [self.mass_kg, self.stiffness_per_mount_n_m, self.gravity_m_s2]
        if not all(np.isfinite(v) and v > 0 for v in values):
            raise ValueError("Mass, stiffness and gravity must be finite and positive")
        if not isinstance(self.mount_count, int) or self.mount_count < 1:
            raise ValueError("Mount count must be a positive integer")
        if not np.isfinite(self.damping_per_mount_ns_m) or self.damping_per_mount_ns_m < 0:
            raise ValueError("Damping must be finite and nonnegative")

    @property
    def stiffness_n_m(self):
        return self.mount_count * self.stiffness_per_mount_n_m

    @property
    def damping_ns_m(self):
        return self.mount_count * self.damping_per_mount_ns_m

    @property
    def natural_frequency_hz(self):
        return np.sqrt(self.stiffness_n_m / self.mass_kg) / (2 * np.pi)

    @property
    def damping_ratio(self):
        return self.damping_ns_m / (2 * np.sqrt(self.mass_kg * self.stiffness_n_m))

    @property
    def static_deflection_m(self):
        return self.mass_kg * self.gravity_m_s2 / self.stiffness_n_m

    @property
    def static_load_per_mount_n(self):
        return self.mass_kg * self.gravity_m_s2 / self.mount_count


def transmissibility(frequency_hz, system: MountSystem):
    """Absolute motion/base motion; also the fixed-base harmonic-force ratio."""
    frequency = np.asarray(frequency_hz, dtype=float)
    if not np.isfinite(frequency).all() or np.any(frequency < 0):
        raise ValueError("Frequency must be finite and nonnegative")
    r = frequency / system.natural_frequency_hz
    damping = 2 * system.damping_ratio * r
    with np.errstate(divide="ignore", invalid="raise"):
        return np.sqrt((1 + damping**2) / ((1 - r**2) ** 2 + damping**2))


def peak(system: MountSystem):
    zeta = system.damping_ratio
    if zeta == 0:
        return system.natural_frequency_hz, float("inf")
    ratio = np.sqrt(2 / (1 + np.sqrt(1 + 8 * zeta**2)))
    frequency = ratio * system.natural_frequency_hz
    return float(frequency), float(transmissibility(frequency, system))


def force_response(frequency_hz, system: MountSystem, force_n: float):
    """Fixed base, internal harmonic force F0: displacement [m], support force [N]."""
    if not np.isfinite(force_n) or force_n < 0:
        raise ValueError("Force amplitude must be finite and nonnegative")
    frequency = np.asarray(frequency_hz, dtype=float)
    if not np.isfinite(frequency).all() or np.any(frequency < 0):
        raise ValueError("Invalid frequency")
    omega = 2 * np.pi * frequency
    impedance = system.stiffness_n_m - system.mass_kg * omega**2 + 1j * system.damping_ns_m * omega
    displacement = force_n / np.abs(impedance)
    support_force = np.abs(system.stiffness_n_m + 1j * system.damping_ns_m * omega) * displacement
    return displacement, support_force


def equivalent_series(stiffness, damping):
    """Massless Kelvin–Voigt stages reduce to one KV element only for equal c/k."""
    k, c = np.asarray(stiffness, dtype=float), np.asarray(damping, dtype=float)
    if k.shape != c.shape or k.ndim != 1 or not len(k):
        raise ValueError("Stage arrays must have equal nonzero length")
    if not np.isfinite(k).all() or not np.isfinite(c).all() or np.any(k <= 0) or np.any(c < 0):
        raise ValueError("Invalid stage stiffness or damping")
    tau = c / k
    if not np.allclose(tau, tau[0], rtol=1e-9, atol=1e-12):
        raise ValueError("Unequal stage relaxation times require a frequency-dependent model")
    equivalent_k = 1 / np.sum(1 / k)
    return float(equivalent_k), float(tau[0] * equivalent_k)
