import torch, json, sys
sys.path.insert(0, r'D:\Tools_FPGA\workspace\voice_conversion_zynq7020\neural_reference\LLVC')
from model import Net

ckpt = torch.load(r'D:\Tools_FPGA\workspace\voice_conversion_zynq7020\board_budget_20261005\full_target_student\checkpoint_step3000.pt', map_location='cpu', weights_only=False)
cfg = ckpt['config']
model = Net(**cfg['model_params'])
model.load_state_dict(ckpt['model'])
model.eval()

def count(m):
    return sum(p.numel() for p in m.parameters())

print("TOTAL params:", count(model))
print("\n=== top-level modules ===")
for name, mod in model.named_children():
    print(f"{name:20s} {count(mod):>10d}  {type(mod).__name__}")

print("\n=== all Conv1d / Linear / ConvTranspose1d ===")
for name, mod in model.named_modules():
    if isinstance(mod, (torch.nn.Conv1d, torch.nn.Linear, torch.nn.ConvTranspose1d)):
        if isinstance(mod, torch.nn.Conv1d):
            extra = f"k={mod.kernel_size} s={mod.stride} g={mod.groups} d={mod.dilation} bias={mod.bias is not None}"
        elif isinstance(mod, torch.nn.ConvTranspose1d):
            extra = f"k={mod.kernel_size} s={mod.stride} pad={mod.padding} bias={mod.bias is not None}"
        else:
            extra = f"in={mod.in_features} out={mod.out_features} bias={mod.bias is not None}"
        print(f"{name:45s} {type(mod).__name__:16s} {count(mod):>8d}  {extra}")
