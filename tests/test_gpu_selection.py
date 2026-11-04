import unittest

from gwe.util.gpu_selection import resolve_gpu_index, InvalidGpuIndexError, get_application_id, get_database_name


class ResolveGpuIndexTest(unittest.TestCase):
    def test_default_is_zero(self):
        self.assertEqual(0, resolve_gpu_index({}, ['gwe']))

    def test_env_var(self):
        self.assertEqual(2, resolve_gpu_index({'GWE_GPU_INDEX': ' 2 '}, ['gwe']))

    def test_empty_env_var_is_ignored(self):
        self.assertEqual(0, resolve_gpu_index({'GWE_GPU_INDEX': ''}, ['gwe']))

    def test_cli_forms(self):
        self.assertEqual(1, resolve_gpu_index({}, ['gwe', '--gpu-index', '1']))
        self.assertEqual(3, resolve_gpu_index({}, ['gwe', '--debug', '--gpu-index=3']))

    def test_cli_wins_over_env(self):
        self.assertEqual(1, resolve_gpu_index({'GWE_GPU_INDEX': '4'}, ['gwe', '--gpu-index', '1']))

    def test_option_after_double_dash_is_ignored(self):
        self.assertEqual(0, resolve_gpu_index({}, ['gwe', '--', '--gpu-index', '1']))

    def test_invalid_values(self):
        for argv in (['gwe', '--gpu-index', '-1'], ['gwe', '--gpu-index=a'], ['gwe', '--gpu-index='],
                     ['gwe', '--gpu-index'], ['gwe', '--gpu-index', '²']):
            with self.assertRaises(InvalidGpuIndexError, msg=argv):
                resolve_gpu_index({}, argv)
        with self.assertRaises(InvalidGpuIndexError):
            resolve_gpu_index({'GWE_GPU_INDEX': 'x'}, ['gwe'])


class NamingTest(unittest.TestCase):
    def test_gpu_zero_keeps_existing_names(self):
        self.assertEqual('com.leinardi.gwe', get_application_id('com.leinardi.gwe', 0))
        self.assertEqual('gwe.db', get_database_name('gwe.db', 0))

    def test_other_gpus_get_unique_names(self):
        self.assertEqual('com.leinardi.gwe.gpu1', get_application_id('com.leinardi.gwe', 1))
        self.assertEqual('gwe-gpu1.db', get_database_name('gwe.db', 1))
        self.assertEqual('gwe-gpu2', get_database_name('gwe', 2))


if __name__ == '__main__':
    unittest.main()
