import math
import sys

sys.path.insert(0, ".")
from oscillator import amplitude, displacement  # the code under test


def rk4_samples(m, k, c, F0, w, x0, v0, times, h=2e-4):
    """Independent truth: RK4 integration of the ODE, sampled at the given times."""
    def f(t, x, v):
        return v, (F0 * math.cos(w * t) - c * v - k * x) / m

    out = {}
    t, x, v = 0.0, x0, v0
    for target in sorted(times):
        while t < target - 1e-12:
            hh = min(h, target - t)
            k1 = f(t, x, v)
            k2 = f(t + hh / 2, x + hh / 2 * k1[0], v + hh / 2 * k1[1])
            k3 = f(t + hh / 2, x + hh / 2 * k2[0], v + hh / 2 * k2[1])
            k4 = f(t + hh, x + hh * k3[0], v + hh * k3[1])
            x += hh / 6 * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0])
            v += hh / 6 * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1])
            t += hh
        out[target] = x
    return out


cases = [
    # m, k, c, F0, omega, x0, v0   (label)
    ((2.5, 10.0, 0.3, 1.7, 1.9, 0.2, -0.5), "underdamped, near resonance"),
    ((0.4, 3.0, 0.05, 0.6, 2.9, 0.0, 0.0), "light damping, off resonance"),
    ((2.0, 8.0, 8.0, 3.0, 1.3, 0.5, 1.0), "critically damped"),
    ((1.5, 2.0, 9.0, 2.0, 0.7, -0.4, 0.3), "overdamped"),
    ((3.0, 12.0, 0.0, 1.0, 1.1, 0.1, 0.0), "undamped, off resonance"),
    ((0.7, 5.0, 1.2, -2.0, 4.4, 1.0, 2.0), "driven above resonance"),
]
times = [0.0, 0.37, 1.0, 2.9, 6.1, 11.3]
fail = []
for (m, k, c, F0, w, x0, v0), label in cases:
    amp = abs(F0) / math.sqrt((k - m * w * w) ** 2 + (c * w) ** 2)
    got = amplitude(m, k, c, F0, w)
    if abs(got - amp) > 1e-9 * amp:
        fail.append(f"{label}: amplitude {got!r}, expected {amp!r}")
    scale = max(abs(x0), amp, abs(F0) / k)
    ref = rk4_samples(m, k, c, F0, w, x0, v0, times)
    for t in times:
        try:
            x = displacement(m, k, c, F0, w, x0, v0, t)
        except Exception as e:  # noqa: BLE001
            fail.append(f"{label}: displacement(t={t}) raised {e!r}")
            break
        if not (abs(x - ref[t]) <= 1e-6 * scale):
            fail.append(f"{label}: x({t}) = {x!r}, expected {ref[t]!r}")
if fail:
    print("\n".join(fail))
    sys.exit(1)
print("hidden ok")
