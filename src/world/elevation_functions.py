from typing import Callable, Tuple

from math import exp
import numpy as np

ElevationFn = Callable[[float, float], float]


def gaussian(amplitude: int, mu_x: int, mu_y: int, sigma_x: int,
             sigma_y: int) -> ElevationFn:
    '''
    Create a callable that returns the value of a Gaussian centered at (mu_x, mu_y) with
    variances given by sigma_x and sigma_y. The input A will modify the final amplitude.

    Arguments:
        amplitude: The Gaussian amplitude
        mu_x: The mean/center in the x direction
        mu_y: The mean/center in the y direction
        sigma_x: The variance in the x direction
        sigma_y: The variance in the y direction

    Returns:
        A callabe that computes z values for (x, y) inputs
    '''
    def fn(x: float, y: float) -> float:
        '''
        Return the function value at the specified point.

        Arguments:
            x: The input x coordinate
            y: The input y coordinate

        Returns:
            z: The output z coordinate computed by the function
        '''

        exp_term = ((x - mu_x)**2 / (4 * sigma_x**2)) + ((y - mu_y)**2 / (4 * sigma_y**2))
        z = amplitude * exp(-exp_term)
        return z

    return fn


class PerlinNoise2D():
    def __init__(self, amplitude: float, shape: Tuple[int, int], res: Tuple[int,
                                                                            int]) -> None:
        '''
        Create a class to compute perlin noise for given input parameters.

        Arguments:
            A: The amplitude to scale the noise by
            shape: The output shape of the data
            res: The resolution of the noise

        Returns:
            None
        '''
        self.amplitude = amplitude
        self.shape = shape
        self.res = res
        self.terrain_map = None

    def precompute(self) -> None:
        '''
        Precompute the noise at each (x, y) location for faster use later.

        Arguments:
            None

        Returns:
            None
        '''
        res = self.res
        shape = self.shape

        def f(t):
            return 6 * t**5 - 15 * t**4 + 10 * t**3

        delta = (res[0] / shape[0], res[1] / shape[1])
        d = (shape[0] // res[0], shape[1] // res[1])
        grid = np.mgrid[0:res[0]:delta[0], 0:res[1]:delta[1]].transpose(1, 2, 0) % 1
        # Gradients
        angles = 2 * np.pi * np.random.rand(res[0] + 1, res[1] + 1)
        gradients = np.dstack((np.cos(angles), np.sin(angles)))
        g00 = gradients[0:-1, 0:-1].repeat(d[0], 0).repeat(d[1], 1)
        g10 = gradients[1:, 0:-1].repeat(d[0], 0).repeat(d[1], 1)
        g01 = gradients[0:-1, 1:].repeat(d[0], 0).repeat(d[1], 1)
        g11 = gradients[1:, 1:].repeat(d[0], 0).repeat(d[1], 1)
        # Ramps
        n00 = np.sum(grid * g00, 2)
        n10 = np.sum(np.dstack((grid[:, :, 0] - 1, grid[:, :, 1])) * g10, 2)
        n01 = np.sum(np.dstack((grid[:, :, 0], grid[:, :, 1] - 1)) * g01, 2)
        n11 = np.sum(np.dstack((grid[:, :, 0] - 1, grid[:, :, 1] - 1)) * g11, 2)
        # Interpolation
        t = f(grid)
        n0 = n00 * (1 - t[:, :, 0]) + t[:, :, 0] * n10
        n1 = n01 * (1 - t[:, :, 0]) + t[:, :, 0] * n11
        self.terrain_map = self.amplitude * np.sqrt(2) * (
            (1 - t[:, :, 1]) * n0 + t[:, :, 1] * n1)
        self.terrain_map = self.terrain_map + np.min(self.terrain_map)

    def fn(self, x: int, y: int) -> float:
        '''
        Wrapper function to retrieve the perlin noise values at input (x, y) coordinates.

        Arguments:
            x: The x coordinate to retrieve
            y: The y coordinate to retrieve

        Returns:
            The perlin noise value at the (x, y) coordinates
        '''
        if not isinstance(x, int):
            x = int(x)
        if not isinstance(y, int):
            y = int(y)
        return self.terrain_map[x, y]


def flat() -> ElevationFn:
    '''
    Create a callable that returns 0 for all elevations.

    Arguments:
        None

    Returns:
        A callable that computes z values for (x, y) inputs
    '''
    def fn(x: float, y: float) -> float:
        return 0

    return fn