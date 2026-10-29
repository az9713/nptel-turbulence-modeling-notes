"""Force, power, and profile checks for explicit Newtonian branches."""
from math import isclose

mu, rho = 1.8e-5, 1.2
gap, plate_speed = .002, 2.
shear = mu * plate_speed / gap
strain = plate_speed / (2 * gap)
dissipation = 2 * mu * (strain**2 + strain**2)
wall_power = shear * plate_speed
integrated_loss = dissipation * gap
assert isclose(wall_power, integrated_loss)
half_height, pressure_gradient, length, width = .02, 10., 10., 1.


def profile(y):
    return pressure_gradient * y * (2 * half_height - y) / (2 * mu)


spacing = 2 * half_height / 4
points = [profile(i * spacing) for i in range(5)]
integral = spacing / 3 * (points[0] + 4 * points[1] + 2 * points[2]
                          + 4 * points[3] + points[4])
bulk = integral / (2 * half_height)
exact_bulk = pressure_gradient * half_height**2 / (3 * mu)
assert isclose(bulk, exact_bulk)
curvature = -pressure_gradient / mu
assert isclose(pressure_gradient + mu * curvature, 0., abs_tol=1e-12)
wall_shear = pressure_gradient * half_height
pressure_force = pressure_gradient * length * 2 * half_height * width
wall_force = 2 * wall_shear * length * width
assert isclose(pressure_force, wall_force)
gradient_for_target = 3 * mu * 10 / half_height**2
print(f'Couette shear Pa: {shear:.6f}')
print(f'Couette dissipation W/m3: {dissipation:.6f}')
print(f'wall input, integrated loss W/m2: {wall_power:.6f}, '
      f'{integrated_loss:.6f}')
print(f'Poiseuille bulk speed m/s: {bulk:.6f}')
print(f'Poiseuille center speed m/s: {profile(half_height):.6f}')
print(f'pressure force, wall force N: {pressure_force:.6f}, '
      f'{wall_force:.6f}')
print(f'laminar pressure gradient for target Pa/m: '
      f'{gradient_for_target:.6f}')
