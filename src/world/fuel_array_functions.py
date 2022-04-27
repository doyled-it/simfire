from typing import Callable

from .parameters import Fuel
from ..utils.terrain import chaparral

FuelArrayFn = Callable[[float, float], Fuel]


def chaparral_fn(seed: int = None) -> FuelArrayFn:
    '''
    Return a callable that accepts (x, y) coordinates and returns a Fuel with
    Chaparral characterisitics at that coordinate. The w_0 parameter is slightly
    altered/jittered to allow for non-uniform terrains. Specifying a specific seed
    allows for re-createable random terrain.

    Arguments:
        seed: The seed to initialize the Fuel w_0 randomization

    Returns:
        A FuelArrayFn callable that accepts (x,y) coordinates and returns a FuelArray
    '''
    def fn(x: float, y: float) -> Fuel:
        '''
        Use the input coordinates to generate a FuelArray for the environment at that
        coordinate.

        Arguments:
            x: The input x coordinate
            y: The input y coorindate

        Returns:
            A Fuel
        '''
        fuel = chaparral(seed)

        return fuel

    return fn
