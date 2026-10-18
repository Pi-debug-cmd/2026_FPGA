import sys, torch
sys.path.insert(0, r'D:\Tools_FPGA\workspace\voice_conversion_zynq7020\neural_reference\sb_stub')
sys.path.insert(0, r'D:\Tools_FPGA\workspace\voice_conversion_zynq7020\neural_reference\LLVC')
from model import Net

ckpt = torch.load(r'D:\Tools_FPGA\workspace\voice_conversion_zynq7020\board_budget_20261005\full_target_student\checkpoint_step3000.pt', map_location='cpu', weights_only=False)
cfg = ckpt['config']
model = Net(**cfg['model_params'])
model.load_state_dict(ckpt['model'])
model.eval()
print("MODEL LOADED params:", sum(p.numel() for p in model.parameters()))

# load B male input and run
import soundfile as sf
b, sr = sf.read(r'D:\Tools_FPGA\workspace\voice_conversion_zynq7020\board_budget_20261005\fargan_v8_fullchain_verification\B_普通男声_同一句中文.wav')
print("B shape", b.shape, "sr", sr)
x = torch.tensor(b, dtype=torch.float32).unsqueeze(0).unsqueeze(0)
with torch.no_grad():
    y = model(x)
print("OUTPUT shape", y.shape, "range", y.min().item(), y.max().item())
sf.write(r'D:\Tools_FPGA\workspace\voice_conversion_zynq7020\board_budget_20261005\reload_check_output.wav', y.squeeze().numpy(), 16000)
print("WROTE reload_check_output.wav")
