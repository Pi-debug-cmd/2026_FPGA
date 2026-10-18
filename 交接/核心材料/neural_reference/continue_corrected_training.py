"""Resume e60 in an isolated experiment; preserve accepted baseline and originals."""
from pathlib import Path
import shutil
import run_rvc_pilot as pilot

BASE=Path(__file__).resolve().parent
ROOT=BASE/'RVC'

def main():
    old=ROOT/'logs/target_person_corrected'
    new=ROOT/'logs/target_person_moretraining'
    pilot.EXP=new
    pilot.settings()
    for name in ['config.json','filelist.txt','G_2333333.pth','D_2333333.pth']:
        if not (new/name).exists(): shutil.copy2(old/name,new/name)
    print('Baseline e60 untouched; resume in '+str(new),flush=True)
    pilot.train(120)

if __name__=='__main__': main()
