"""Isolate wider/shallow trials; preserve every prior experiment and checkpoint."""
from pathlib import Path
base=Path(__file__).resolve().parent
source=(base/'train_board_reconstruction_20261005.py').read_text(encoding='utf-8')
source=source.replace("from pathlib import Path", "from pathlib import Path\nfrom prepare_wide_shallow_geometry import build_wide_shallow")
source=source.replace('small128_reconstruction','wide192_shallow2_reconstruction')
source=source.replace('model,cfg,selection=build_small(128)','model,cfg,selection=build_wide_shallow()')
(base/'train_board_wide_shallow_reconstruction_20261005.py').write_text(source,encoding='utf-8')
source=(base/'train_board_target_anchor_20261005.py').read_text(encoding='utf-8')
source=source.replace("from pathlib import Path", "from pathlib import Path\nfrom prepare_wide_shallow_geometry import build_wide_shallow")
source=source.replace('small128_reconstruction','wide192_shallow2_reconstruction').replace('small128_target_anchor','wide192_shallow2_target_anchor')
source=source.replace('model,cfg,selection=build_small(128)','model,cfg,selection=build_wide_shallow()')
source=source.replace('STEPS=2400','STEPS=800')
source=source.replace("cl=transcript_loss(fake,torch.stack(clean)[:,warm:])", "cl=transcript_loss(fake,torch.stack(clean)[:,warm:]) if step%4==0 else torch.tensor(0.,device=device)")
source=source.replace("checkpoint_selection='fixed2400step_endpoint'", "checkpoint_selection='fixed800step_endpoint',ctc_guidance_frequency_steps=4")
# The GAN sees equally normalized voice, preventing low amplitude from making
# teacher and synthesized signals indistinguishable to the small discriminator.
source=source.replace("history=[];start=time.perf_counter();", "def disc_wave(x):\n  return x*(.1/x.square().mean(dim=-1,keepdim=True).sqrt().detach().clamp_min(.001))\n history=[];start=time.perf_counter();")
source=source.replace('disc(real[:,None])','disc(disc_wave(real)[:,None])').replace('disc(fake.detach()[:,None])','disc(disc_wave(fake.detach())[:,None])').replace('disc(fake[:,None])','disc(disc_wave(fake)[:,None])')
source=source.replace("runtime_no_original_mix=True", "runtime_no_original_mix=True,discriminator_rms_normalization=.1")
(base/'train_board_wide_shallow_target_anchor_20261005.py').write_text(source,encoding='utf-8')
print('WIDE_TRAINING_SCRIPTS_PREPARED')
