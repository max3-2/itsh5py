"""
Tester for the main functions handling hdf io. All test are run with and
without compression which, in theory, should work since gzip is lossless.
"""
from sys import argv
import unittest
import logging
from pathlib import Path
import itsh5py

logger = logging.getLogger('itsh5py')




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


class TestIterableTypes(unittest.TestCase):
    def test_simple_iterables(self):
        test_data = {'list_type': [1, 2, 3],  # fails due to array conv.
                     'tuple_type': (1, 2, 3),
                     'set_type': set([1, 2, 3]),
                     }

        test_file = itsh5py.save('test_iterables', test_data)
        test_data_loaded = itsh5py.load(test_file)

        self.assertIsInstance(test_data_loaded, dict)
        self.assertDictEqual(test_data, test_data_loaded)
        test_file.unlink()


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

    itsh5py.config.use_lazy = False  # Set lazy to False so the data can be compared.
    unittest.main()
