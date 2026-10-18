"""Numeric audit only: official unrelated LLVC voice, eight encoder GEMMs.

This does not accept target identity, Chinese pronunciation, or board latency.
FP32 accumulation of integer-valued operands is exact here: <=512 products,
each <=127**2, hence the absolute sum stays below 2**24.
"""
from pathlib import Path
import copy, json, time
from load_llvc_audit_model import load_model, BASE, digest
from llvc_online_stream import LLVCAudioStream
import torch
import numpy as np
import soundfile as sf

OUT = BASE.parent / 'board_budget_20261004/encoder_quantization'
OUT.mkdir(parents=True, exist_ok=True)
torch.set_num_threads(4)


class QuantizedPointwise(torch.nn.Module):
    def __init__(self, original, activation_bits):
        super().__init__()
        assert original.kernel_size == (1,) and original.groups == 1
        weight = original.weight.detach()[:, :, 0]
        scale = weight.abs().amax(dim=1).clamp_min(1e-12) / 127
        self.register_buffer('qw', (weight / scale[:, None]).round().clamp(-127, 127))
        self.register_buffer('scale', scale)
        self.register_buffer('bias', original.bias.detach().clone() if original.bias is not None else torch.zeros(len(scale)))
        self.activation_bits = activation_bits
        self.calls = 0

    def forward(self, x):
        self.calls += 1
        if self.activation_bits == 8:
            sx = x.abs().amax().clamp_min(1e-12) / 127
            qx = (x / sx).round().clamp(-127, 127)
            y = torch.matmul(qx.transpose(1, 2), self.qw.T) * sx
        else:
            y = torch.matmul(x.transpose(1, 2), self.qw.T)
        return (y * self.scale + self.bias).transpose(1, 2)


def run(model, audio):
    stream = LLVCAudioStream(model)
    outputs = []
    for start in range(0, len(audio), 208):
        outputs.extend(stream.feed(audio[start:start + 208]))
    outputs.extend(stream.finish())
    return np.concatenate(outputs)


def metrics(reference, actual):
    r, a = reference.astype('float64'), actual.astype('float64')
    error = a - r
    alpha = np.dot(a, r) / max(np.dot(r, r), 1e-30)
    target = alpha * r
    noise = a - target
    return dict(normalized_rmse=float(np.linalg.norm(error) / max(np.linalg.norm(r), 1e-30)),
                waveform_snr_db=float(10 * np.log10(max(np.dot(r, r), 1e-30) / max(np.dot(error, error), 1e-30))),
                scale_invariant_sdr_db=float(10 * np.log10(max(np.dot(target, target), 1e-30) / max(np.dot(noise, noise), 1e-30))),
                max_absolute_error=float(np.max(np.abs(error))),
                all_finite=bool(np.isfinite(actual).all()))


if __name__ == '__main__':
    model, config = load_model()
    source = BASE / 'public_chinese_validation/fleurs_test_row0_id1906.wav'
    wave, sr = sf.read(source, dtype='float32')
    assert sr == 16000 and wave.ndim == 1
    reference = run(model, wave)
    rows = []
    for bits in [32, 8]:
        candidate = copy.deepcopy(model)
        replaced = []
        for name, module in list(candidate.named_modules()):
            if name.startswith('mask_gen.encoder.dcc_layers.') and isinstance(module, torch.nn.Conv1d) and module.kernel_size == (1,):
                parent_name, child = name.rsplit('.', 1)
                parent = candidate.get_submodule(parent_name)
                replacement = QuantizedPointwise(module, bits)
                setattr(parent, child, replacement)
                replaced.append(name)
        assert len(replaced) == 8
        start = time.perf_counter()
        actual = run(candidate, wave)
        assert len(actual) == len(reference)
        row = dict(weight_bits=8, activation_bits=bits, affected_layers=replaced,
                   outputs=metrics(reference, actual), pc_wall_seconds=time.perf_counter()-start,
                   bias_normalization_context_and_other_layers_fp32=True)
        rows.append(row)
        print(json.dumps(row, ensure_ascii=False), flush=True)
    decision = dict(status='numeric_audit_only', source=str(source), source_sha256=digest(source),
                    checkpoint_sha256=digest(BASE/'llvc_pretrained_audit/G_500000.pth'),
                    comparisons=rows, per_output_channel_weight_scale=True,
                    per_invocation_activation_scale=True, official_checkpoint_not_user_target=True,
                    target_identity_accepted=False, pronunciation_accepted=False,
                    board_deployed=False, nonlinear_and_attention_quantization_not_tested=True)
    (OUT/'decision.json').write_text(json.dumps(decision, ensure_ascii=False, indent=2), encoding='utf8')
