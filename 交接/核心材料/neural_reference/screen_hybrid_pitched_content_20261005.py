"""Actual hybrid content/identity diagnostics; reuse trained guidance disclosed."""
from pathlib import Path
import json,sys
BASE=Path(__file__).resolve().parent
out=BASE.parent/'board_budget_20261005/neural_band_hybrid/small128_target_anchor_step400_cut1200'
from screen_board_phonetic_pilot_20261005 import main
# Reuse the checked free decode, accepting an isolated explicit candidate folder.
sys.argv=[sys.argv[0],'--outname','neural_band_hybrid/small128_target_anchor_step400_cut1200','--validation-only']
main()
