"""mangaocr-nar-small network (PyTorch, inference only). Parameter names match model.safetensors.

  encoder   MonkeyOCRv2-S ViT (12 blocks, width 384, 6 heads, SwiGLU 1536, 2D RoPE): patch embedding h0, blocks h1..h11,
            final block + post-norm h12
  memory    gamma fusion: base = Bridge(h12) + Pos(row, col); decoder layer j reads
            m_j = [null x2 ; base + gamma_j * Wo f_j],  f_j = sum_l softmax(depth_logits_j)_l RMSNorm_l(h_l), l = 0..11
  decoder   4 non-autoregressive blocks over 65 output slots (self-attention with QK-norm and 1D RoPE on half the head dims,
            cross-attention to m_j, SwiGLU 2048), per-block pre-norms and residual scales in `cond`; output head tied to `tok`

The released weights are an exact fp16-safe rescaling of the trained checkpoint; the matching RMSNorm eps values come from
config.json ("reparam.norm_eps"). `inject`, `loop_emb` and `occ` are training-time parameters that inference does not use."""
from __future__ import annotations

import json
from pathlib import Path

import torch
import torch.nn.functional as F
from torch import Tensor, nn

SLOTS, D, HEADS, K = 65, 512, 8, 4
ENC_DIM, ENC_HEADS, ENC_FFN, ENC_LAYERS = 384, 6, 1536, 12
UNUSED = ("inject", "loop_emb", "occ.weight", "occ.bias")


class RMSNorm(nn.Module):
    def __init__(self, d: int, eps: float = 1e-6):
        super().__init__()
        self.weight, self.eps = nn.Parameter(torch.ones(d)), eps

    def forward(self, x: Tensor) -> Tensor:
        return F.rms_norm(x.float(), (x.shape[-1],), self.weight.float(), self.eps).to(x.dtype)


class EncRMSNorm(nn.Module):
    """MonkeyOCRv2's RMSNorm (normalise in fp32, cast back, then scale)."""
    def __init__(self, d: int, eps: float = 1e-5):
        super().__init__()
        self.weight, self.eps = nn.Parameter(torch.ones(d)), eps

    def forward(self, x: Tensor) -> Tensor:
        y = x.float()
        return (y * torch.rsqrt(y.pow(2).mean(-1, keepdim=True) + self.eps)).type_as(x) * self.weight


def rotate_half(x: Tensor) -> Tensor:
    a, b = x.chunk(2, -1)
    return torch.cat((-b, a), -1)


class _Attn(nn.Module):
    def __init__(self):
        super().__init__()
        self.qkv, self.proj = nn.Linear(ENC_DIM, 3 * ENC_DIM, bias=False), nn.Linear(ENC_DIM, ENC_DIM, bias=False)


class _Mlp(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(ENC_DIM, ENC_FFN, bias=False)
        self.fc2 = nn.Linear(ENC_FFN, ENC_DIM, bias=False)
        self.fc3 = nn.Linear(ENC_DIM, ENC_FFN, bias=False)


class _VitBlock(nn.Module):
    def __init__(self):
        super().__init__()
        self.attn, self.mlp = _Attn(), _Mlp()
        self.norm1, self.norm2 = EncRMSNorm(ENC_DIM), EncRMSNorm(ENC_DIM)


class _Patchifier(nn.Module):
    def __init__(self):
        super().__init__()
        self.proj = nn.Conv2d(3, ENC_DIM, kernel_size=14, stride=14)
        self.norm = EncRMSNorm(ENC_DIM)


class _PatchEmbed(nn.Module):
    def __init__(self):
        super().__init__()
        self.patchifier = _Patchifier()


class _Rotary(nn.Module):
    def __init__(self, dim: int, theta: float = 10000.0):
        super().__init__()
        self.register_buffer("inv_freq", 1.0 / (theta ** (torch.arange(0, dim, 2, dtype=torch.float) / dim)), persistent=False)

    def forward(self, n: int) -> Tensor:
        return torch.outer(torch.arange(n, device=self.inv_freq.device, dtype=self.inv_freq.dtype), self.inv_freq)


class _Vit(nn.Module):
    def __init__(self):
        super().__init__()
        self.patch_embed = _PatchEmbed()
        self.rotary_pos_emb = _Rotary(ENC_DIM // ENC_HEADS // 2)
        self.blocks = nn.ModuleList(_VitBlock() for _ in range(ENC_LAYERS))
        self.post_trunk_norm = EncRMSNorm(ENC_DIM)


class _Encoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.vit = _Vit()


class Memory(nn.Module):
    def __init__(self):
        super().__init__()
        self.bridge = nn.Sequential(RMSNorm(ENC_DIM), nn.Linear(ENC_DIM, 1024, bias=False), nn.GELU(),
                                    nn.Linear(1024, D, bias=False), RMSNorm(D))
        self.pos = nn.Linear(32, D, bias=False)
        self.null = nn.Parameter(torch.zeros(2, D))
        self.norms = nn.ModuleList(RMSNorm(ENC_DIM) for _ in range(ENC_LAYERS))
        self.wo = nn.Linear(ENC_DIM, D, bias=False)
        self.gamma = nn.Parameter(torch.zeros(K, D))
        self.depth_logits = nn.Parameter(torch.zeros(K, ENC_LAYERS))

    @staticmethod
    def fourier(rows: Tensor, cols: Tensor, h: Tensor, w: Tensor) -> Tensor:
        r = (rows.float() + 0.5) / h[:, None].float()
        c = (cols.float() + 0.5) / w[:, None].float()
        f = torch.pi * 2.0 ** torch.arange(8, device=rows.device).float()
        return torch.cat([fn(t[..., None] * f) for t in (r, c) for fn in (torch.sin, torch.cos)], -1)


class Block(nn.Module):
    def __init__(self):
        super().__init__()
        self.h, self.hd = HEADS, D // HEADS
        self.qkv, self.o1 = nn.Linear(D, 3 * D, bias=False), nn.Linear(D, D, bias=False)
        self.q, self.kv, self.o2 = nn.Linear(D, D, bias=False), nn.Linear(D, 2 * D, bias=False), nn.Linear(D, D, bias=False)
        self.sq, self.sk, self.cq, self.ck = (RMSNorm(self.hd) for _ in range(4))
        self.gate_up, self.down = nn.Linear(D, 2 * 2048, bias=False), nn.Linear(2048, D, bias=False)

    def split(self, x: Tensor) -> Tensor:
        return x.view(x.shape[0], x.shape[1], self.h, self.hd).transpose(1, 2)

    def memory_kv(self, memory: Tensor):
        k, v = self.kv(memory).chunk(2, -1)
        return self.ck(self.split(k)), self.split(v)


class Cond(nn.Module):
    def __init__(self):
        super().__init__()
        self.n1, self.n2, self.n3 = RMSNorm(D), RMSNorm(D), RMSNorm(D)
        self.s1, self.s2, self.s3 = (nn.Parameter(torch.ones(D)) for _ in range(3))


def _rope(t: Tensor, cos: Tensor, sin: Tensor, half: int) -> Tensor:
    a, rest = t[..., :half], t[..., half:]
    return torch.cat((a * cos + rotate_half(a) * sin, rest), -1)


class MangaOcrNarSmallNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = _Encoder()
        self.memory = Memory()
        self.blocks = nn.ModuleList(Block() for _ in range(K))
        self.cond = nn.ModuleList(Cond() for _ in range(K))
        self.final_norms = nn.ModuleList([RMSNorm(D)])
        self.slot_pos = nn.Parameter(torch.zeros(SLOTS, D))
        self.tok = nn.Embedding(6819, D)                      # 6,817 characters + end of text + BLANK (input only)
        self.bias = nn.Parameter(torch.zeros(6818))
        hd = D // HEADS
        inv = 1.0 / (10000 ** (torch.arange(0, hd // 2, 2).float() / (hd // 2)))
        ang = torch.outer(torch.arange(SLOTS).float(), inv)
        self.register_buffer("rope_cos", torch.cat((ang, ang), -1).cos()[None, None], persistent=False)
        self.register_buffer("rope_sin", torch.cat((ang, ang), -1).sin()[None, None], persistent=False)
        self.ready = False

    @classmethod
    def load(cls, model_dir: Path, device="cuda", dtype=torch.float16) -> "MangaOcrNarSmallNet":
        from safetensors.torch import load_file
        model_dir = Path(model_dir)
        cfg = json.loads((model_dir / "config.json").read_text(encoding="utf-8"))
        net = cls()
        sd = {k: v for k, v in load_file(str(model_dir / "model.safetensors")).items() if k not in UNUSED}
        net.load_state_dict(sd, strict=True)
        mods = dict(net.named_modules())
        for name, eps in cfg["reparam"]["norm_eps"].items():
            mods[name].eps = eps
        net = net.to(device=device, dtype=dtype).eval()
        net.prepare()
        return net

    @torch.no_grad()
    def prepare(self):
        """Constants computed once in the run dtype: concatenated encoder fc1|fc3, RoPE table, static depth weights, and the
        first decoder block's self-attention on the image-independent slot input."""
        vit = self.encoder.vit
        dt = self.slot_pos.dtype
        self.fc13 = [torch.cat((b.mlp.fc1.weight, b.mlp.fc3.weight), 0).contiguous() for b in vit.blocks]
        self.rope_table = vit.rotary_pos_emb(325).float()
        self.alpha = self.memory.depth_logits.softmax(-1).to(dt)
        self.cos, self.sin = self.rope_cos.to(dt), self.rope_sin.to(dt)
        s0 = (self.slot_pos + self.tok.weight[6818])[None]
        blk, c = self.blocks[0], self.cond[0]
        B, S, Dm = s0.shape
        q, k, v = blk.qkv(c.n1(s0)).chunk(3, -1)
        q, k, v = blk.sq(blk.split(q)), blk.sk(blk.split(k)), blk.split(v)
        att = F.scaled_dot_product_attention(_rope(q, self.cos, self.sin, blk.hd // 2), _rope(k, self.cos, self.sin, blk.hd // 2), v)
        self.s_after_sa0 = (s0 + c.s1 * blk.o1(att.transpose(1, 2).reshape(B, S, Dm))).contiguous()
        self.ready = True

    def forward(self, P: Tensor, V: Tensor, R: Tensor, C: Tensor, H: Tensor, W: Tensor) -> Tensor:
        """P [B,324,588] patches, V [B,324] bool valid, R/C [B,324] long patch row/column, H/W [B] long grid size
        -> argmax ids [B, 65]."""
        vit = self.encoder.vit
        B, N, _ = P.shape
        pe = vit.patch_embed.patchifier
        x = pe.norm(F.linear(P, pe.proj.weight.flatten(1), pe.proj.bias))
        emb = torch.stack((self.rope_table[R], self.rope_table[C]), -1).flatten(-2)
        cos = torch.cat((emb.cos(), emb.cos()), -1)[:, :, None]
        sin = torch.cat((emb.sin(), emb.sin()), -1)[:, :, None]
        mask = V[:, None, None, :]
        hd = ENC_DIM // ENC_HEADS
        states = [x]
        for blk, w13 in zip(vit.blocks, self.fc13):
            q, k, v = blk.attn.qkv(blk.norm1(x)).view(B, N, 3, ENC_HEADS, hd).unbind(2)
            q = (q.float() * cos + rotate_half(q.float()) * sin).to(x.dtype)
            k = (k.float() * cos + rotate_half(k.float()) * sin).to(x.dtype)
            att = F.scaled_dot_product_attention(q.transpose(1, 2), k.transpose(1, 2), v.transpose(1, 2), attn_mask=mask)
            x = x + blk.attn.proj(att.transpose(1, 2).reshape(B, N, ENC_DIM))
            g, u = F.linear(blk.norm2(x), w13).split(ENC_FFN, -1)
            x = x + blk.mlp.fc2(F.silu(g) * u)
            states.append(x)
        states[-1] = vit.post_trunk_norm(x)
        mem = self.memory
        h12 = states[-1]
        base = mem.bridge(h12) + mem.pos(mem.fourier(R, C, H, W).to(h12.dtype))
        Hn = torch.stack([nm(s) for nm, s in zip(mem.norms, states[:-1])], 0)
        f = torch.einsum("jl,lbnd->jbnd", self.alpha, Hn)
        mems = base[None] + mem.gamma[:, None, None] * mem.wo(f)
        mems = torch.cat((mem.null.expand(mems.shape[0], B, -1, -1), mems), 2)
        kvs = [self.blocks[j].memory_kv(m) for j, m in enumerate(mems.unbind(0))]
        km = torch.cat((torch.ones(B, 2, dtype=torch.bool, device=V.device), V), 1)[:, None, None, :]
        s = self.s_after_sa0.expand(B, -1, -1)
        S, Dm = s.shape[1], s.shape[2]
        for i in range(K):
            blk, c = self.blocks[i], self.cond[i]
            if i > 0:
                q, k, v = blk.qkv(c.n1(s)).chunk(3, -1)
                q, k, v = blk.sq(blk.split(q)), blk.sk(blk.split(k)), blk.split(v)
                half = blk.hd // 2
                att = F.scaled_dot_product_attention(_rope(q, self.cos, self.sin, half), _rope(k, self.cos, self.sin, half), v)
                s = s + c.s1 * blk.o1(att.transpose(1, 2).reshape(B, S, Dm))
            q = blk.cq(blk.split(blk.q(c.n2(s))))
            att = F.scaled_dot_product_attention(q, *kvs[i], attn_mask=km)
            s = s + c.s2 * blk.o2(att.transpose(1, 2).reshape(B, S, Dm))
            g, u = blk.gate_up(c.n3(s)).chunk(2, -1)
            s = s + c.s3 * blk.down(F.silu(g) * u)
        return (F.linear(self.final_norms[0](s), self.tok.weight[:6818]) + self.bias).argmax(-1)
