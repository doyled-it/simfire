from typing import Sequence
from dataclasses import dataclass


@dataclass
class FuelParticle:
    '''
    Set default values here since the paper assumes they're constant. These
    could be changed, but for now it's easier to assume they're constant.
    '''
    # Low Heat Content (BTU/lb)
    h: float = 8000
    # Total Mineral Content
    S_T: float = 0.0555
    # Effective Mineral Content
    S_e: float = 0.01
    # Oven-dry Particle Density (lb/ft^3)
    p_p: float = 32


@dataclass
class Fuel:
    '''
    Class that describes the parameters of a fuel type
    '''
    # Oven-dry Fuel Load (lb/ft^2)
    w_0: float
    # Fuel bed depth (ft)
    delta: float
    # Dead fuel moisture of extinction
    M_x: float
    # Surface-area-to-volume ratio (ft^2/ft^3)
    sigma: float


@dataclass
class Environment:
    '''
    These parameters relate to the environment of the tile. For now we'll
    assume these values are constant over a small area.
    '''
    # Fuel Moisture (amount of water in fuel/vegetation)
    # 1-3% for SoCal, usually never more than 8% for SoCal
    M_f: float
    # Wind speed at midflame height (ft/min)
    U: Sequence[Sequence[float]]
    # Wind direction at midflame height (degrees)
    # 0 is North, 90 is East, 180 is South, 270 is West
    U_dir: float
