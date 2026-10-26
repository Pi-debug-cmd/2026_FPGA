"""PS-20261025-20 v2: only change temporal delta loss weight 0.25 -> 1.0.

All other data, model, training and evaluation rules are inherited from v1.
Separate outputs preserve the frozen v1 model. Example:
  python build/remote_ps_c_hubert_fargan_v2.py train --cache-root build/generated/remote_ps_c_hubert_fargan_v1
"""
import remote_ps_c_hubert_fargan as experiment

experiment.CONFIG = {**experiment.CONFIG, "delta_weight": 1.0}
experiment.DEFAULT_OUTPUT = experiment.GENERATED / "remote_ps_c_hubert_fargan_v2"
experiment.CANDIDATE = "Remote-PS-C_HuBERT_BiGRU_FARGAN_v2_delta1"

if __name__ == "__main__":
    experiment.main()
