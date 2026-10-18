from pathlib import Path
import json, subprocess, sys

base = Path(__file__).resolve().parent
native = base.parent / 'board_support/native_llvc_20261005'
live = json.loads((native/'fargan_v8_live_evidence.json').read_text(encoding='utf-8'))
prepared_path = native/'v8_trial_prepared.json'
prepared = json.loads(prepared_path.read_text(encoding='utf-8'))
prepared.update(live_deployed=live['v8_live_deployed'],
                live_verified_short_observation=live['live_verified_short_observation'],
                latest_evidence_path=str(native/'fargan_v8_live_evidence.json'),
                human_acceptance_pending=True, quality_accepted=False,
                project_completed=False)
prepared_path.write_text(json.dumps(prepared, ensure_ascii=False, indent=2),encoding='utf-8')
subprocess.run([sys.executable, str(base/'publish_oct6_refinement_20261006.py')],check=True)
print(json.dumps(dict(v8_live_deployed=live['v8_live_deployed'],
                     observed_frames=live['status']['frames'],
                     capture_playback_logs_empty=not live['logs']['capture.log'] and not live['logs']['playback.log'],
                     human_acceptance_pending=True),ensure_ascii=False))
