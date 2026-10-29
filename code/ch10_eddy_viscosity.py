"""Tensor closure and bare mixing-length checks, not a fitted RANS solver."""

from math import asinh, log, sqrt

S, k = 100.0, 0.19
measured_diag = [0.25, 0.09, 0.04]
measured_shear = -0.08  # Stipulated covariance, not experimental data.
fitted_nu = -measured_shear / S
print(f"eddy viscosity fitting stipulated shear m2/s: {fitted_nu:.8f}")
print("stipulated normal variances:", measured_diag)
for nu_t in (fitted_nu, 0.002):
    d = 2 * k / 3
    eig = [d - nu_t * S, d, d + nu_t * S]
    print(
        f"nu_t={nu_t:.6f}: predicted diagonal={d:.8f}, "
        f"eigenvalues={','.join((f'{x:.8f}' for x in eig))}, "
        f"production={nu_t * S * S:.6f}"
    )

# U=(S*y,0,0), nu_t=nu0*(1+x*x/L**2).
nu0, x, L = 0.001, 0.5, 1.0
missing_normal_force = 2 * nu0 * x * S / L**2
print(
    f"variable-viscosity missing normal acceleration m/s2: "
    f"{missing_normal_force:.8f}"
)
print(f"curl of missing acceleration 1/s2: {2 * nu0 * S / L ** 2:.8f}")

kappa, B = 0.41, 5.2
for s in (1.0, 5.0, 30.0, 100.0):
    z = 2 * kappa * s
    g = 2 / (1 + sqrt(1 + z * z))
    velocity = (asinh(z) - z / (1 + sqrt(1 + z * z))) / kappa
    residual = g + (kappa * s) ** 2 * g * g - 1
    assert abs(residual) < 1e-12
    print(
        f"bare mixing y+={s:.0f}: gradient={g:.8f}, U+={velocity:.8f}, "
        f"illustrative log U+={log(s) / kappa + B:.8f}"
    )
print(f"bare mixing asymptotic intercept: {(log(4 * kappa) - 1) / kappa:.8f}")
epsilon = 0.5
print(f"k/epsilon time s: {k / epsilon:.8f}")
print(f"k^(3/2)/epsilon length m: {k ** 1.5 / epsilon:.8f}")
print(f"eddy viscosity divided by C_mu m2/s: {k * k / epsilon:.8f}")
