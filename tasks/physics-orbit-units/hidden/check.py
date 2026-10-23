import math
import sys

sys.path.insert(0, ".")
import mission  # the code under test

MU, R = 398600.4418, 6378.137  # km^3/s^2, km
fail = []


def close(label, got, want, rel):
    if not abs(got - want) <= rel * abs(want):
        fail.append(f"{label}: got {got!r}, expected {want!r}")


for alt in (350.0, 1234.5, 20200.0):
    close(f"circular_speed({alt})", mission.circular_speed(alt), math.sqrt(MU / (R + alt)), 1e-9)
for h1, h2 in ((400.0, 20200.0), (800.0, 1500.0), (35786.0, 300.0)):
    r1, r2 = R + h1, R + h2
    a = (r1 + r2) / 2
    want = abs(math.sqrt(MU * (2 / r1 - 1 / a)) - math.sqrt(MU / r1)) + abs(math.sqrt(MU / r2) - math.sqrt(MU * (2 / r2 - 1 / a)))
    close(f"hohmann_dv({h1}, {h2})", mission.hohmann_dv(h1, h2), want, 1e-9)
for v, ang in ((7.67, 28.5), (3.07, 51.6), (1.6, 90.0), (7.0, 0.0)):
    close(f"plane_change_dv({v}, {ang})", mission.plane_change_dv(v, ang), 2 * v * math.sin(math.radians(ang) / 2), 1e-9)
for hp, ha in ((420.0, 420.0), (600.0, 39750.0), (250.0, 35786.0)):
    a = R + (hp + ha) / 2
    close(f"orbit_period({hp}, {ha})", mission.orbit_period(hp, ha), 2 * math.pi * math.sqrt(a ** 3 / MU), 1e-5)
if fail:
    print("\n".join(fail))
    sys.exit(1)
print("hidden ok")
