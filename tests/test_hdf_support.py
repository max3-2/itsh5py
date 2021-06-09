"""
Tester for the main functions handling hdf io. All test are run with
compression which, in theory, should work since gzip is lossless.
"""
from sys import argv
import unittest
import logging
from pathlib import Path
import numpy as np
import pandas as pd
from numpy.testing import assert_array_equal
from pandas.testing import assert_frame_equal
import itsh5py

logger = logging.getLogger('itsh5py')
itsh5py.config.use_lazy = False  # Set lazy to False so the data can be compared.

class CustomValidation(object):
    def assertDictEqual_with_arrays(self, d1, d2):
        assert d1.keys() == d2.keys(), "Dict mismatch in keys"
        for key, value in d1.items():
            if isinstance(value, np.ndarray):
                assert isinstance(d2[key], np.ndarray), "Second element not an array"
                assert_array_equal(value, d2[key], err_msg='Array mismatch')

            elif isinstance(value, pd.DataFrame):
                assert isinstance(d2[key], pd.DataFrame), "Second element not a DataFrame"
                assert_frame_equal(value, d2[key])

            else:
                assert value == d2[key], "Non-Array item mismatch"


class TestSupplementary(unittest.TestCase):
    """Tests additional features
    """
    def test_ending(self):
        logger.info('Testing default suffix')

        itsh5py.config.default_suffix = '.h5'
        logger.debug(f'Testing default suffix: {itsh5py.config.default_suffix}')
        test_file = itsh5py.save('test_ending', {'1': 1})
        self.assertIsInstance(test_file, Path)
        self.assertEqual(str(test_file.name), 'test_ending' + itsh5py.config.default_suffix)
        test_file.unlink()

        itsh5py.config.default_suffix = '.hdf'
        logger.debug(f'Testing default suffix: {itsh5py.config.default_suffix}')
        test_file = itsh5py.save('test_ending', {'1': 1})
        self.assertIsInstance(test_file, Path)
        self.assertEqual(str(test_file.name), 'test_ending' + itsh5py.config.default_suffix)
        test_file.unlink()

        logger.debug('Tree view test / Lazy Test / Queue Test')
        itsh5py.config.use_lazy = True
        test_data = {'int_type': 1,
                     'float_type': 1.,
                     }

        test_file = itsh5py.save('test_tree', test_data)
        test_data_loaded = itsh5py.load(test_file)
        print(test_data_loaded)
        self.assertEqual(itsh5py.max_open_files, 12)
        self.assertEqual(itsh5py.open_filenames(), [test_file.name])
        test_data_loaded.close()
        self.assertTrue(not itsh5py.queue_handler.is_open(test_file))
        self.assertEqual(len(itsh5py.queue_handler.open_files), 0)

        itsh5py.config.use_lazy = False
        test_file.unlink()

class TestBasicTypes(unittest.TestCase):
    """Tests the most basic types for IO
    """
    def test_numbers(self):
        test_data = {'int_type': 1,
                     'float_type': 1.,
                     'complex_type': 1+1j,
                     }

        test_file = itsh5py.save('test_numbers', test_data)
        test_data_loaded = itsh5py.load(test_file)

        self.assertIsInstance(test_data_loaded, dict)
        self.assertDictEqual(test_data, test_data_loaded)
        test_file.unlink()

    def test_string(self):
        test_data = {'string_type': 'string',
                     'unicode_str_type': 'öäü°^'
                     }
        test_file = itsh5py.save('test_string', test_data)
        test_data_loaded = itsh5py.load(test_file)

        self.assertIsInstance(test_data_loaded, dict)
        self.assertDictEqual(test_data, test_data_loaded)
        test_file.unlink()

    def test_boolean(self):
        test_data = {'bool_type_1': True,
                     'bool_type_2': False,
                     }
        test_file = itsh5py.save('test_boolean', test_data)
        test_data_loaded = itsh5py.load(test_file)

        self.assertIsInstance(test_data_loaded, dict)
        self.assertDictEqual(test_data, test_data_loaded)
        test_file.unlink()

    def test_singleton(self):
        test_data = {'int_type': 1,
                     }

        test_file = itsh5py.save('test_singleton', test_data)
        test_data_loaded = itsh5py.load(test_file)

        self.assertEqual(test_data_loaded, 1)
        test_file.unlink()


class TestIterableTypes(unittest.TestCase):
    def test_simple_iterables(self):
        test_data = {'list_type': [1, 2, 3],  # fails due to array conv.
                     'tuple_type': (1, 2, 3),
                     'set_type': set([1, 2, 3]),
                     'list_type_str': ['a', 'b', 'cd', 'äöü'],
                     }

        test_file = itsh5py.save('test_iterables', test_data)
        test_data_loaded = itsh5py.load(test_file)

        self.assertIsInstance(test_data_loaded, dict)
        self.assertDictEqual(test_data, test_data_loaded)
        test_file.unlink()

    def test_mixed_iterables(self):
        test_data = {'list_type': [1, 2., '3'],
                     'tuple_type': (1, 2., '3'),
                     'long_tuple_type': tuple([i for i in range(1000)]),
                     'set_type': set([1, 2., '3']),
                     }

        test_file = itsh5py.save('test_mixed_iterables', test_data)
        test_data_loaded = itsh5py.load(test_file)

        self.assertIsInstance(test_data_loaded, dict)
        self.assertDictEqual(test_data, test_data_loaded)
        test_file.unlink()

    def test_iterable_with_array(self):
        test_data = {'list_type': [1, 2., '3', np.ones((10, 20))],
                     'tuple_type': (1, 2., '3', np.ones((10, 20))),
                     }

        test_file = itsh5py.save('test_iterables_array', test_data)
        test_data_loaded = itsh5py.load(test_file)

        self.assertIsInstance(test_data_loaded, dict)
        with self.assertRaises(ValueError):
            self.assertDictEqual(test_data, test_data_loaded)
        test_file.unlink()


class TestNestedTypes(unittest.TestCase):
    def test_nested(self):
        test_data_2 = {'list_type': [1, 2., '3'],
                       'tuple_type': (1, 2., '3'),
                       'set_type': set([1, 2., '3']),
                       }

        test_data_1 = {'int_type': 1,
                       'float_type': 1.,
                       'complex_type': 1+1j,
                       'nested_2': test_data_2,
                       }

        test_data = {'int_type': 1,
                     'float_type': 1.,
                     'complex_type': 1+1j,
                     'nested': test_data_1,
                     'list_of_str_lists': [['a', 'b', 'C'], ['D', 'e']],
                     'tuple_of_str_tuples': (('a', 'b', 'C'), ('D', 'e')),
                     'list_of_str_lists_ascii': [['a', 'b', 'C'], ['D', 'e'], ['1', 'ä']],
                     'tuple_of_str_tuples_ascii': (('a', 'b', 'C'), ('D', 'e'), ('1', 'ü')),
                     }

        test_file = itsh5py.save('test_nested', test_data)

        # First lazy, check the tree and the lazy load
        itsh5py.config.use_lazy = True
        test_data_loaded = itsh5py.load(test_file)
        print(test_data_loaded)
        test_data_loaded.close()

        # Now the basic comparison
        itsh5py.config.use_lazy = False
        test_data_loaded = itsh5py.load(test_file)
        self.assertIsInstance(test_data_loaded, dict)
        self.assertDictEqual(test_data, test_data_loaded)
        test_file.unlink()


class TestArrayTypes(unittest.TestCase, CustomValidation):
    def test1D(self):
        test_data = {'int_type_1d': np.ones((10,), dtype=int),
                     'float_type_1d': np.ones((10,), dtype=float),
                     'complex_type_1d': np.ones((10,)) * (1+1j),
                     'string_type_1d': np.array(['a', 'b', 'cd', 'äöü']),
                     'string_type_1d_bin': np.array(['a', 'b', 'cd', 'efG'], dtype=bytes),
                     }

        test_file = itsh5py.save('test_array_1d', test_data)
        test_data_loaded = itsh5py.load(test_file)

        self.assertIsInstance(test_data_loaded, dict)
        self.assertDictEqual_with_arrays(test_data, test_data_loaded)
        test_file.unlink()

    def testND(self):
        for i in range(2, 6):  # up to 5 dimensions
            test_data = {'int_type_nd': np.ones(i * (10,), dtype=int),
                         'float_type_nd': np.ones(i * (10,), dtype=float),
                         'complex_type_nd': np.ones(i * (10,)) * (1+1j),
                         'string_type_nd': np.tile(
                            np.array(['a', 'b', 'cd', 'äöü']), i * (5,)),
                         'string_type_nd_bin': np.tile(
                           np.array(['a', 'b', 'cd', 'efG'], dtype=bytes), i * (5,)),
                         }

            test_file = itsh5py.save(f'test_array_{i}d', test_data)
            test_data_loaded = itsh5py.load(test_file)

            self.assertIsInstance(test_data_loaded, dict)
            self.assertDictEqual_with_arrays(test_data, test_data_loaded)
            test_file.unlink()


class TestPandasTypes(unittest.TestCase, CustomValidation):
    def test_single(self):
        test_data = {'dataframe': pd.DataFrame(np.ones((100,5)))
                     }

        test_file = itsh5py.save('test_dataframe', test_data)
        test_data_loaded = itsh5py.load(test_file)

        assert_frame_equal(test_data['dataframe'], test_data_loaded)
        test_file.unlink()

    def test_bare(self):
        test_data = pd.DataFrame(np.ones((100,5)))

        test_file = itsh5py.save('test_dataframe_bare', test_data)
        test_data_loaded = itsh5py.load(test_file)

        assert_frame_equal(test_data, test_data_loaded)
        test_file.unlink()

    def test_frame_lvl1(self):
        test_data = {'dataframe': pd.DataFrame(np.ones((100,5))),
                     'meta': [1, 2, 3],
                     'meta2': np.array([1, 2., 3.]),
                     }

        test_file = itsh5py.save('test_dataframe_lvl1', test_data)
        test_data_loaded = itsh5py.load(test_file)

        self.assertIsInstance(test_data_loaded, dict)
        self.assertDictEqual_with_arrays(test_data, test_data_loaded)
        test_file.unlink()

    def test_frame_lvl2(self):
        lvl2 = {'dataframe': pd.DataFrame(np.ones((100,5))),
                'meta2': np.array([1, 2., 3.]),
                }
        test_data = {'nested': lvl2,
                     'meta': [1, 2, 3],
                     }

        with self.assertRaises(TypeError):
            _ = itsh5py.save('test_dataframe_lvl2', test_data)

        Path('test_dataframe_lvl2' + itsh5py.config.default_suffix).unlink()

class TestInvalidType(unittest.TestCase):
    """Tests a fail, here we use a callable which is not implemented
    """
    def test_invalid_type(self):
        test_data = {'callable': print}
        with self.assertRaises(RuntimeError):
            _ = itsh5py.save('test_fail', test_data)

    def tearDown(self):
        Path('test_fail.hdf').unlink()


if __name__ == '__main__':
    if 'log' in argv[1:]:
        logging.basicConfig(
            level=logging.DEBUG,
            format='[%(asctime)s.%(msecs)03d] %(message)s',
            datefmt='%H:%M:%S')
        logger.info('Logging ON')
        argv.remove('log')

    unittest.main()
