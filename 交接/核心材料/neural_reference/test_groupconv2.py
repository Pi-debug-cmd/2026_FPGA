import torch, torch.nn as nn
# proj_d2e: 256 -> 512, groups=256
conv = nn.Conv1d(256, 512, 1, groups=256, bias=False)
with torch.no_grad():
    conv.weight.fill_(1.0)
x = torch.arange(1, 257, dtype=torch.float32).reshape(1, 256, 1)
y = conv(x)
out = open(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\deploy_runtime\test\groupconv2.txt", "w")
out.write("out0=%.1f out1=%.1f out2=%.1f out3=%.1f out510=%.1f out511=%.1f\n" % (
    y[0,0], y[0,1], y[0,2], y[0,3], y[0,510], y[0,511]))
out.write("weight shape %s\n" % str(tuple(conv.weight.shape)))
out.close()
