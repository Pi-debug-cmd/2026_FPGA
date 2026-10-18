from pathlib import Path
base=Path(__file__).resolve().parent;native=base.parent/'board_support/native_llvc_20261005'
s=(native/'board_neural_wide192.sh').read_text(encoding='utf-8')
s=s.replace('board_neural_live.sh','board_neural_fargan.sh').replace('native_llvc_wide192_shallow2_meter_arm','native_fargan_mapper_arm').replace('wide192_shallow2_target_anchor_selected.f32','fargan_mapper_selected.f32')
s=s.replace('--stream "$DIR/', '"$DIR/').replace('--period-size=208 --buffer-size=832','--period-size=160 --buffer-size=640').replace('--start-delay=39000','--start-delay=30000')
s=s.replace('live_watchdog.py','fargan_live_watchdog.py')
(native/'board_neural_fargan.sh').write_text(s,encoding='utf-8',newline='\n')
print('FARGAN_HELPER_PREPARED_NOT_DEPLOYED')
