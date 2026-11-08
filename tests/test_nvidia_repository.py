"""Tests of the NVML / X connection handling of NvidiaRepository with fake NVML and X connections.

They need the GWE dependencies (Gtk...), so they are skipped when the app can't be imported.
"""
import os
import threading
import unittest
from unittest import mock

try:
    from Xlib.error import ConnectionClosedError
    from py3nvml.py3nvml import NVMLError, NVML_ERROR_UNINITIALIZED
    from gwe.repository import nvidia_repository
    IMPORT_ERROR = None
except ImportError as e:  # pragma: no cover
    IMPORT_ERROR = e


def make_display() -> mock.MagicMock:
    xlib_display = mock.MagicMock(name='Display')
    xlib_display.nvcontrol_get_gpu_count.return_value = 2
    xlib_display.nvcontrol_get_gpu_uuid.side_effect = lambda gpu: f'GPU-{gpu.id()}'
    xlib_display.nvcontrol_get_performance_modes.return_value = []
    xlib_display.nvcontrol_get_utilization_rates.return_value = None
    xlib_display.nvcontrol_get_mem_transfer_rate_offset_range.return_value = None
    xlib_display.nvcontrol_get_coolers_used_by_gpu.return_value = []
    xlib_display.nvcontrol_get_cooler_manual_control_enabled.return_value = None
    return xlib_display


@unittest.skipIf(IMPORT_ERROR is not None, f"GWE can't be imported: {IMPORT_ERROR}")
class NvidiaRepositoryConnectionsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.displays = []
        self.nvml = mock.MagicMock(name='py3nvml')
        patches = [
            mock.patch.object(nvidia_repository, 'py3nvml', self.nvml),
            mock.patch.object(nvidia_repository.display, 'Display', side_effect=self._new_display),
        ]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)

    def _new_display(self, *_):
        xlib_display = make_display()
        self.displays.append(xlib_display)
        return xlib_display

    @staticmethod
    def repository(keep=None):
        env = {} if keep is None else {'GWE_KEEP_CONNECTIONS': keep}
        with mock.patch.dict(os.environ, env):
            if keep is None:
                os.environ.pop('GWE_KEEP_CONNECTIONS', None)
            return nvidia_repository.NvidiaRepository()

    def test_connections_are_kept_between_refreshes(self):
        repository = self.repository()
        for _ in range(5):
            status = repository.get_status()
            self.assertIsNotNone(status)
            self.assertEqual(2, len(status.gpu_status_list))
        self.assertEqual(1, self.nvml.nvmlInit.call_count)
        self.assertEqual(1, len(self.displays))
        self.assertEqual(0, self.nvml.nvmlShutdown.call_count)
        self.assertEqual(0, self.displays[0].close.call_count)

    def test_gpu_handles_are_looked_up_once(self):
        repository = self.repository()
        for _ in range(4):
            repository.get_status()
        self.assertEqual(2, self.nvml.nvmlDeviceGetHandleByUUID.call_count)  # one per GPU

    def test_connections_are_reopened_after_an_x_error(self):
        repository = self.repository()
        self.assertIsNotNone(repository.get_status())
        self.displays[0].nvcontrol_get_gpu_count.side_effect = ConnectionClosedError('X server')  # e.g. X restarted
        self.assertIsNone(repository.get_status())
        self.assertEqual(1, self.displays[0].close.call_count)
        self.assertEqual(1, self.nvml.nvmlShutdown.call_count)
        self.assertIsNotNone(repository.get_status())  # reconnected
        self.assertEqual(2, len(self.displays))
        self.assertEqual(2, self.nvml.nvmlInit.call_count)
        self.assertEqual(4, self.nvml.nvmlDeviceGetHandleByUUID.call_count)  # handles looked up again after the reinit

    def test_connections_are_reopened_after_an_nvml_error(self):
        repository = self.repository()
        self.assertIsNotNone(repository.get_status())
        self.nvml.nvmlDeviceGetMemoryInfo.side_effect = NVMLError(NVML_ERROR_UNINITIALIZED)
        self.assertIsNone(repository.get_status())
        self.nvml.nvmlDeviceGetMemoryInfo.side_effect = None
        self.assertIsNotNone(repository.get_status())
        self.assertEqual(2, self.nvml.nvmlInit.call_count)
        self.assertEqual(1, self.nvml.nvmlShutdown.call_count)
        self.assertEqual(2, len(self.displays))

    def test_failing_nvml_init_is_retried(self):
        repository = self.repository()
        self.nvml.nvmlInit.side_effect = [NVMLError(9), None]  # driver not loaded, then loaded
        self.assertIsNone(repository.get_status())
        self.assertEqual(0, self.nvml.nvmlShutdown.call_count)  # nothing was initialized
        self.assertIsNotNone(repository.get_status())

    def test_a_failing_close_doesnt_skip_the_rest(self):
        repository = self.repository()
        repository.get_status()
        self.displays[0].close.side_effect = ConnectionClosedError('already closed')
        repository.close()
        self.assertEqual(1, self.nvml.nvmlShutdown.call_count)

    def test_close_releases_everything_and_is_idempotent(self):
        repository = self.repository()
        repository.get_status()
        repository.close()
        repository.close()
        self.assertEqual(1, self.nvml.nvmlShutdown.call_count)
        self.assertEqual(1, self.displays[0].close.call_count)
        self.assertIsNotNone(repository.get_status())  # reconnects when used again
        self.assertEqual(2, self.nvml.nvmlInit.call_count)

    def test_old_behavior_with_the_environment_variable(self):
        for value in ('0', 'false', 'off', 'no'):
            self.setUp()
            repository = self.repository(value)
            for _ in range(3):
                self.assertIsNotNone(repository.get_status())
            self.assertEqual(3, self.nvml.nvmlInit.call_count, value)
            self.assertEqual(3, self.nvml.nvmlShutdown.call_count, value)
            self.assertEqual(3, len(self.displays), value)
            self.assertTrue(all(d.close.call_count == 1 for d in self.displays), value)

    def test_parallel_refreshes_are_serialized(self):
        repository = self.repository()
        results = []
        threads = [threading.Thread(target=lambda: results.append(repository.get_status())) for _ in range(6)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertTrue(all(result is not None for result in results))
        self.assertEqual(1, self.nvml.nvmlInit.call_count)
        self.assertEqual(1, len(self.displays))


if __name__ == '__main__':
    unittest.main()
