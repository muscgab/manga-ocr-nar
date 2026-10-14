"""manga-ocr-nar-small [--backend auto|cuda|onnx|coreml] [--model-dir DIR] crop.png ...  -> one "path<TAB>text" line per crop;
all crops given in one call are run as one batch."""
from __future__ import annotations

import argparse
import sys

from . import MangaOcrNarSmall


def main(argv=None):
    ap = argparse.ArgumentParser(prog="manga-ocr-nar-small")
    ap.add_argument("images", nargs="+")
    ap.add_argument("--backend", default="auto", choices=("auto", "cuda", "onnx", "coreml"))
    ap.add_argument("--model-dir", default=None)
    a = ap.parse_args(argv)
    ocr = MangaOcrNarSmall(a.backend, a.model_dir)
    out = sys.stdout
    if hasattr(out, "reconfigure"):
        out.reconfigure(encoding="utf-8")
    for path, text in zip(a.images, ocr(list(a.images))):
        out.write(f"{path}\t{text}\n")


if __name__ == "__main__":
    main()
