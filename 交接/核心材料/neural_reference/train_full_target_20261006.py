"""Full-size (3.26M) LLVC fine-tuning to the target person.

Starts from the official G_500000 (already knows VC). Losses: multires mel to
the CV3 teacher, HuBERT content (fake vs source), WeSpeaker target identity,
multi-period discriminator + feature matching, target anchor self-reconstruction.
Heavy auxiliary nets are frozen offline training aids only.
"""
from run_rvc_pilot import settings
settings()
from pathlib import Path
import sys, json, time, hashlib, argparse
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import HubertModel

BASE = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
NR = BASE/"neural_reference"
BUD = BASE/"board_budget_20261005"
CORPUS = BUD/"full_train_corpus_16k"
sys.path.insert(0, str(NR))
sys.path.insert(0, str(NR/"LLVC"))
from load_llvc_audit_model import load_model
from llvc_online_stream import LLVCAudioStream
from train_board_student_20261005 import Objective, read
from discriminators import MultiPeriodDiscriminator, discriminator_loss, feature_loss, generator_loss
from differentiable_speaker_20261005 import FrozenSpeaker

OFFICIAL = NR/"llvc_pretrained_audit/G_500000.pth"
FIXED_SRC = BUD/"fargan_v8_fullchain_verification/B_普通男声_同一句中文.wav"
TARGET_REF = Path(r"D:\总进度\目标人物分析\SeedVC下一阶段\inputs\target_t6_8s.wav")

def load_corpus():
    m = json.loads((CORPUS/"manifest.json").read_text(encoding="utf-8"))
    assert m["complete"]
    train, val, anchors = [], [], []
    for e in m["train"]:
        x = np.fromfile(e["src"], dtype="<f4"); y = np.fromfile(e["tch"], dtype="<f4")
        train.append((x, y))
    for e in m["validation"]:
        x = np.fromfile(e["src"], dtype="<f4"); y = np.fromfile(e["tch"], dtype="<f4")
        val.append((e["stem"], x, y))
    for e in m["anchors"]:
        anchors.append(np.fromfile(e["path"], dtype="<f4"))
    return train, val, anchors

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=3000)
    ap.add_argument("--out", default="full_target_student")
    ap.add_argument("--resume")
    ap.add_argument("--start-adv", type=int, default=400)
    args = ap.parse_args()
    OUT = BUD/args.out; OUT.mkdir(parents=True, exist_ok=True)

    torch.manual_seed(20261006); rng = np.random.default_rng(20261006)
    device = "cuda"; assert torch.cuda.is_available()

    # Full model from official checkpoint
    net, cfg = load_model(False)
    state = torch.load(OFFICIAL, map_location="cpu", weights_only=True)
    net.load_state_dict(state["model"], strict=True)
    if args.resume:
        rs = torch.load(args.resume, map_location="cpu", weights_only=True)
        net.load_state_dict(rs["model"], strict=True)
    net = net.to(device).train()
    print("MODEL params", sum(p.numel() for p in net.parameters()), flush=True)

    train, val, anchors = load_corpus()
    anchors = [torch.tensor(a, device=device) for a in anchors]

    # HuBERT content
    hub = HubertModel.from_pretrained(str(NR/"RVC/assets/hubert_base"), local_files_only=True).to(device).eval()
    hub.encoder.layers = nn.ModuleList(hub.encoder.layers[:9])
    for p in hub.parameters(): p.requires_grad_(False)

    # Discriminator
    mpd = MultiPeriodDiscriminator(periods=[2,3,5,7,11]).to(device)
    objective = Objective(device)

    # Target identity
    speaker = FrozenSpeaker().to(device).eval()
    with torch.no_grad():
        ref_emb = speaker.embedding(torch.tensor(read(str(TARGET_REF)), device=device))

    go = torch.optim.AdamW(net.parameters(), lr=1e-4, betas=(.8,.99), weight_decay=0)
    do = torch.optim.AdamW(mpd.parameters(), lr=1e-4, betas=(.8,.99), weight_decay=0)

    SEG = 32000  # 2s
    start = time.perf_counter(); history = []

    def hub_feat(w):
        return hub(F.layer_norm(w, w.shape[-1:])).last_hidden_state

    for step in range(args.steps):
        xs=[]; ys=[]
        for _ in range(2):
            x, y = train[int(rng.integers(len(train)))]
            at = int(rng.integers(max(1, len(x)-SEG+1)))
            xx = x[at:at+SEG]; yy = y[at:at+SEG]
            xx = np.pad(xx,(0,max(0,SEG-len(xx)))); yy = np.pad(yy,(0,max(0,SEG-len(yy))))
            xs.append(torch.tensor(xx,device=device)); ys.append(torch.tensor(yy,device=device))
        source = torch.stack(xs); teacher = torch.stack(ys)
        # anchor self-reconstruction
        anc = anchors[int(rng.integers(len(anchors)))]
        at = int(rng.integers(max(1,len(anc)-SEG+1)))
        aclip = anc[at:at+SEG]; aclip = F.pad(aclip,(0,max(0,SEG-len(aclip))))
        batch_in = torch.cat([source, aclip[None]])
        pred = net(batch_in[:,None])[:,0].float()
        assert torch.isfinite(pred).all()
        fake = pred[:2]; anc_fake = pred[2:3]

        adv = step >= args.start_adv
        if adv:
            for p in mpd.parameters(): p.requires_grad_(True)
            do.zero_grad(set_to_none=True)
            ydr, ydg, _, _ = mpd(teacher[:,None], fake.detach()[:,None])
            dl, _, _ = discriminator_loss(ydr, ydg)
            dl.backward(); torch.nn.utils.clip_grad_norm_(mpd.parameters(), 5); do.step()
        for p in mpd.parameters(): p.requires_grad_(False)

        go.zero_grad(set_to_none=True)
        spectral = objective.loss(fake, teacher)
        with torch.no_grad(): src_h = hub_feat(source)
        fake_h = hub_feat(fake)
        content = F.l1_loss(fake_h, src_h)
        identity = 1-(speaker.embedding(fake.reshape(-1)[None] if False else fake)*ref_emb).sum(dim=-1).mean()
        anc_spectral = objective.loss(anc_fake, aclip[None])
        anc_wave = (anc_fake-aclip[None]).abs().mean()/aclip.abs().mean().clamp_min(1e-3)
        gl=torch.tensor(0.,device=device); fm=torch.tensor(0.,device=device)
        if adv:
            ydr, ydg, fmr, fmg = mpd(teacher[:,None], fake[:,None])
            gl, _ = generator_loss(ydg)
            fm = feature_loss(fmr, fmg)
        loss = 5*spectral + 2*content + 3*identity + 2*anc_spectral + 2*anc_wave + (0.3*gl + 2*fm if adv else 0)
        assert torch.isfinite(loss)
        loss.backward(); grad = torch.nn.utils.clip_grad_norm_(net.parameters(),5)
        assert torch.isfinite(grad); go.step()

        if step%50==0 or step==args.steps-1:
            rec = dict(step=step+1, loss=float(loss), spectral=float(spectral),
                       content=float(content), identity=float(identity),
                       anc_spectral=float(anc_spectral), anc_wave=float(anc_wave),
                       adv=float(gl), feat_match=float(fm),
                       seconds=time.perf_counter()-start,
                       gpu_mb=round(torch.cuda.max_memory_allocated()/1e6,1))
            history.append(rec); print("STEP", json.dumps(rec), flush=True)
            (OUT/"training_status.json").write_text(json.dumps(dict(history=history,complete=False),indent=2))

        if (step+1)%400==0 or step==args.steps-1:
            torch.save(dict(model={k:v.detach().cpu() for k,v in net.state_dict().items()},
                            config=cfg, steps=step+1, quality_accepted=False),
                       OUT/("checkpoint_step"+str(step+1)+".pt"))
            # validation: fixed sentence + 8 val utterances, streaming
            # validation: fixed sentence + 8 val utterances, bulk forward (fast)
            net.eval()
            import soundfile as sf
            def bulk(x):
                w = torch.tensor(np.asarray(x, dtype=np.float32), device=device)
                return net(w[None,None])[0,0].float().cpu().numpy()
            with torch.no_grad():
                fx = read(str(FIXED_SRC))
                fout = bulk(fx)
                sf.write(OUT/("fixed_sentence_step"+str(step+1)+".wav"), fout, 16000)
                vmetrics=[]
                for stem, vx, vy in val:
                    vo = bulk(vx); n = min(len(vo), len(vy))
                    vt = torch.tensor(vo[:n],device=device)
                    vmet = dict(stem=stem,
                        target_cos=float((speaker.embedding(vt[None])*ref_emb).sum()),
                        spectral=float(objective.loss(vt[None],torch.tensor(vy[:n],device=device)[None])))
                    vmetrics.append(vmet)
                mean_cos = float(np.mean([v["target_cos"] for v in vmetrics]))
                mean_spec = float(np.mean([v["spectral"] for v in vmetrics]))
                print("VAL", step+1, "target_cos", round(mean_cos,3), "spectral", round(mean_spec,3), flush=True)
                (OUT/("validation_step"+str(step+1)+".json")).write_text(
                    json.dumps(dict(mean_target_cos=mean_cos, mean_spectral=mean_spec, per=vmetrics),indent=2))
            net.train()

    (OUT/"decision.json").write_text(json.dumps(dict(
        complete=True, steps=args.steps, parameters=sum(p.numel() for p in net.parameters()),
        history=history, teacher_human_accepted=False, quality_accepted=False,
        board_live_verified=False, official_start=str(OFFICIAL),
        target_track9_used=False, source_enrollment=False),indent=2), encoding="utf-8")
    print("FULL_TRAIN_DONE", flush=True)

if __name__=="__main__":
    main()
