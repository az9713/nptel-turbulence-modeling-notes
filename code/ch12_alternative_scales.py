"""Calibration and restricted time-scale checks, not a spatial RANS solver."""

from math import sqrt

Cmu, C1, C2, sigma_eps, kappa = 0.09, 1.44, 1.92, 1.3, 0.41
inferred_C1 = C2 - kappa * kappa / (sigma_eps * sqrt(Cmu))
implied_kappa = sqrt(sigma_eps * sqrt(Cmu) * (C2 - C1))
print(f"log-balance C_epsilon1 with kappa0.41: {inferred_C1:.8f}")
print(f"kappa implied by baseline coefficient set: {implied_kappa:.8f}")

eta0, beta_rng = 4.38, 0.012
for eta in (0.0, 2.0, eta0, 8.0):
    correction = eta * (1 - eta / eta0) / (1 + beta_rng * eta**3)
    print(
        f"RNG eta={eta:.2f}: correction={correction:.8f}, effective "
        f"C1={1.42 - correction:.8f}"
    )

k, CD, Cnu, S = 0.19, 0.09, 1.0, 10.0
for length in (0.01, 0.02):
    epsilon = CD * k**1.5 / length
    viscosity = Cnu * length * sqrt(k)
    equilibrium = (Cnu / CD) * (length * S) ** 2
    print(
        f"one-equation length={length:.3f} m: epsilon={epsilon:.8f}, "
        f"nu_t={viscosity:.8f}, prescribed-shear equilibrium "
        f"k={equilibrium:.8f}"
    )

beta_star, beta_wilcox, gamma = 0.09, 3 / 40, 5 / 9
sigma_w = 0.5  # Multiplier convention for the 1988 model.
print(
    f"Wilcox1988 implied kappa: "
    f"{sqrt(
        (beta_wilcox / beta_star - gamma) * sqrt(beta_star) / sigma_w
    ):.8f}"
)
print(
    f"transformed baseline source coefficients: gamma={C1 - 1:.8f}, "
    f"beta={(C2 - 1) * beta_star:.8f}"
)

# Pointwise homogeneous source transformation, no spatial gradients.
epsilon, production = 0.5, 0.8
omega = epsilon / (beta_star * k)
dk = production - epsilon
de = C1 * epsilon / k * production - C2 * epsilon**2 / k
quotient = de / (beta_star * k) - omega * dk / k
transformed = (C1 - 1) * omega * production / k - (
    C2 - 1
) * beta_star * omega**2
print(f"omega quotient source 1/s2: {quotient:.8f}")
print(f"transformed source agreement: {abs(quotient - transformed):.3e}")
assert abs(quotient - transformed) < 1e-12

# Spatial product-rule check in a positive interior, with varying diffusivity.
# These are manufactured scalar fields, not a solution of the RANS system.
x = 0.3
kx, ox = 1 + 0.2 * x + 0.1 * x * x, 2 + 0.4 * x + 0.3 * x * x
kp, kpp = 0.2 + 0.2 * x, 0.2
op, opp = 0.4 + 0.6 * x, 0.6
De, Dk, Dep, Dkp = 0.5 + 0.1 * x, 0.4 + 0.2 * x, 0.1, 0.2
product_diff = Dep * (kp * ox + kx * op) + De * (
    kpp * ox + 2 * kp * op + kx * opp
)
k_diff = Dkp * kp + Dk * kpp
direct = product_diff / kx - ox * k_diff / kx
omega_diff = Dep * op + De * opp
cross = 2 * De * kp * op / kx
unequal = ox * ((Dep - Dkp) * kp + (De - Dk) * kpp) / kx
print(
    f"spatial quotient diffusion: direct={direct:.8f}, "
    f"expanded={omega_diff + cross + unequal:.8f}"
)
print(f"spatial omitted terms: cross={cross:.8f}, unequal={unequal:.8f}")
assert abs(direct - (omega_diff + cross + unequal)) < 1e-14

# Near-wall singular reference and a deliberately excessive explicit step.
nu = 1.5e-5
for distance in (1e-5, 2e-5):
    wall_omega = 6 * nu / (beta_wilcox * distance**2)
    positive_step = 1 / (beta_wilcox * wall_omega)
    print(
        f"distance={distance * 1000000.0:.0f} micrometres: "
        f"omega={wall_omega:.6e}, explicit-sink positivity limit "
        f"s={positive_step:.6e}"
    )
wall_omega = 6 * nu / (beta_wilcox * 1e-10)
dt = 2e-6
euler = wall_omega * (1 - beta_wilcox * wall_omega * dt)
exact = wall_omega / (1 + beta_wilcox * wall_omega * dt)
print(
    f"isolated sink after2microseconds: Euler={euler:.6e}, exact={exact:.6e}"
)
assert euler < 0 < exact
