"""W8A8 quantization simulation for the LLVC target student.

Scheme (matches the gemm_s8 deployment contract):
- weights: per-output-channel symmetric int8, scale s_w[out]
- activations: per-invocation symmetric int8, scale s_x (computed from the
  actual tensor each call -> "per-invocation activation scale")
- compute: int8 @ int8 -> int32, then dequant float, add bias
- everything else (depthwise, attention scores, norms, in/out conv) stays fp32
"""
import torch
import torch.nn as nn
import torch.nn.functional as F


def quantize_per_channel_w(W):
    """W: [out, in] (linear) or [out, in, 1] (conv1d). Returns wq int8, sw [out,1]."""
    if W.dim() == 3:
        W2 = W.squeeze(-1)
    else:
        W2 = W
    out = W2.shape[0]
    amax = W2.abs().amax(dim=1).clamp_min(1e-8)
    sw = (amax / 127.0).view(out, 1)
    wq = torch.round(W2 / sw).clamp(-128, 127).to(torch.int8)
    return wq, sw


def quantize_activation(x):
    """x: any float tensor. Symmetric int8 per-invocation (whole tensor)."""
    amax = x.abs().amax().clamp_min(1e-8)
    sx = amax / 127.0
    xq = torch.round(x / sx).clamp(-128, 127).to(torch.int8)
    return xq, float(sx)


def i8mm(xq, wq):
    """xq [., in] int8, wq [out, in] int8 -> int32 [., out]."""
    return torch.matmul(xq.to(torch.int32), wq.t().to(torch.int32))


class QuantizedMHA(nn.Module):
    """Replicates nn.MultiheadAttention (batch_first) with W8A8 projections.

    Query may have a different length than key/value. The packed in_proj
    weight [3E, E] is split into W_Q, W_K, W_V.
    """
    def __init__(self, ref):
        super().__init__()
        E = ref.embed_dim
        self.E = E
        self.heads = ref.num_heads
        self.head_dim = E // ref.num_heads
        ipw = ref.in_proj_weight.detach()  # [3E, E]
        ipb = ref.in_proj_bias.detach()    # [3E]
        for nm, slc in [("q", slice(0, E)), ("k", slice(E, 2 * E)), ("v", slice(2 * E, 3 * E))]:
            wq, sw = quantize_per_channel_w(ipw[slc])
            self.register_buffer(f"wq_{nm}", wq)
            self.register_buffer(f"sw_{nm}", sw.squeeze(1))
            self.register_buffer(f"b_{nm}", ipb[slc].clone())
        ow, osw = quantize_per_channel_w(ref.out_proj.weight)
        self.register_buffer("wq_o", ow)
        self.register_buffer("sw_o", osw.squeeze(1))
        self.register_buffer("b_o", ref.out_proj.bias.detach().clone())

    def _proj(self, x, nm):
        # x [B, T, E]
        B, T, E = x.shape
        wq = getattr(self, f"wq_{nm}")
        sw = getattr(self, f"sw_{nm}")
        xq, sx = quantize_activation(x)
        xq2 = xq.reshape(B * T, E)
        yq = i8mm(xq2, wq).reshape(B, T, E)
        y = yq.to(torch.float32) * (sx * sw).view(1, 1, -1)
        y = y + getattr(self, f"b_{nm}").view(1, 1, -1)
        return y

    def forward(self, query, key, value, attn_mask=None, key_padding_mask=None):
        B, Tq, _ = query.shape
        Tk = key.shape[1]
        Q = self._proj(query, "q").reshape(B, Tq, self.heads, self.head_dim).permute(0, 2, 1, 3)
        K = self._proj(key, "k").reshape(B, Tk, self.heads, self.head_dim).permute(0, 2, 1, 3)
        V = self._proj(value, "v").reshape(B, Tk, self.heads, self.head_dim).permute(0, 2, 1, 3)
        scores = torch.matmul(Q, K.transpose(-1, -2)) / (self.head_dim ** 0.5)
        if attn_mask is not None:
            scores = scores + attn_mask
        attn = torch.softmax(scores, dim=-1)
        out = torch.matmul(attn, V)  # [B, h, Tq, hd]
        out = out.permute(0, 2, 1, 3).reshape(B, Tq, self.E)
        # output projection
        outq, osx = quantize_activation(out)
        outq2 = outq.reshape(B * Tq, self.E)
        yq = i8mm(outq2, self.wq_o).reshape(B, Tq, self.E)
        y = yq.to(torch.float32) * (osx * self.sw_o).view(1, 1, -1)
        y = y + self.b_o.view(1, 1, -1)
        return y, attn


class QuantizedDense(nn.Module):
    """Wraps a Conv1d(kernel=1) or Linear with W8A8 simulation."""
    def __init__(self, ref):
        super().__init__()
        if isinstance(ref, nn.Conv1d):
            assert ref.kernel_size == (1,)
            self.kind = "conv"
            W = ref.weight
            self.bias = ref.bias
        elif isinstance(ref, nn.Linear):
            self.kind = "lin"
            W = ref.weight
            self.bias = ref.bias
        else:
            raise TypeError(ref)
        wq, sw = quantize_per_channel_w(W)
        self.register_buffer("wq", wq)
        self.register_buffer("sw", sw.squeeze(1))
        self.out_features = wq.shape[0]
        self.in_features = wq.shape[1]

    def forward(self, x):
        # x: conv [B, in, T] ; linear [B, in]
        if self.kind == "conv":
            B, C, T = x.shape
            xq, sx = quantize_activation(x)
            xq2 = xq.permute(0, 2, 1).reshape(B * T, C)
            yq = i8mm(xq2, self.wq).reshape(B, T, self.out_features).permute(0, 2, 1)
            y = yq.to(torch.float32) * (sx * self.sw).view(1, -1, 1)
            if self.bias is not None:
                y = y + self.bias.view(1, -1, 1)
            return y
        else:
            xq, sx = quantize_activation(x)
            yq = i8mm(xq, self.wq)
            y = yq.to(torch.float32) * (sx * self.sw).view(1, -1)
            if self.bias is not None:
                y = y + self.bias.view(1, -1)
            return y
