"""manga-ocr-nar: Japanese manga text-box OCR, non-autoregressive (manga-ocr-nar-small, manga-ocr-nar-small-distil).

    from manga_ocr_nar_small import MangaOcrNarSmall
    ocr = MangaOcrNarSmall()                 # backend "auto" | "cuda" | "onnx" | "coreml"
    ocr("crop.png")                          # one crop -> str
    ocr([crop1, crop2, ...])                 # the crops of one page -> list[str], run as one batch
    MangaOcrNarSmall(model_dir="manga-ocr-nar-small-distil")    # the distilled model: same API, model chosen by its files

Crops may be file paths, PIL images or uint8 HWC RGB arrays."""
from __future__ import annotations

import os
import platform
from pathlib import Path

import numpy as np
from PIL import Image

from .vocab import Vocab

__version__ = "1.1.0"
__all__ = ["MangaOcrNarSmall"]
DEFAULT_DIR = Path(os.environ.get("MANGA_OCR_NAR_SMALL_DIR") or os.environ.get("MANGAOCR_NAR_SMALL_DIR")  # old name still read
                   or Path(__file__).resolve().parent.parent)


def _auto(model_dir: Path) -> str:
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
    except ImportError:
        pass
    if (model_dir / "coreml").is_dir() and platform.system() == "Darwin" and int(platform.mac_ver()[0].split(".")[0] or 0) >= 15:
        try:
            import CoreML  # noqa: F401
            return "coreml"
        except ImportError:
            pass
    return "onnx"


def _rgb(x) -> np.ndarray:
    if isinstance(x, np.ndarray):
        return np.ascontiguousarray(x if x.ndim == 3 else np.stack([x] * 3, -1), dtype=np.uint8)
    if not isinstance(x, Image.Image):
        with Image.open(x) as im:
            im.load()
            x = im.convert("RGB")
    return np.asarray(x.convert("RGB"), np.uint8)


class MangaOcrNarSmall:
    def __init__(self, backend: str = "auto", model_dir=None, **kwargs):
        self.model_dir = Path(model_dir) if model_dir else DEFAULT_DIR
        if not (self.model_dir / "nar_vocabulary_6817.json").exists():
            raise FileNotFoundError(f"model files not found in {self.model_dir}; pass model_dir= (the downloaded repository) "
                                    "or set MANGA_OCR_NAR_SMALL_DIR")
        self.vocab = Vocab(self.model_dir / "nar_vocabulary_6817.json")
        self.backend_name = _auto(self.model_dir) if backend == "auto" else backend
        if self.backend_name == "cuda":
            from .backends.cuda import CudaBackend
            self.backend = CudaBackend(self.model_dir, **kwargs)
        elif self.backend_name == "onnx":
            from .backends.onnx import OnnxBackend
            self.backend = OnnxBackend(self.model_dir, **kwargs)
        elif self.backend_name == "coreml":
            from .backends.coreml import CoreMLBackend
            self.backend = CoreMLBackend(self.model_dir, **kwargs)
        else:
            raise ValueError(f"unknown backend {backend!r}")

    def __call__(self, images):
        single = not isinstance(images, (list, tuple))
        arrs = [_rgb(x) for x in ([images] if single else images)]
        texts = self.vocab.decode(self.backend.ids(arrs).tolist())
        return texts[0] if single else texts
