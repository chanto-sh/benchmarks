"""Back-of-the-envelope Earth orbit mission planning."""
import math

MU_EARTH = 398600.4418  # km^3 / s^2
R_EARTH = 6378.137      # equatorial radius, km


def circular_speed(alt_km):
    """Speed (km/s) of a circular orbit at the given altitude (km)."""
    return math.sqrt(MU_EARTH / (R_EARTH + alt_km))


def hohmann_dv(alt1_km, alt2_km):
    """Total delta-v (km/s) of a Hohmann transfer between two circular orbits."""
    r1, r2 = R_EARTH + alt1_km, R_EARTH + alt2_km
    a = (r1 + r2) / 2
    v1, v2 = circular_speed(alt1_km), circular_speed(alt2_km)
    vp = math.sqrt(MU_EARTH * (2 / r1 - 1 / a))
    va = math.sqrt(MU_EARTH * (2 / r2 - 1 / a))
    return abs(vp - v1) + abs(v2 - va)


def plane_change_dv(speed_kms, angle_deg):
    """Delta-v (km/s) to rotate the orbital plane by angle_deg at the given speed."""
    return 2 * speed_kms * math.sin(angle_deg / 2)


def orbit_period(perigee_alt_km, apogee_alt_km, steps_per_orbit=4000):
    """Orbital period in seconds, found by integrating the orbit (so that
    perturbations can be added to accel() later)."""
    rp = (R_EARTH + perigee_alt_km) * 1000.0  # metres
    ra = (R_EARTH + apogee_alt_km) * 1000.0
    a = (rp + ra) / 2
    mu = MU_EARTH * 1e9  # m^3 / s^2
    vp = math.sqrt(mu * (2 / rp - 1 / a))
    dt = 2 * math.pi * math.sqrt(a ** 3 / mu) / steps_per_orbit

    def f(s):
        r3 = (s[0] ** 2 + s[1] ** 2) ** 1.5
        return (s[2], s[3], -mu * s[0] / r3, -mu * s[1] / r3)

    s = [rp, 0.0, 0.0, vp]
    t, swept = 0.0, 0.0
    while True:
        k1 = f(s)
        k2 = f([x + dt / 2 * y for x, y in zip(s, k1)])
        k3 = f([x + dt / 2 * y for x, y in zip(s, k2)])
        k4 = f([x + dt * y for x, y in zip(s, k3)])
        n = [x + dt / 6 * (p + 2 * q + 2 * r + w) for x, p, q, r, w in zip(s, k1, k2, k3, k4)]
        d = math.atan2(s[0] * n[1] - s[1] * n[0], s[0] * n[0] + s[1] * n[1])
        if swept + d >= 2 * math.pi:
            return t + dt * (2 * math.pi - swept) / d
        swept += d
        s, t = n, t + dt
