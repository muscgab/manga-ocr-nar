"""GPU preprocessing for the CUDA backend: the same pixels as preprocess.preprocess (Pillow BICUBIC re-implemented with Pillow's
8-bit fixed-point arithmetic, border median, canvas, normalisation, patch layout), bit for bit. Only the scalar geometry and the
small resize coefficient tables are computed on the CPU."""
from __future__ import annotations

import math

import numpy as np
import torch

from . import preprocess as M

PRECISION_BITS = 22


def _bicubic(x):
    a = -0.5
    x = np.abs(x)
    return np.where(x < 1.0, ((a + 2.0) * x - (a + 3.0)) * x * x + 1,
                    np.where(x < 2.0, (((x - 5) * x + 8) * x - 4) * a, 0.0))


def pil_coeffs(in_size: int, out_size: int):
    """-> xmin [out] int64, kk [out, ksize] int64 (fixed point), ksize; exactly Pillow's precompute_coeffs + normalize_coeffs_8bpc."""
    scale = float(in_size) / out_size
    filterscale = max(scale, 1.0)
    support = 2.0 * filterscale
    ksize = int(math.ceil(support)) * 2 + 1
    xx = np.arange(out_size, dtype=np.float64)
    center = (xx + 0.5) * scale
    ss = 1.0 / filterscale
    xmin = np.maximum(np.trunc(center - support + 0.5).astype(np.int64), 0)          # C (int) cast truncates toward zero
    xmax = np.minimum(np.trunc(center + support + 0.5).astype(np.int64), in_size) - xmin
    x = np.arange(ksize, dtype=np.float64)[None, :]
    w = _bicubic((x + xmin[:, None] - center[:, None] + 0.5) * ss)
    live = x < xmax[:, None]
    w = np.where(live, w, 0.0)
    # Pillow sums the weights sequentially (ww += w); numpy's pairwise sum can differ in the last bit -> accumulate left to right
    ww = np.zeros(out_size)
    for j in range(ksize):
        ww = ww + w[:, j]
    w = np.where(ww[:, None] != 0.0, w / np.where(ww == 0.0, 1.0, ww)[:, None], w)
    k = np.where(w < 0, np.trunc(-0.5 + w * (1 << PRECISION_BITS)), np.trunc(0.5 + w * (1 << PRECISION_BITS))).astype(np.int64)
    return xmin, k, ksize


class GpuPreprocess:
    def __init__(self, budget: int = 324, device: str = "cuda"):
        self.budget, self.dev = budget, torch.device(device)
        self.mean = torch.tensor(M.MEAN, device=self.dev)
        self.std = torch.tensor(M.STD, device=self.dev)
        # a 1-element device tensor, not a Python scalar: PyTorch CUDA turns "x / scalar" into "x * (1 / scalar)", which differs from
        # numpy's true division in the last bit (win1060 2026-10-12: 7,789/7,789 patch tensors off by ulps, texts unchanged)
        self.c255 = torch.tensor([255.0], device=self.dev)
        idx = torch.arange(budget, device=self.dev)
        self.idx = idx
        self._coef = {}

    def _pass(self, x: torch.Tensor, in_size: int, out_size: int, dim: int) -> torch.Tensor:
        """one resample pass along dim (0 = rows / vertical, 1 = columns / horizontal) of a uint8 HWC tensor"""
        key = (in_size, out_size)
        if key not in self._coef:
            xmin, k, ksize = pil_coeffs(in_size, out_size)
            src = np.minimum(xmin[:, None] + np.arange(ksize)[None, :], in_size - 1)                      # dead taps have k == 0
            self._coef[key] = (torch.from_numpy(src).to(self.dev), torch.from_numpy(k).to(self.dev))
            if len(self._coef) > 4096:
                self._coef.pop(next(iter(self._coef)))
        src, k = self._coef[key]
        xi = x.to(torch.int64)
        if dim == 1:
            g = xi[:, src]                                                    # [H, out, K, 3]
            acc = (g * k[None, :, :, None]).sum(2)
        else:
            g = xi[src]                                                       # [out, K, W, 3]
            acc = (g * k[:, :, None, None]).sum(1)
        acc = acc + (1 << (PRECISION_BITS - 1))
        return torch.clamp(acc >> PRECISION_BITS, 0, 255).to(torch.uint8)

    @torch.inference_mode()
    def __call__(self, img):
        if not isinstance(img, torch.Tensor):
            img = torch.from_numpy(np.array(img.convert("RGB") if hasattr(img, "convert") else img, dtype=np.uint8))
        x = img.to(self.dev, non_blocking=True)
        H, W = int(x.shape[0]), int(x.shape[1])
        s, h, w = M.pad_grid(H, W, self.budget)
        rw, rh = max(1, min(w * 14, round(W * s))), max(1, min(h * 14, round(H * s)))
        small = x
        if rw != W:
            small = self._pass(small, W, rw, 1)
        if rh != H:
            small = self._pass(small, H, rh, 0)
        border = torch.cat([small[0], small[-1], small[:, 0], small[:, -1]], 0)        # [n, 3], same order as numpy
        srt = border.sort(0).values; n = srt.shape[0]
        med = srt[n // 2] if n % 2 else ((srt[n // 2 - 1].double() + srt[n // 2].double()) / 2).to(torch.uint8)
        canvas = med.view(1, 1, 3).expand(h * 14, w * 14, 3).clone()
        canvas[:rh, :rw] = small
        arr = (canvas.to(torch.float32) / self.c255 - self.mean) / self.std
        P = torch.zeros(self.budget, 588, device=self.dev)
        P[: h * w] = arr.view(h, 14, w, 14, 3).permute(0, 2, 4, 1, 3).reshape(h * w, 588)
        V = self.idx < h * w
        R = torch.where(V, self.idx // w, 0)
        C = torch.where(V, self.idx % w, 0)
        return P, V, R, C, (h, w)
