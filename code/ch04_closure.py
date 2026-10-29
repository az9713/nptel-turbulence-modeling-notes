"""Finite covariance, momentum-flux, and centering checks; no external \
inputs."""

from math import cos, isclose, pi, sin, sqrt

states = [
    (2.0, -1.0, 0.5),
    (0.0, 1.0, -0.5),
    (-2.0, 1.0, 0.5),
    (0.0, -1.0, -0.5),
]
mean = [sum(row[i] for row in states) / 4 for i in range(3)]
assert all(isclose(value, 0.0, abs_tol=1e-14) for value in mean)
cov = [
    [sum(row[i] * row[j] for row in states) / 4 for j in range(3)]
    for i in range(3)
]
assert all(cov[i][j] == cov[j][i] for i in range(3) for j in range(3))
assert cov[0][1] ** 2 <= cov[0][0] * cov[1][1]
rho, nu, half_height, gradient = 1.2, 1.5e-5, 0.02, 10.0
mu = rho * nu
y = half_height / 2
shear = 100.0
total = gradient * (half_height - y)
molecular = mu * shear
r12 = -(total - molecular) / rho
assert isclose(molecular - rho * r12, total, abs_tol=1e-14)
production = -r12 * shear

amp, wave, x, pos_y = 1.3, 2.0, 0.21, 0.37
nonlinear = []
for phase in [0.0, pi / 2, pi, 3 * pi / 2]:
    angle_x, angle_y = wave * x + phase, wave * pos_y
    u = amp * sin(angle_x) * cos(angle_y)
    v = -amp * cos(angle_x) * sin(angle_y)
    ux = amp * wave * cos(angle_x) * cos(angle_y)
    uy = -amp * wave * sin(angle_x) * sin(angle_y)
    vx = amp * wave * sin(angle_x) * sin(angle_y)
    vy = -amp * wave * cos(angle_x) * cos(angle_y)
    assert isclose(ux + vy, 0.0, abs_tol=1e-14)
    nonlinear.append([u * ux + v * uy, u * vx + v * vy])
avg_n = [sum(row[i] for row in nonlinear) / 4 for i in range(2)]
div_r = [0.0, amp**2 * wave * sin(wave * pos_y) * cos(wave * pos_y)]
assert all(isclose(a, b, abs_tol=1e-14) for a, b in zip(avg_n, div_r))
centered = [sum(row[i] - avg_n[i] for row in nonlinear) / 4 for i in range(2)]
assert all(isclose(value, 0.0, abs_tol=1e-14) for value in centered)
print("mean velocity:", mean)
print("covariance:", cov)
print(f"correlation c12: {cov[0][1] / sqrt(cov[0][0] * cov[1][1]):.6f}")
print(f"wall shear Pa: {gradient * half_height:.6f}")
print(f"local total, molecular Pa: {total:.6f}, {molecular:.6f}")
print(f"required R12 m2/s2: {r12:.8f}")
print(f"local TKE production m2/s3: {production:.6f}")
print("mean nonlinear acceleration:", [round(value, 8) for value in avg_n])
print("covariance divergence:", [round(value, 8) for value in div_r])
print("centered mean:", [round(value, 8) + 0.0 for value in centered])
