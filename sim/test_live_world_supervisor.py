"""Fault injection for child ownership, bounded cleanup and mixer restoration."""
import contextlib
import importlib.util
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('live_world_trial', ROOT / 'board/live_world_trial.py')
trial = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trial)


class SupervisorChecks(unittest.TestCase):
    def exercise(self, fault):
        events, children = [], []
        class Child:
            def __init__(self, role):
                self.role, self.pid, self.returncode = role, 100 + role, None
                self.stdout = io.BytesIO() if role < 2 else None
            def poll(self):
                if fault in ('launch_fail', 'stuck_child'):
                    return self.returncode
                if fault == 'child_fail':
                    if self.role == 1:
                        self.returncode = 5
                    return self.returncode
                self.returncode = 0
                return 0
            def terminate(self):
                events.append(('terminate', self.role))
                if fault != 'stuck_child':
                    self.returncode = -15
            def kill(self):
                events.append(('kill', self.role)); self.returncode = -9
            def wait(self, timeout):
                events.append(('wait', self.role, timeout))
                if self.returncode is None:
                    raise subprocess.TimeoutExpired('fake child', timeout)
                return self.returncode

        def popen(command, **kwargs):
            role = len(children)
            if fault in ('launch_fail', 'stuck_child') and role == 2:
                raise OSError('aplay launch failed')
            child = Child(role); children.append(child)
            if role == 0 and fault == 'xrun':
                kwargs['stderr'].write(b'overrun!!!\n')
            if role == 1:
                if fault in ('fifo_ok', 'fifo_fallback'):
                    self.assertEqual(command[-1], 'fifo')
                    enabled = 'true' if fault == 'fifo_ok' else 'false'
                    kwargs['stderr'].write(('{"exit_code":0,"scheduling_fifo":' + enabled +
                        ',"reader_sched_error":0,"analysis_sched_error":0,"render_sched_error":0,"writer_sched_error":0}\n').encode())
                elif fault in ('fifo_io_ok', 'fifo_io_fallback', 'fifo_io_wrong_compute'):
                    self.assertEqual(command[-1], 'fifo_io')
                    runtime = {'exit_code': 0, 'scheduling_fifo_io': fault != 'fifo_io_fallback',
                               'scheduling_fifo': fault == 'fifo_io_wrong_compute',
                               'reader_sched_error': 0, 'analysis_sched_error': 0,
                               'render_sched_error': 0, 'writer_sched_error': 0}
                    import json
                    kwargs['stderr'].write((json.dumps(runtime) + '\n').encode())
                elif fault in ('voiced_ok', 'voiced_missing'):
                    kwargs['stderr'].write(b'{"exit_code":0,"voiced_frames":100}\n' if fault == 'voiced_ok'
                                           else b'{"exit_code":0,"voiced_frames":0}\n')
                else:
                    kwargs['stderr'].write(b'{"exit_code":0,"raw_capture_clipped_samples":1}\n' if fault == 'adc_clip' else b'{"exit_code":0}\n')
            return child

        def run(command, **kwargs):
            if command[0] == 'amixer' and fault == 'setup_fail':
                raise subprocess.CalledProcessError(1, command)
            if command[-2:] == ['store', '0']:
                Path(command[2]).write_text('saved mixer')
            if command[-2:] == ['restore', '0']:
                events.append(('restore',))
                return subprocess.CompletedProcess(command, 1 if fault == 'restore_fail' else 0)
            return subprocess.CompletedProcess(command, 0)

        with tempfile.TemporaryDirectory(dir=ROOT / 'build/generated/world_budget') as directory:
            base = Path(directory)
            with patch.object(trial, 'preflight', return_value=base / 'runtime'), \
                 patch.object(trial, 'pcm_idle', return_value={'pcm0p': 'closed', 'pcm1c': 'closed'}), \
                 patch.object(trial.subprocess, 'Popen', side_effect=popen), \
                 patch.object(trial.subprocess, 'run', side_effect=run), \
                 contextlib.redirect_stdout(io.StringIO()):
                code = trial.run_trial(base, 2, 180, fifo=fault in ('fifo_ok', 'fifo_fallback'),
                                       fifo_io=fault.startswith('fifo_io'), require_voiced=fault.startswith('voiced_'))
            self.assertEqual(code, 0 if fault in ('none', 'fifo_ok', 'fifo_io_ok', 'voiced_ok') else 1)
            self.assertEqual(sum(event == ('restore',) for event in events), 1)
            restore_index = events.index(('restore',))
            self.assertTrue(all(index < restore_index for index, event in enumerate(events)
                                if event[0] in ('terminate', 'kill', 'wait')))
            if fault in ('launch_fail', 'child_fail'):
                self.assertTrue(any(event[0] == 'terminate' for event in events))
            if fault == 'stuck_child':
                self.assertTrue(any(event[0] == 'kill' for event in events))
            if fault == 'setup_fail':
                self.assertFalse(children)

    def test_normal_completion(self): self.exercise('none')
    def test_partial_launch_failure(self): self.exercise('launch_fail')
    def test_runtime_failure_terminates_other_children(self): self.exercise('child_fail')
    def test_setup_failure_restores_without_launching(self): self.exercise('setup_fail')
    def test_xrun_rejects_successful_child_exits(self): self.exercise('xrun')
    def test_restore_failure_rejects_otherwise_success(self): self.exercise('restore_fail')
    def test_stuck_child_is_killed_before_restore(self): self.exercise('stuck_child')
    def test_adc_saturation_rejects_zero_child_exits(self): self.exercise('adc_clip')
    def test_fifo_verified_success(self): self.exercise('fifo_ok')
    def test_fifo_silent_fallback_rejected(self): self.exercise('fifo_fallback')
    def test_fifo_io_verified_success(self): self.exercise('fifo_io_ok')
    def test_fifo_io_silent_fallback_rejected(self): self.exercise('fifo_io_fallback')
    def test_fifo_io_compute_policy_rejected(self): self.exercise('fifo_io_wrong_compute')
    def test_detected_voiced_input_accepted(self): self.exercise('voiced_ok')
    def test_missing_voiced_input_rejects_speech_trial(self): self.exercise('voiced_missing')


if __name__ == '__main__':
    unittest.main()
