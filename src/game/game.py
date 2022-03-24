from importlib import resources
from typing import Sequence, Tuple

import math
import pygame
import numpy as np

from .image import load_image
from ..utils.units import mph_to_ftpm
from ..enums import BurnStatus, GameStatus
from .sprites import Fire, FireLine, Terrain


class Game():
    '''
    Class that controls the game. This class will initalize the game and allow for
    terrain, fire, and other sprites to be rendered and interact.
    '''
    def __init__(self,
                 screen_size: int,
                 headless: bool = False,
                 show_wind_magnitude: bool = False,
                 show_wind_direction: bool = False,
                 mw_speed_min: float = 0.0,
                 mw_speed_max: float = mph_to_ftpm(150.0),
                 dw_deg_min: float = 0.0,
                 dw_deg_max: float = 360.0) -> None:
        '''
        Initalize the class by creating the game display and background.

        Arguments:
            screen_size: The (n,n) size of the game screen/display.
            headless: Flag to run in a headless state.
        '''
        self.screen_size = screen_size
        self.show_wind_magnitude = show_wind_magnitude
        self.show_wind_direction = show_wind_direction
        self.mw_speed_min = mw_speed_min
        self.mw_speed_max = mw_speed_max
        self.dw_deg_min = dw_deg_min
        self.dw_deg_max = dw_deg_max

        self.headless = headless

        if not self.headless:
            pygame.init()
            self.screen = pygame.display.set_mode((screen_size, screen_size))
            pygame.display.set_caption('Rothermel 2D Simulator')
            with resources.path('assets.icons', 'fireline_logo.png') as path:
                fireline_logo_path = path
            pygame.display.set_icon(load_image(fireline_logo_path))

        # Create the background so it doesn't have to be recreated every update
        if self.headless:
            self.background = None
        else:
            self.background = pygame.Surface(self.screen.get_size())
            self.background = self.background.convert()
            self.background.fill((0, 0, 0))

        # Map to track which pixels are on fire or have burned
        self.fire_map = np.full((screen_size, screen_size), BurnStatus.UNBURNED)

    def _toggle_wind_magnitude_display(self):
        '''
        Toggle display of wind MAGNITUDE over the main screen.
        '''
        self.show_wind_magnitude = not self.show_wind_magnitude
        if self.show_wind_magnitude is False:
            print('Wind Magnitude OFF')
        else:
            print('Wind Magnitude ON')
        return

    def _toggle_wind_direction_display(self):
        '''
        Toggle display of wind DIRECTION over the main screen.
        '''
        self.show_wind_direction = not self.show_wind_direction
        if self.show_wind_direction is False:
            print('Wind Direction OFF')
        else:
            print('Wind Direction ON')
        return

    def _disable_wind_magnitude_display(self):
        '''
        Toggle display of wind DIRECTION over the main screen.
        '''
        self.show_wind_magnitude = False

    def _disable_wind_direction_display(self):
        '''
        Toggle display of wind DIRECTION over the main screen.
        '''
        self.show_wind_direction = False

    def _get_wind_direction_color(self, direction: float) -> Tuple[int, int, int]:
        '''
        Get the color and intensity representing direction based on wind direction.

        0/360: Black, 90: Red, 180: White, Blue: 270

        Returns tuple of RGBa where a is alpha channel or transparency of the color

        Arguments:
            direction: Float value of the angle 0-360.
            ws_min: Minimum wind speed.
            ws_max: Maximum wind speed.
        '''
        north_min = 0.0
        north_max = 360.0
        east = 90.0
        south = 180.0
        west = 270.0

        colorRGB = (255.0, 255.0, 255.0)  # Default white

        # North to East, Red to Green
        if direction >= north_min and direction < east:
            angleRange = (east - north_min)

            # Red
            redMin = 255.0
            redMax = 128.0
            redRange = (redMax - redMin)  # 255 - 128 red range from north to east
            red = (((direction - north_min) * redRange) / angleRange) + redMin

            # Green
            greenMin = 0.0
            greenMax = 255.0
            greenRange = (greenMax - greenMin)  # 0 - 255 red range from north to east
            green = (((direction - north_min) * greenRange) / angleRange) + greenMin

            colorRGB = (red, green, 0.0)

        # East to South, Green to Teal
        if direction >= east and direction < south:
            angleRange = (south - east)

            # Red
            redMin = 128.0
            redMax = 0.0
            redRange = (redMax - redMin)  # 128 - 0 red range from east to south
            red = (((direction - east) * redRange) / angleRange) + redMin

            # Blue
            blueMin = 0
            blueMax = 255
            blueRange = (blueMax - blueMin)  # 0 - 255 blue range from east to south
            blue = (((direction - east) * blueRange) / angleRange) + blueMin

            colorRGB = (red, 255, blue)

        # South to West, Teal to Purple
        if direction >= south and direction < west:
            angleRange = (west - south)

            # Red
            redMin = 0
            redMax = 128
            redRange = (redMax - redMin)  # 0 - 128 red range from south to west
            red = (((direction - south) * redRange) / angleRange) + redMin

            # Green
            greenMin = 255
            greenMax = 0
            greenRange = (greenMax - greenMin)  # 0 - 255 green range from south to west
            green = (((direction - south) * greenRange) / angleRange) + greenMin

            colorRGB = (red, green, 255)

        # West to North, Purple to Red
        if direction <= north_max and direction >= west:
            angleRange = (north_max - west)

            # Red
            redMin = 128.0
            redMax = 255.0
            redRange = (redMax - redMin)  # 128 - 255 red range from east to south
            red = (((direction - west) * redRange) / angleRange) + redMin

            # Blue
            blueMin = 0
            blueMax = 255
            blueRange = (blueMax - blueMin)  # 0 - 255 blue range from east to south
            blue = (((direction - west) * blueRange) / angleRange) + blueMin

            colorRGB = (red, 0, blue)

        floorColorRGB = (
            int(math.floor(colorRGB[0])),
            int(math.floor(colorRGB[1])),
            int(math.floor(colorRGB[2])),
        )
        return floorColorRGB

    def _get_wind_mag_surf(self, wind_magnitude_map: Sequence[Sequence[float]]) -> \
            pygame.Surface:
        '''
        Compute the wind magnitude surface for display.

        Arguments:
            wind_magnitude_map: The map/array containing wind magnitudes at each pixel
                                location

        Returns:
            The PyGame Surface for the wind magnitude
        '''
        wind_mag_surf = pygame.Surface(self.screen.get_size())
        for y_idx, y in enumerate(wind_magnitude_map):
            for x_idx, x in enumerate(y):
                w_mag = x
                wind_speed_range = (self.mw_speed_max - self.mw_speed_min)
                color_grad = (255 - 0)
                color_mag = int(((
                    (w_mag - self.mw_speed_min) * color_grad) / wind_speed_range) + 0)
                wind_mag_surf.set_at((x_idx, y_idx), pygame.Color(0, color_mag, 0))
        return wind_mag_surf

    def _get_wind_dir_surf(self, wind_direction_map: Sequence[Sequence[float]]) -> \
            pygame.Surface:
        '''
        Compute the wind direction surface for display.

        Arguments:
            wind_direction_map: The map/array containing wind directions at each pixel
                                location

        Returns:
            The PyGame Surface for the wind direction
        '''
        wind_dir_surf = pygame.Surface(self.screen.get_size())
        for y_idx, y in enumerate(wind_direction_map):
            for x_idx, x in enumerate(y):
                w_dir = x
                color = self._get_wind_direction_color(w_dir)
                pyColor = pygame.Color(color[0], color[1], color[2], a=0.75)
                wind_dir_surf.set_at((x_idx, y_idx), pyColor)

        return wind_dir_surf

    def update(self, terrain: Terrain, fire_sprites: Sequence[Fire],
               fireline_sprites: Sequence[FireLine],
               wind_magnitude_map: Sequence[Sequence[float]],
               wind_direction_map: Sequence[Sequence[float]]) -> bool:
        '''
        Update the game display using the provided terrain, sprites, and
        environment data. Most of the logic for the game is handled within
        each sprite/manager, so this is mostly just calls to update everything.

        Arguments:
            terrain: The Terrain class that comprises the burnable area.
            fire_sprites: A list of all Fire sprites that are actively burning.
            fireline_sprites: A list of all FireLine sprites that are dug.
            wind_magnitude_map: The map/array containing wind magnitudes at each pixel
                                location
            wind_direction_map: The map/array containing wind directions at each pixel
                                location
        '''
        status = GameStatus.RUNNING

        if not self.headless:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    status = GameStatus.QUIT

                if event.type == pygame.KEYDOWN:
                    keys = pygame.key.get_pressed()
                    if keys[pygame.K_m] is True:
                        self._disable_wind_direction_display()
                        self._toggle_wind_magnitude_display()

                    if keys[pygame.K_n] is True:
                        self._disable_wind_magnitude_display()
                        self._toggle_wind_direction_display()

        # Create a layered group so that the fire appears on top
        fire_sprites_group = pygame.sprite.LayeredUpdates(fire_sprites, fireline_sprites)
        all_sprites = pygame.sprite.LayeredUpdates(fire_sprites_group, terrain)

        # Update and draw the sprites
        if not self.headless:
            for sprite in all_sprites.sprites():
                self.screen.blit(self.background, sprite.rect, sprite.rect)

        fire_sprites_group.update()
        terrain.update(self.fire_map)
        if not self.headless:
            all_sprites.draw(self.screen)

            if self.show_wind_magnitude is True:
                wind_mag_surf = self._get_wind_mag_surf(wind_magnitude_map)
                self.screen.blit(wind_mag_surf, (0, 0))

            if self.show_wind_direction is True:
                wind_dir_surf = self._get_wind_dir_surf(wind_direction_map)
                self.screen.blit(wind_dir_surf, (0, 0))

        if not self.headless:
            pygame.display.flip()

        return status
