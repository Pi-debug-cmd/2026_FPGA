import torch, torch.nn as nn
conv = nn.Conv1d(512, 256, 1, groups=256, bias=False)
with torch.no_grad():
    conv.weight.fill_(1.0)
x = torch.arange(1, 513, dtype=torch.float32).reshape(1, 512, 1)
y = conv(x)
out = open(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\deploy_runtime\test\groupconv.txt", "w")
out.write("out0=%.1f out1=%.1f out255=%.1f\n" % (y[0,0], y[0,1], y[0,255]))
out.write("weight shape %s\n" % str(tuple(conv.weight.shape)))
out.close()
