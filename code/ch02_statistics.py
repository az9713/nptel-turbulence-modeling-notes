"""Finite sampling, correlation and Cartesian tensor checks."""

from math import isclose, sqrt

sample = [5, 6, 1, 3, 4, 6, 1, 6, 4, 1]
mean = sum(sample) / len(sample)
residual = sum(value - mean for value in sample)
assert isclose(residual, 0.0, abs_tol=1e-12)
die_mean = sum(range(1, 7)) / 6
die_variance = sum((value - die_mean) ** 2 for value in range(1, 7)) / 6
assert isclose(die_variance, 35 / 12)
n, correlation = 100, 0.9
factor = 1 + 2 * sum((1 - lag / n) * correlation**lag for lag in range(1, n))
effective = n / factor
sd_mean = sqrt(factor / n)
data = [-1.0, 0.0, 1.0]
denominator = sum(value**2 for value in data)
lag_product = data[0] * data[2]
acf = lag_product / denominator
mixed_normalization = lag_product / (denominator / len(data))
assert acf == -0.5 and mixed_normalization == -1.5


def matmul(left, right):
    return [
        [sum(left[i][k] * right[k][j] for k in range(3)) for j in range(3)]
        for i in range(3)
    ]


def transpose(matrix):
    return [list(row) for row in zip(*matrix)]


cov = [[4.0, -1.0, 0.0], [-1.0, 1.0, 0.0], [0.0, 0.0, 0.25]]
rotation = [[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]]
rotated = matmul(matmul(rotation, cov), transpose(rotation))
trace = sum(cov[i][i] for i in range(3))
assert isclose(sum(rotated[i][i] for i in range(3)), trace)
gradient = [[0.0, 2.0, 0.0], [0.0, 0.0, 3.0], [4.0, 0.0, 0.0]]
curl = [
    gradient[2][1] - gradient[1][2],
    gradient[0][2] - gradient[2][0],
    gradient[1][0] - gradient[0][1],
]
assert curl == [-3.0, -4.0, -2.0]
assert sum(gradient[i][i] for i in range(3)) == 0
print(f"sample mean: {mean:.6f}")
print(f"sample-centered residual (floating point): {residual:.3e}")
print(f"fair-die mean, variance: {die_mean:.6f}, {die_variance:.6f}")
print(f"correlation factor: {factor:.8f}")
print(f"effective samples: {effective:.6f}")
print(f"unit-variance mean standard deviation: {sd_mean:.6f}")
print(
    f"lag-2 coefficient, mixed normalization: {acf:.1f}, "
    f"{mixed_normalization:.1f}"
)
print("rotated covariance:", rotated)
print(f"covariance trace: {trace:.6f}")
print("linear-field curl:", curl)
