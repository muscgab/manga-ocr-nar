"""CPU backend (onnxruntime, fp32 ONNX, one crop per run)."""
from __future__ import annotations

import os

import numpy as np
from PIL import Image

from ..preprocess import empty_inputs, preprocess

ONNX_FILE = "onnx/mangaocr_nar_small_fp32.onnx"


class OnnxBackend:
    def __init__(self, model_dir, threads: int | None = None):
        import onnxruntime as ort
        so = ort.SessionOptions()
        so.intra_op_num_threads = threads or min(8, os.cpu_count() or 1)
        so.inter_op_num_threads = 1
        so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        self.sess = ort.InferenceSession(str(model_dir / ONNX_FILE), so, providers=["CPUExecutionProvider"])
        self.buf = empty_inputs()

    def ids(self, arrs: list[np.ndarray]) -> np.ndarray:
        rows = []
        for a in arrs:
            preprocess(Image.fromarray(a), self.buf)
            rows.append(np.asarray(self.sess.run(None, self.buf)[0]).reshape(65))
        return np.stack(rows) if rows else np.zeros((0, 65), np.int64)
