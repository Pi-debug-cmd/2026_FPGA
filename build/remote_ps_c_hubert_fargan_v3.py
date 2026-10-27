"""PS-20261025-20 v3: change only v1 PCA input dimension 96 -> 192.

Retains v1 delta loss 0.25 and all other training/evaluation rules.
Dimension changes the input layer shape and random-number consumption.
Separate outputs preserve frozen v1/v2 models. Example:
  python build/remote_ps_c_hubert_fargan_v3.py train --cache-root build/generated/remote_ps_c_hubert_fargan_v1
"""
import remote_ps_c_hubert_fargan as experiment

experiment.CONFIG = {**experiment.CONFIG, "pca_dim": 192}
experiment.DEFAULT_OUTPUT = experiment.GENERATED / "remote_ps_c_hubert_fargan_v3"
experiment.CANDIDATE = "Remote-PS-C_HuBERT_BiGRU_FARGAN_v3_pca192"

if __name__ == "__main__":
    experiment.main()
