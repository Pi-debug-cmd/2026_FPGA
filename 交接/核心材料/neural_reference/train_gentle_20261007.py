"""Gentle, clean target adaptation of full LLVC.

Root cause of prior failure: LR 1e-4 + many conflicting losses immediately
destroyed the clean G_5000 weights (flatness 0.0007 -> 0.009 by step 400).
This version: LR 1e-5, strong waveform-L1 + multires-mel to the CV3 teacher,
no GAN, light content/anchor/identity terms. Preserves clean weights.
"""
from run_rvc_pilot import settings
settings()
from pathlib import Path
import sys, json, time, argparse
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import HubertModel

BASE = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
NR = BASE/"neural_reference"; BUD = BASE/"board_budget_20261005"
CORPUS = BUD/"full_train_corpus_16k"
sys.path.insert(0, str(NR)); sys.path.insert(0, str(NR/"LLVC"))
from load_llvc_audit_model import load_model
from train_board_student_20261005 import Objective, read
from differentiable_speaker_20261005 import FrozenSpeaker

OFFICIAL = NR/"llvc_pretrained_audit/G_500000.pth"
FIXED_SRC = BUD/"fargan_v8_fullchain_verification/B_普通男声_同一句中文.wav"
TARGET_REF = Path(r"D:\总进度\目标人物分析\SeedVC下一阶段\inputs\target_t6_8s.wav")

def load_corpus():
    m = json.loads((CORPUS/"manifest.json").read_text(encoding="utf-8"))
    train, val, anchors = [], [], []
    for e in m["train"]:
        train.append((np.fromfile(e["src"],dtype="<f4"), np.fromfile(e["tch"],dtype="<f4")))
    for e in m["validation"]:
        val.append((e["stem"], np.fromfile(e["src"],dtype="<f4"), np.fromfile(e["tch"],dtype="<f4")))
    for e in m["anchors"]:
        anchors.append(np.fromfile(e["path"],dtype="<f4"))
    return train, val, anchors

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=3000)
    ap.add_argument("--out", default="gentle_target_student")
    ap.add_argument("--lr", type=float, default=1e-5)
    args = ap.parse_args()
    OUT = BUD/args.out; OUT.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(20261007); rng = np.random.default_rng(20261007)
    device="cuda"

    net, cfg = load_model(False)
    net.load_state_dict(torch.load(OFFICIAL,map_location="cpu",weights_only=True)["model"], strict=True)
    net = net.to(device).train()
    print("MODEL params", sum(p.numel() for p in net.parameters()), flush=True)

    train, val, anchors = load_corpus()
    anchors=[torch.tensor(a,device=device) for a in anchors]

    hub = HubertModel.from_pretrained(str(NR/"RVC/assets/hubert_base"),local_files_only=True).to(device).eval()
    hub.encoder.layers = nn.ModuleList(hub.encoder.layers[:9])
    for p in hub.parameters(): p.requires_grad_(False)
    objective = Objective(device)
    speaker = FrozenSpeaker().to(device).eval()
    with torch.no_grad():
        ref_emb = speaker.embedding(torch.tensor(read(str(TARGET_REF)),device=device))

    opt = torch.optim.AdamW(net.parameters(), lr=args.lr, betas=(.8,.99), weight_decay=0)
    SEG=32000; start=time.perf_counter(); history=[]
    def hf(w): return hub(F.layer_norm(w,w.shape[-1:])).last_hidden_state

    for step in range(args.steps):
        xs=[]; ys=[]
        for _ in range(2):
            x,y=train[int(rng.integers(len(train)))]
            at=int(rng.integers(max(1,len(x)-SEG+1)))
            xx=np.pad(x[at:at+SEG],(0,max(0,SEG-(min(SEG,len(x)-at))))); yy=np.pad(y[at:at+SEG],(0,max(0,SEG-(min(SEG,len(y)-at)))))
            xs.append(torch.tensor(xx,device=device)); ys.append(torch.tensor(yy,device=device))
        source=torch.stack(xs); teacher=torch.stack(ys)
        anc=anchors[int(rng.integers(len(anchors)))]
        at=int(rng.integers(max(1,len(anc)-SEG+1)))
        seg=min(SEG,len(anc)-at); aclip=F.pad(anc[at:at+seg],(0,SEG-seg))
        batch=torch.cat([source,aclip[None]])
        pred=net(batch[:,None])[:,0].float()
        fake=pred[:2]; anc_fake=pred[2:3]

        spectral=objective.loss(fake,teacher)
        wave=(fake-teacher).abs().mean()/teacher.abs().mean().clamp_min(1e-3)
        with torch.no_grad(): sh=hf(source)
        content=F.l1_loss(hf(fake),sh)
        identity=1-(speaker.embedding(fake)*ref_emb).sum(dim=-1).mean()
        anc_mel=objective.loss(anc_fake,aclip[None])
        anc_w=(anc_fake-aclip[None]).abs().mean()/aclip.abs().mean().clamp_min(1e-3)
        loss=5*spectral+3*wave+1*content+1*identity+1*anc_mel+1*anc_w
        opt.zero_grad(set_to_none=True); loss.backward()
        torch.nn.utils.clip_grad_norm_(net.parameters(),5); opt.step()

        if step%50==0 or step==args.steps-1:
            rec=dict(step=step+1,loss=float(loss),spectral=float(spectral),wave=float(wave),
                     content=float(content),identity=float(identity),anc=float(anc_w),
                     seconds=time.perf_counter()-start)
            history.append(rec); print("STEP",json.dumps(rec),flush=True)
            (OUT/"training_status.json").write_text(json.dumps(dict(history=history,complete=False)))

        if (step+1)%400==0 or step==args.steps-1:
            torch.save(dict(model={k:v.detach().cpu() for k,v in net.state_dict().items()},
                            config=cfg,steps=step+1),OUT/("checkpoint_step"+str(step+1)+".pt"))
            net.eval(); import soundfile as sf
            def bulk(x):
                return net(torch.tensor(np.asarray(x,dtype=np.float32),device=device)[None,None])[0,0].float().cpu().numpy()
            with torch.no_grad():
                fout=bulk(read(str(FIXED_SRC))); sf.write(OUT/("fixed_sentence_step"+str(step+1)+".wav"),fout,16000)
                vm=[]
                for stem,vx,vy in val:
                    vo=bulk(vx); n=min(len(vo),len(vy))
                    vt=torch.tensor(vo[:n],device=device)
                    vm.append(dict(stem=stem,cos=float((speaker.embedding(vt[None])*ref_emb).sum()),
                                   spec=float(objective.loss(vt[None],torch.tensor(vy[:n],device=device)[None]))))
                print("VAL",step+1,"cos",round(float(np.mean([v['cos'] for v in vm])),3),
                      "spec",round(float(np.mean([v['spec'] for v in vm])),3),flush=True)
            net.train()
    print("GENTLE_TRAIN_DONE",flush=True)

if __name__=="__main__":
    main()
