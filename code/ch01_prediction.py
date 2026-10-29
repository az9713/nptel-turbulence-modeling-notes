"""Constructed checks of prediction, convergence, sensitivity, and energy."""

from math import exp, floor, isclose, log

height, width, bulk_speed = 0.04, 1.0, 10.0
flow_rate = height * width * bulk_speed
pressure, efficiency = 100.0, 0.6
power = pressure * flow_rate
print(f"flow m3/s: {flow_rate:.6f}")
print(f"pressure work W: {power:.6f}")
print(f"electrical power W: {power / efficiency:.6f}")
for continuum in [80.0, 100.0]:
    values = [continuum + 400 / n**2 for n in [10, 20, 40]]
    extrapolated = (4 * values[2] - values[1]) / 3
    assert isclose(extrapolated, continuum)
    print(
        f"continuum {continuum:.0f} Pa: {values}, extrapolated "
        f"{extrapolated:.6f}"
    )
z, other, initial_gap = 0.125, 0.125001, 1e-6
for _ in range(8):
    z = 2 * z - floor(2 * z)
    other = 2 * other - floor(2 * other)
gap = abs(z - other)
assert isclose(gap, 2**8 * initial_gap, rel_tol=1e-8)
initial_energy, decay_time, time = 0.5, 2.0, 4.0
energy = initial_energy * exp(-time / decay_time)
half_time = decay_time * log(2)
assert isclose(initial_energy * exp(-half_time / decay_time), 0.25)
print(f"separation after 8 updates: {gap:.8f}")
print(f"energy at 4 s m2/s2: {energy:.8f}")
print(f"half-life s: {half_time:.6f}")
