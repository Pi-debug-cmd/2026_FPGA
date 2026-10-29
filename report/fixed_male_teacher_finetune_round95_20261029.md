# PS-20261021-10：源专用教师微调 Round 95

本轮 **REJECTED**。全模型微调25步、学习率`1e-4`的录音4指标为`.6957/.6789/.1169/2.2371/.2941`（身份/P10/泄漏/UTMOS/CER）。相对Round88，泄漏、UTMOS和CER全部退步；全模型适配方向止损。Round96只训练输出层，隔离目标参数适配对内容编码器的破坏。

Checkpoint SHA `42e22c7d5c5f0a0d84a3fe63c6c926d3b20c2016a20b41e26917154c3ca3e4d4`；候选SHA `d1d19d811ff06b0576529be7d3f7225af663da9399139d537b653e1debad39a8`。录音5和Track9未使用。
