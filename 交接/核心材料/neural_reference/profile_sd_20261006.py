import torch

ckpt = torch.load(r'D:\Tools_FPGA\workspace\voice_conversion_zynq7020\board_budget_20261005\full_target_student\checkpoint_step3000.pt', map_location='cpu', weights_only=False)
sd = ckpt['model']
total = sum(v.numel() for v in sd.values())
print("TOTAL params:", total)

# group by module prefix
from collections import defaultdict
groups = defaultdict(int)
for k, v in sd.items():
    top = k.split('.')[0]
    groups[top] += v.numel()
print("\n=== top-level groups ===")
for g, n in sorted(groups.items(), key=lambda x: -x[1]):
    print(f"{g:20s} {n:>10d}")

print("\n=== every tensor (name, shape, numel) ===")
for k, v in sd.items():
    print(f"{k:55s} {str(list(v.shape)):22s} {v.numel():>8d}")
