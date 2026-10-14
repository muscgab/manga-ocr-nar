"""NVIDIA GPU backend (PyTorch). One request = one call with all crops of a page:
the CPU copies the uint8 crops into pinned memory and queues everything without waiting (upload, GPU preprocessing written
straight into the input buffers of a captured CUDA graph, graph replay, copy of the 65 ids per crop back to pinned memory), then
sleeps on a blocking event and turns the ids into text. CUDA graphs are captured for batch sizes 1-16, 32 and 48 at start-up; a
page of b crops runs in the smallest size >= b (extra rows repeat the last crop and are dropped), more than 48 crops are split.
torch intra-op threads are set to 1 (idle OpenMP threads would otherwise spin)."""
from __future__ import annotations

import numpy as np
import torch

from ..gpu_preprocess import GpuPreprocess
from ..model import MangaOcrNarSmallNet

BUCKETS = tuple(range(1, 17)) + (32, 48)
BUDGET = 324


class CudaBackend:
    def __init__(self, model_dir, device: str = "cuda", fp16: bool = True, buckets=BUCKETS, threads: int = 1):
        torch.set_num_threads(threads)
        self.dev = torch.device(device)
        self.dt = torch.float16 if fp16 else torch.float32
        self.net = MangaOcrNarSmallNet.load(model_dir, self.dev, self.dt)
        self.pre = GpuPreprocess(BUDGET, device=str(self.dev))
        self.buckets = tuple(sorted(buckets))
        self.pool = torch.cuda.graph_pool_handle()
        self.graphs = {b: self._capture(b) for b in self.buckets}
        self.stage = torch.empty(0, dtype=torch.uint8).pin_memory()
        self.ids_host = torch.empty(self.buckets[-1], 65, dtype=torch.long).pin_memory()
        self.event = torch.cuda.Event(blocking=True)

    def _capture(self, b):
        d = self.dev
        buf = {"P": torch.zeros(b, BUDGET, 588, device=d, dtype=self.dt), "V": torch.ones(b, BUDGET, device=d, dtype=torch.bool),
               "R": torch.zeros(b, BUDGET, device=d, dtype=torch.long), "C": torch.zeros(b, BUDGET, device=d, dtype=torch.long),
               "H": torch.ones(b, device=d, dtype=torch.long), "W": torch.ones(b, device=d, dtype=torch.long)}
        s = torch.cuda.Stream(d)
        s.wait_stream(torch.cuda.current_stream(d))
        with torch.inference_mode(), torch.cuda.stream(s):
            for _ in range(2):
                self.net(buf["P"], buf["V"], buf["R"], buf["C"], buf["H"], buf["W"])
        torch.cuda.current_stream(d).wait_stream(s)
        g = torch.cuda.CUDAGraph()
        with torch.inference_mode(), torch.cuda.graph(g, pool=self.pool):
            out = self.net(buf["P"], buf["V"], buf["R"], buf["C"], buf["H"], buf["W"])
        torch.cuda.synchronize(d)
        return g, buf, out

    def _upload(self, arrs):
        need = sum(a.size for a in arrs)
        if self.stage.numel() < need:
            self.stage = torch.empty(int(need * 1.5), dtype=torch.uint8).pin_memory()
        out, off = [], 0
        for a in arrs:
            n = a.size
            self.stage[off:off + n].numpy()[:] = a.reshape(-1)
            out.append(self.stage[off:off + n].to(self.dev, non_blocking=True).view(a.shape))
            off += n
        return out

    @torch.inference_mode()
    def ids(self, arrs: list[np.ndarray]) -> np.ndarray:
        """uint8 HWC RGB crops -> ids [n, 65]"""
        top, rows = self.buckets[-1], []
        for i in range(0, len(arrs), top):
            rows.append(self._chunk(arrs[i:i + top]))
        return np.concatenate(rows) if rows else np.zeros((0, 65), np.int64)

    def _chunk(self, arrs):
        b = len(arrs)
        nb = next(x for x in self.buckets if x >= b)
        g, buf, out = self.graphs[nb]
        for j, x in enumerate(self._upload(arrs)):
            P, V, R, C, (h, w) = self.pre(x)
            buf["P"][j].copy_(P); buf["V"][j].copy_(V); buf["R"][j].copy_(R); buf["C"][j].copy_(C)
            buf["H"][j].fill_(h); buf["W"][j].fill_(w)
        if nb > b:                                                       # padding rows repeat the last real crop
            for k in ("P", "V", "R", "C", "H", "W"):
                buf[k][b:nb].copy_(buf[k][b - 1:b].expand(nb - b, *buf[k].shape[1:]))
        g.replay()
        self.ids_host[:nb].copy_(out, non_blocking=True)
        self.event.record()
        self.event.synchronize()
        return self.ids_host[:b].numpy().copy()
