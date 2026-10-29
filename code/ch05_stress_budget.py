"""Exact algebraic and kinematic budget checks, not a complete flow solver."""

from math import cos, isclose, pi, sin

cov = [[4.0, -1.0, 0.0], [-1.0, 1.0, 0.0], [0.0, 0.0, 0.25]]
mean_gradient = [[0.0, 2.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
production = [
    [
        -sum(
            cov[j][ell] * mean_gradient[i][ell]
            + cov[i][ell] * mean_gradient[j][ell]
            for ell in range(3)
        )
        for j in range(3)
    ]
    for i in range(3)
]
tke_production = sum(production[i][i] for i in range(3)) / 2
assert tke_production == 2.0
redistribution = [-2.0, 1.0, 1.0]
assert sum(redistribution) == 0.0
after = [
    value + 0.5 * rate for value, rate in zip([4.0, 1.0, 1.0], redistribution)
]
assert sum(after) == 6.0
nu, amp, wave, x = 0.01, 1.0, 1.0, 0.2


def dissipation(y):
    pseudo, physical = 0.0, 0.0
    for phase in [0.0, pi / 2, pi, 3 * pi / 2]:
        xx, yy = wave * x + phase, wave * y
        gradient = [
            [amp * wave * cos(xx) * cos(yy), -amp * wave * sin(xx) * sin(yy)],
            [amp * wave * sin(xx) * sin(yy), -amp * wave * cos(xx) * cos(yy)],
        ]
        assert isclose(gradient[0][0] + gradient[1][1], 0.0, abs_tol=1e-14)
        pseudo += nu * sum(value**2 for row in gradient for value in row) / 4
        physical += (
            2
            * nu
            * sum(
                ((gradient[i][j] + gradient[j][i]) / 2) ** 2
                for i in range(2)
                for j in range(2)
            )
            / 4
        )
    correction = nu * amp**2 * wave**2 * cos(2 * wave * y)
    assert isclose(physical, pseudo + correction, abs_tol=1e-14)
    return pseudo, physical, correction


print("production tensor:", production)
print(f"TKE production m2/s3: {tke_production:.6f}")
print("redistribution-only diagonal after 0.5 s:", after)
for y in [0.0, pi / 2]:
    pseudo, physical, correction = dissipation(y)
    print(
        f"y={y:.6f}: pseudo={pseudo:.6f}, physical={physical:.6f}, "
        f"correction={correction:.6f}"
    )
period_mean = sum(dissipation(2 * pi * i / 400)[1] for i in range(400)) / 400
assert isclose(period_mean, nu * amp**2 * wave**2, abs_tol=1e-14)
print(f"period-mean physical dissipation m2/s3: {period_mean:.6f}")
