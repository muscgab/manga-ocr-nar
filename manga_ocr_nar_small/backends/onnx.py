"""CPU backend (onnxruntime, one crop per run). manga-ocr-nar-small: fp32 ONNX. manga-ocr-nar-small-distil: int8 ONNX, in two
encodings of the same weights listed in config.json "onnx": u8s8 (ARM, x86 with VNNI) and u8u8 (x86 without VNNI, where
onnxruntime's u8s8 kernels can saturate and change outputs); int8="auto" picks by CPU (an x86 CPU it cannot inspect gets u8u8)."""
from __future__ import annotations

import json
import os
import platform

import numpy as np
from PIL import Image

from ..preprocess import empty_inputs, preprocess

ONNX_FILE = "onnx/mangaocr_nar_small_fp32.onnx"


def _x86_without_vnni() -> bool:
    if platform.machine().lower() not in ("x86_64", "amd64", "i386", "i686", "x86"):
        return False
    try:
        with open("/proc/cpuinfo", encoding="utf-8") as f:
            flags = f.read()
    except OSError:
        return True
    return not ("avx512_vnni" in flags or "avx_vnni" in flags)


def onnx_file(model_dir, int8: str = "auto") -> str:
    files = json.loads((model_dir / "config.json").read_text(encoding="utf-8")).get("onnx")
    if not files:
        return ONNX_FILE
    if int8 == "auto":
        int8 = "u8u8" if _x86_without_vnni() else "u8s8"
    if int8 not in files:
        raise ValueError(f"int8 must be 'auto' or one of {sorted(files)}, got {int8!r}")
    return files[int8]


class OnnxBackend:
    def __init__(self, model_dir, threads: int | None = None, int8: str = "auto"):
        import onnxruntime as ort
        so = ort.SessionOptions()
        so.intra_op_num_threads = threads or min(8, os.cpu_count() or 1)
        so.inter_op_num_threads = 1
        so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        self.file = onnx_file(model_dir, int8)
        self.sess = ort.InferenceSession(str(model_dir / self.file), so, providers=["CPUExecutionProvider"])
        self.unpadded = "V" not in {i.name for i in self.sess.get_inputs()}   # distil graph: only the valid patches
        self.buf = empty_inputs()

    def ids(self, arrs: list[np.ndarray]) -> np.ndarray:
        rows = []
        for a in arrs:
            preprocess(Image.fromarray(a), self.buf)
            b = self.buf
            if self.unpadded:
                n = int(b["H"][0]) * int(b["W"][0])
                b = {"P": b["P"][:n], "R": b["R"][:n], "C": b["C"][:n], "H": b["H"], "W": b["W"]}
            rows.append(np.asarray(self.sess.run(None, b)[0]).reshape(65))
        return np.stack(rows) if rows else np.zeros((0, 65), np.int64)
