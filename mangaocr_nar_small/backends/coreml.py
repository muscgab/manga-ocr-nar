"""Mac backend (CoreML on the GPU, macOS 15+, no torch). The package holds five functions with static batch sizes 1, 2, 4, 8 and 16
that share one set of weights. CoreML re-encodes the whole compute graph on the CPU for every call, so a page is sent in as few
calls as possible: the crops of a page are split into batch sizes with the lowest total measured time (padding allowed), each
function is loaded and run once at start-up, preprocessing is numpy (preprocess.py)."""
from __future__ import annotations

import numpy as np
from PIL import Image

from ..preprocess import BUDGET, FEAT, preprocess

MLPACKAGE = "coreml/mangaocr_nar_small_fp16.mlpackage"
SIZES = (1, 2, 4, 8, 16)
COST = {1: 14.7, 2: 23.1, 4: 39.6, 8: 71.7, 16: 134.7}   # ms per call, M1 Pro GPU


class CoreMLBackend:
    def __init__(self, model_dir, units: str = "gpu"):
        import CoreML
        import Foundation
        pkg = model_dir / MLPACKAGE
        mlc = pkg.with_suffix(".mlmodelc")
        if not mlc.exists():                                   # one-time on-device compile, cached next to the package
            tmp, err = CoreML.MLModel.compileModelAtURL_error_(Foundation.NSURL.fileURLWithPath_(str(pkg)), None)
            if err is not None:
                raise RuntimeError(err)
            Foundation.NSFileManager.defaultManager().moveItemAtURL_toURL_error_(tmp, Foundation.NSURL.fileURLWithPath_(str(mlc)), None)
        unit = {"gpu": CoreML.MLComputeUnitsCPUAndGPU, "ane": CoreML.MLComputeUnitsCPUAndNeuralEngine,
                "cpu": CoreML.MLComputeUnitsCPUOnly, "all": CoreML.MLComputeUnitsAll}[units]
        self.fn = {}
        for b in SIZES:
            cfg = CoreML.MLModelConfiguration.alloc().init()
            cfg.setComputeUnits_(unit)
            cfg.setFunctionName_(f"b{b}")
            model, err = CoreML.MLModel.modelWithContentsOfURL_configuration_error_(Foundation.NSURL.fileURLWithPath_(str(mlc)), cfg, None)
            if err is not None:
                raise RuntimeError(err)
            spec = {"P": ((b, BUDGET, FEAT), np.float32), "V": ((b, BUDGET), np.float32), "R": ((b, BUDGET), np.int32),
                    "C": ((b, BUDGET), np.int32), "H": ((b,), np.int32), "W": ((b,), np.int32)}
            views, feats = {}, {}
            for k, (shape, dt) in spec.items():
                ml = CoreML.MLMultiArrayDataTypeFloat32 if dt == np.float32 else CoreML.MLMultiArrayDataTypeInt32
                a, err = CoreML.MLMultiArray.alloc().initWithShape_dataType_error_(list(shape), ml, None)
                views[k] = np.frombuffer(a.dataPointer().as_buffer(int(np.prod(shape)) * 4), dt).reshape(shape)
                feats[k] = CoreML.MLFeatureValue.featureValueWithMultiArray_(a)
            prov, err = CoreML.MLDictionaryFeatureProvider.alloc().initWithDictionary_error_(feats, None)
            self.fn[b] = (model, views, prov)
        self.plan = {0: []}                                    # cheapest batch-size sequence for n crops
        for n in range(1, 49):
            self.plan[n] = min(([b] + self.plan[max(0, n - b)] for b in SIZES), key=lambda q: sum(COST[x] for x in q))
        blank = np.full((32, 32, 3), 255, np.uint8)
        for b in SIZES:                                        # first call of each function is slow; do it now
            self._run(b, [blank])

    def _run(self, b, arrs):
        model, views, prov = self.fn[b]
        for j, a in enumerate(arrs):
            preprocess(Image.fromarray(a), {k: (v[j:j + 1] if v.ndim == 1 else v[j]) for k, v in views.items()})
        n = len(arrs)
        for v in views.values():                               # padding rows repeat the last crop
            v[n:] = v[n - 1]
        out, err = model.predictionFromFeatures_error_(prov, None)
        if err is not None:
            raise RuntimeError(err)
        m = out.featureValueForName_("ids").multiArrayValue()
        return np.frombuffer(m.dataPointer().as_buffer(b * 65 * 4), np.int32).reshape(b, 65)[:n].copy()

    def ids(self, arrs: list[np.ndarray]) -> np.ndarray:
        rows, i = [], 0
        while i < len(arrs):
            for b in self.plan[min(len(arrs) - i, 48)]:
                part = arrs[i:i + b]
                if part:
                    rows.append(self._run(b, part))
                i += len(part)
        return np.concatenate(rows) if rows else np.zeros((0, 65), np.int64)
