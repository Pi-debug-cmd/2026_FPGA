"""Offline failure injection for the persistent minphase-PL boot wrapper."""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
AUTOSTART = ROOT / 'board/world_minphase_autostart.sh'
INIT = ROOT / 'board/world_minphase_init.sh'
SHELL = shutil.which('sh')
TMP_PARENT = ROOT / 'build/generated/world_budget'


class PersistentBootChecks(unittest.TestCase):
    @unittest.skipUnless(SHELL, 'host has no POSIX sh; run execution injection on board')
    def test_bad_boot_asset_selects_factory_and_latches_disable(self):
        with tempfile.TemporaryDirectory(dir=TMP_PARENT) as directory:
            base = Path(directory)
            app, boot, run = base / 'app', base / 'boot', base / 'run'
            app.mkdir(); boot.mkdir()
            factory_bit = base / 'factory.bit'
            factory_bit.write_bytes(b'factory')
            (boot / 'manifest.sha256').write_text('0' * 64 + '  missing.gz\n')
            factory_log = base / 'factory.log'
            factory = base / 'factory.sh'
            factory.write_text('#!/bin/sh\nprintf "%s\\n" "$1" >> "' +
                               factory_log.as_posix() + '"\n')
            env = os.environ.copy()
            env.update({
                'WORLD_PL_APP_DIR': str(app),
                'WORLD_PL_BOOT_DIR': str(boot),
                'WORLD_PL_RUN_DIR': str(run),
                'WORLD_PL_FACTORY_INIT': str(factory),
                'WORLD_PL_FACTORY_BIT': str(factory_bit),
                'WORLD_PL_FACTORY_SHA': hashlib.sha256(b'factory').hexdigest(),
                'WORLD_PL_LOG': str(base / 'autostart.log'),
            })
            result = subprocess.run([SHELL, str(AUTOSTART)], env=env,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(result.returncode, 1)
            self.assertEqual((boot / 'DISABLE').read_text().strip(), 'BOOT_ASSET_HASH')
            self.assertEqual((run / 'state').read_text().strip(),
                             'FALLBACK_FACTORY_BOOT_ASSET_HASH')
            self.assertIn('start', factory_log.read_text().splitlines())

    @unittest.skipUnless(SHELL, 'host has no POSIX sh; run execution injection on board')
    def test_disable_flag_bypasses_candidate_init(self):
        with tempfile.TemporaryDirectory(dir=TMP_PARENT) as directory:
            base = Path(directory)
            disable = base / 'DISABLE'
            disable.write_text('MANUAL\n')
            factory_log = base / 'factory.log'
            factory = base / 'factory.sh'
            factory.write_text('#!/bin/sh\nprintf "%s\\n" "$1" >> "' +
                               factory_log.as_posix() + '"\n')
            env = os.environ.copy()
            env.update({
                'WORLD_PL_DISABLE': str(disable),
                'WORLD_PL_FACTORY_INIT': str(factory),
                'WORLD_PL_DAEMON': str(base / 'must-not-run'),
                'WORLD_PL_PIDFILE': str(base / 'pid'),
                'WORLD_PL_STATE': str(base / 'state'),
            })
            result = subprocess.run([SHELL, str(INIT), 'start'], env=env,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(factory_log.read_text().splitlines(), ['start'])
            self.assertFalse((base / 'pid').exists())

    def test_persistent_runtime_uses_reduced_output_gain(self):
        text = AUTOSTART.read_text()
        self.assertIn('--output-gain-q16 16384', text)
        self.assertNotIn('--output-gain-q16 49152', text)

    def test_init_discards_stale_readiness_before_launch(self):
        text = INIT.read_text()
        self.assertIn('rm -f "${PIDFILE}" "${STATE}"', text)
        self.assertLess(text.index('rm -f "${PIDFILE}" "${STATE}"'),
                        text.index('start-stop-daemon -S'))


if __name__ == '__main__':
    unittest.main()
