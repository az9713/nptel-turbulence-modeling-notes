"""Restricted scale, mode-resolution, domain and sampling checks; no \
turbulent DNS."""

from math import cos, exp, log, pi, sin, sqrt

nu, eps, speed, length = 1.5e-5, 0.5, 1.0, 0.2
eta = (nu**3 / eps) ** 0.25
tau = sqrt(nu / eps)
ueta = (nu * eps) ** 0.25
re = speed * length / nu
ce = eps * length / speed**3
print(
    f"Kolmogorov length m, time s, speed m/s: {eta:.9f}, {tau:.9f}, {ueta:.9f}"
)
print(f"microscale Reynolds number: {ueta * eta / nu:.8f}")
print(
    f"integral Reynolds number and dissipation coefficient: {re:.8f}, {ce:.8f}"
)
assert abs(eta / length - ce ** (-0.25) * re ** (-0.75)) < 1e-15
for reynolds in (1e4, 1e6):
    n = reynolds**0.75
    print(
        f"Re={reynolds:.0f}: points per direction={n:.4f}, "
        f"total={n ** 3:.8e}, four-field bytes={32 * n ** 3:.8e}"
    )
print(f"unit speed/unit length with stipulated air viscosity: Re={1 / nu:.8f}")
dx, dy, dz = 8 * eta, 0.5 * eta, 0.5 * eta
print(
    f"anisotropic grid geometric criterion and maximum ratio: "
    f"{(dx * dy * dz) ** (1 / 3) / (pi * eta):.8f}, "
    f"{max(dx, dy, dz) / eta:.8f}"
)
print(
    f"eta inflation if epsilon is underestimated by factor16: {16 ** 0.25:.8f}"
)

# Exact heat-equation Fourier mode versus a centered spatial Laplacian.
viscosity, wave, time = 0.01, 6, 1.0
exact = exp(-viscosity * wave**2 * time)
errors = []
for n in (32, 64, 128):
    h = 2 * pi / n
    discrete_wave_squared = 4 * sin(wave * h / 2) ** 2 / h**2
    semi_discrete = exp(-viscosity * discrete_wave_squared * time)
    errors.append(abs(semi_discrete - exact))
    print(
        f"diffusing mode N={n}: amplitude={semi_discrete:.8f}, "
        f"error={errors[-1]:.8e}"
    )
print(f"last spatial refinement ratio: {errors[-2] / errors[-1]:.8f}")
assert 3.9 < errors[-2] / errors[-1] < 4.1


# Periodized exponential covariance: normalized and positive definite.
def periodic_corr(separation, box, corr_length):
    return (
        exp(-separation / corr_length) + exp(-(box - separation) / corr_length)
    ) / (1 + exp(-box / corr_length))


for box in (4.0, 12.0):
    print(
        f"periodic covariance box/correlation length={box:.0f}: "
        f"half-box correlation={periodic_corr(box / 2, box, 1):.8f}"
    )

# Exact variance of the average for stationary unit-variance AR(1) samples.
n, rho = 1000, 0.99
factor = 1 + 2 * sum((1 - j / n) * rho**j for j in range(1, n))
print(
    f"1000 correlated samples: effective count={n / factor:.8f}, mean "
    f"standard deviation={sqrt(factor / n):.8f}"
)
print(f"exponential correlation below .05 requires lag/tc={-log(0.05):.8f}")

# A prescribed divergence-free periodic perturbation, not grid noise.
x, y, amplitude = 0.4, 0.7, 0.1
du_dx = amplitude * cos(x) * cos(y)
dv_dy = -amplitude * cos(x) * cos(y)
print(f"analytic startup perturbation divergence: {du_dx + dv_dy:.3e}")
