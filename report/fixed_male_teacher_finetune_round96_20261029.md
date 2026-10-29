# PS-20261021-10：输出层源专用适配 Round 96

本轮 **REJECTED**。只训练输出层100步的录音4五门为`.6975/.6843/.1168/2.2291/.2500`。冻结内容网络使CER优于Round94/95，但泄漏和UTMOS仍比未适配基线差，输出层适配100步也过强。Checkpoint SHA `5655368d363ec0fa17231ffb6e5d9f96889852bacf3038ea5edce36666e435ce`；候选SHA `37b7143199e48f7679d020ef27dbc55140eceb6b89f5abed0ef072bf1a8cea3f`。录音5和Track9未使用。
