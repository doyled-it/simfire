import yaml
import unittest
from pathlib import Path

from src.utils.units import mph_to_ftpm

from ..config import ConfigType, Config
from ...world.wind import WindController
from ...world.fuel_array_functions import chaparral_fn
from ...world.elevation_functions import PerlinNoise2D


class ConfigTypeTest(unittest.TestCase):
    def setUp(self) -> None:
        yaml_dict = {
            'level_0_a': 0,
            'level_0_b': {
                'level_1_a': 1,
                'level_1_b': {
                    'level_2_a': 2,
                    'level_2_b': 3,
                    'level_2_c': '(1, 2, 3)'
                }
            }
        }
        self.cfg_type = ConfigType(**yaml_dict)

    def test__init__(self) -> None:
        '''
        Test creating a nested ConfigType class
        '''
        msg = 'The nesting of dictionary attributes did not work correctly.'

        self.assertEqual(self.cfg_type.level_0_a, 0)
        self.assertEqual(self.cfg_type.level_0_b.level_1_a,
                         1,
                         msg=f'{msg} level_0_b.level_1_a should equal {1} when '
                         f'it is set to {self.cfg_type.level_0_b.level_1_a}')
        self.assertEqual(self.cfg_type.level_0_b.level_1_b.level_2_a,
                         2,
                         msg=f'{msg} level_0_b.level_1_b.level_2_a should equal {2} when '
                         f'it is set to {self.cfg_type.level_0_b.level_1_b.level_2_a}')
        self.assertEqual(self.cfg_type.level_0_b.level_1_b.level_2_b,
                         3,
                         msg=f'{msg} level_0_b.level_1_b.level_2_b should equal {3} when '
                         f'it is set to {self.cfg_type.level_0_b.level_1_b.level_2_b}')

    def test__type(self):
        '''
        Test typing a string of a tuple into a tuple
        '''
        self.assertEqual((1, 2, 3), self.cfg_type.level_0_b.level_1_b.level_2_c)


class ConfigTest(unittest.TestCase):
    def setUp(self) -> None:
        self.yaml = Path('./src/utils/_tests/test_config.yml')
        self.cfg = Config(self.yaml)
        with open(self.yaml, 'r') as f:
            self.data = yaml.safe_load(f)

    def test__set_attributes(self) -> None:
        '''
        Test setting all attributes from the YAML file
        '''
        self.assertEqual(self.data,
                         self.cfg.data,
                         msg=f'The YAML at {self.yaml} was loaded into the Config class '
                         'incorrectly')
        self.assertEqual(self.cfg.area.screen_size, self.data['area']['screen_size'])
        self.assertEqual(self.cfg.terrain.perlin.shape, (9, 9))

    def test__set_terrain_scale(self) -> None:
        '''
        Test correctly setting the terrain scale based on `pixel_scale` and `terrain_size`
        '''
        self.assertEqual(
            self.data['area']['terrain_size'] * self.data['area']['pixel_scale'],
            self.cfg.area.terrain_scale)

    def test__set_elevation_function(self) -> None:
        '''
        Test assigning elevation Python function based on a config string
        '''
        pnoise = PerlinNoise2D(500, (9, 9), (1, 1), 1111)
        pnoise.precompute()
        # This is the only way I could really come up with to make the correct function
        # was assigned - mdoyle
        self.assertEqual(self.cfg.terrain.elevation_function.__doc__,
                         pnoise.fn.__doc__,
                         msg='The docstring for the set terrain.elevation_function '
                         f'({self.cfg.terrain.elevation_function}) does not match the '
                         'docstring for world.elevation_functions.PerlinNoise2D')

    def test__set_fuel_array_function(self) -> None:
        '''
        Test assigning fuel array Python function based on config string
        '''
        fn = chaparral_fn(self.data['area']['pixel_scale'],
                          self.data['area']['pixel_scale'],
                          self.data['terrain']['chaparral']['seed'])
        self.assertEqual(self.cfg.terrain.fuel_array_function.__doc__,
                         fn.__doc__,
                         msg='The docstring for the set terrain.fuel_array_function '
                         f'({self.cfg.terrain.fuel_array_function}) does not match the '
                         'docstring for world.fuel_array_functions.chaparral_fn.fn')

    def test__set_wind_function(self) -> None:
        '''
        Test assigning wind speed and direction arrays based on config string
        '''
        speed_min = mph_to_ftpm(self.data['wind']['perlin']['speed']['min'])
        speed_max = mph_to_ftpm(self.data['wind']['perlin']['speed']['max'])
        wind_map = WindController()
        wind_map.init_wind_speed_generator(
            self.data['wind']['perlin']['speed']['seed'],
            self.data['wind']['perlin']['speed']['scale'],
            self.data['wind']['perlin']['speed']['octaves'],
            self.data['wind']['perlin']['speed']['persistence'],
            self.data['wind']['perlin']['speed']['lacunarity'], speed_min, speed_max,
            self.data['area']['screen_size'])
        wind_map.init_wind_direction_generator(
            self.data['wind']['perlin']['direction']['seed'],
            self.data['wind']['perlin']['direction']['scale'],
            self.data['wind']['perlin']['direction']['octaves'],
            self.data['wind']['perlin']['direction']['persistence'],
            self.data['wind']['perlin']['direction']['lacunarity'],
            self.data['wind']['perlin']['direction']['min'],
            self.data['wind']['perlin']['direction']['max'],
            self.data['area']['screen_size'])
        self.assertEqual(wind_map.map_wind_speed,
                         self.cfg.wind.speed,
                         msg='The speed array set by config.py:Config does not match the '
                         'values straight from test_config.yml. The Config class is not '
                         'loading the wind speed correctly.')
        self.assertEqual(wind_map.map_wind_direction,
                         self.cfg.wind.direction,
                         msg='The direction array set by config.py:Config does not match '
                         'the values straight from test_config.yml. The Config class is '
                         'notloading the wind direction correctly.')

    def test_save(self) -> None:
        '''
        Test saving the config's data and making sure it matches the original YAML
        '''
        save_path = self.yaml.parent / 'save_config.yml'
        self.cfg.save(save_path)
        with open(save_path, 'r') as f:
            save_data = yaml.safe_load(f)
        save_path.unlink()
        self.assertEqual(self.cfg.data,
                         save_data,
                         msg=f'The data in the saved YAML at {save_path} does not match '
                         f'the data in the test YAML at {self.yaml}')