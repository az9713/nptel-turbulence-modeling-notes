"""Advection amplification, statistical partition and hybrid-interface \
algebra."""

from itertools import product
from math import cos, pi, sin, sqrt, tanh

n, m, cfl = 64, 3, 0.5
h = 2 * pi / n
theta = 2 * pi * m / n
steps = int(n / cfl)
central_gain = sqrt(1 + (cfl * sin(theta)) ** 2)
upwind_gain = sqrt((1 - cfl + cfl * cos(theta)) ** 2 + (cfl * sin(theta)) ** 2)
print(
    f"forward Euler centered/upwind amplitude after one crossing: "
    f"{central_gain ** steps:.8f}, {upwind_gain ** steps:.8f}"
)
print(
    f"leading forward-Euler upwind numerical viscosity at unit speed: "
    f"{h * (1 - cfl) / 2:.8f}"
)
print("centered-space Crank-Nicolson linear-advection amplitude: 1.00000000")

shear, dy, fluct_variance = 100.0, 0.002, 0.04
mean_filter_stress = shear**2 * dy**2 / 12
resolved_k = fluct_variance / 2
mean_q = mean_filter_stress / 2
true_filtered_k = resolved_k
corrected = resolved_k + mean_q - mean_filter_stress / 2
print(
    f"filtered turbulence energy, naive resolved+SGS, corrected: "
    f"{true_filtered_k:.10f}, {resolved_k + mean_q:.10f}, "
    f"{corrected:.10f}"
)

# Eight equiprobable signs exactly realize this one-point target covariance.
rows = []
for a, b, c in product((-1.0, 1.0), repeat=3):
    rows.append((0.5 * a, -0.16 * a + sqrt(0.09 - 0.16**2) * b, 0.2 * c))
means = [sum(row[i] for row in rows) / len(rows) for i in range(3)]
cov = [
    [sum(row[i] * row[j] for row in rows) / len(rows) for j in range(3)]
    for i in range(3)
]
print(f"synthetic one-point fluctuation mean: {means}")
print(f"synthetic one-point covariance: {cov}")
print(
    f"synthetic one-point energy: {sum((cov[i][i] for i in range(3))) / 2:.8f}"
)
assert abs(cov[0][1] + 0.08) < 1e-14 and abs(cov[1][1] - 0.09) < 1e-14
print(
    f"energy-feedback multiplier for one illustrative partition "
    f".12+.07: {(0.12 + 0.07) / 0.12:.8f}"
)

cd = 0.65
for d, grid, fd in (
    (0.01, 0.02, 1.0),
    (0.01, 0.005, 1.0),
    (0.01, 0.005, 0.0),
    (0.05, 0.005, 1.0),
):
    des = min(d, cd * grid)
    delayed = d - fd * max(0.0, d - cd * grid)
    print(
        f"wall distance={d}, grid length={grid}, fd={fd}: DES "
        f"length={des:.8f}, shielded length={delayed:.8f}"
    )
for rd in (0.01, 0.1, 1.0):
    fd = 1 - tanh((8 * rd) ** 3)
    print(f"shielding rd={rd}: fd={fd:.10f}")
for label, power in (
    ("WM illustrative", 1.0),
    ("WR high-Re plate", 13 / 7),
    ("homogeneous DNS", 9 / 4),
    ("uniform-cross-plane plate DNS", 37 / 14),
):
    print(
        f"tenfold Reynolds ratio, {label}: point multiplier={10 ** power:.8f}"
    )
