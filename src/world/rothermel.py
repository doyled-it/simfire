from math import atan2, cos, exp, radians
from numba import vectorize
from ..config import device


@vectorize([('float32(float32,float32,float32,float32,float32,float32,'
             'float32,float32,float32,float32,float32,float32,'
             'float32,float32,float32,float32,float32)')],
           target=device)
def compute_rate_of_spread(loc_x: float, loc_y: float, loc_z: float, new_loc_x: float,
                           new_loc_y: float, new_loc_z: float, w_0: float, delta: float,
                           M_x: float, sigma: float, h: float, S_T: float, S_e: float,
                           p_p: float, M_f: float, U: float, U_dir: float) -> float:
    # Mineral Damping Coefficient
    eta_S = min(0.174 * S_e**-0.19, 1)
    # Moisture Damping Coefficient
    r_M = min(M_f / M_x, 1)
    eta_M = 1 - 2.59 * r_M + 5.11 * r_M**2 - 3.52 * r_M**3
    # Net Fuel Load (lb/ft^2)
    w_n = w_0 * (1 - S_T)
    # Oven-dry Bulk Density (lb/ft^3)
    p_b = w_0 / delta
    # Packing Ratio
    B = p_b / p_p
    # Optimum Packing Ratio
    B_op = 3.348 * sigma**-0.8189
    # Maximum Reaction Velocity (1/min)
    gamma_prime_max = sigma**1.5 / (495 + 0.0594 * sigma**1.5)
    A = 133 * sigma**-0.7913
    # Optimum Reaction Velocity (1/min)
    gamma_prime = gamma_prime_max * (B / B_op)**A * exp(A * (1 - B / B_op))
    # Reaction Intensity (BTU/ft^2-min)
    I_R = gamma_prime * w_n * h * eta_M * eta_S
    # Propagating Flux Ratio
    xi = exp((0.792 + 0.681 * sigma**0.5) * (B + 0.1)) / (192 + 0.25 * sigma)

    # Wind Factor
    c = 7.47 * exp(-0.133 * sigma**0.55)
    b = 0.02526 * sigma**0.54
    e = 0.715 * exp(-3.59e-4 * sigma)
    # Need to find wind component in direction of travel
    # Switch order of y-component subtraction since image y coordintates
    # increase from top to bottom
    angle_of_travel = atan2(loc_y - new_loc_y, new_loc_x - loc_x)
    # Subtract 90 degrees because this angle is North-oriented
    wind_angle_radians = radians(90 - U_dir)
    wind_along_angle_of_travel = U * \
                                 cos(wind_angle_radians - angle_of_travel)
    # This is the wind speed in in this direction
    U = wind_along_angle_of_travel
    # Negative wind leads to trouble with calculation and doesn't
    # physically make sense
    U = max(U, 0)
    phi_w = c * U**b * (B / B_op)**-e

    # Slope Factor
    # Phi is the slope between the two locations (i.e. the change in elevation).
    # We can approximate this using the z coordinates for each point
    # This equation normally has tan(phi)**2, but we can substitute
    # tan(phi) = (new_loc.z-old_loc.z)
    phi_s = 5.275 * B**-0.3 * (new_loc_z - loc_z)**2

    # Effective Heating Number
    epsilon = exp(-138 / sigma)
    # Heat of Preignition (BTU/lb)
    Q_ig = 250 + 1116 * M_f

    # Rate of Spread (ft/min)
    R = (I_R * xi * (1 + phi_w + phi_s)) / (p_b * epsilon * Q_ig)

    # Take the minimum with 0 because a fire cannot put itself out
    R = max(R, 0)

    return R
