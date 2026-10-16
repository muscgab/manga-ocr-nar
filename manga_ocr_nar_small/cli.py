"""manga-ocr-nar-small [--backend auto|cuda|onnx|coreml] [--model-dir DIR] [--int8 auto|u8s8|u8u8] crop.png ...  -> one
"path<TAB>text" line per crop; all crops given in one call are run as one batch. --int8 only applies to the ONNX backend of
manga-ocr-nar-small-distil."""
from __future__ import annotations

import argparse
import sys

from . import MangaOcrNarSmall


def main(argv=None):
    ap = argparse.ArgumentParser(prog="manga-ocr-nar-small")
    ap.add_argument("images", nargs="+")
    ap.add_argument("--backend", default="auto", choices=("auto", "cuda", "onnx", "coreml"))
    ap.add_argument("--model-dir", default=None)
    ap.add_argument("--int8", default=None, choices=("auto", "u8s8", "u8u8"))
    a = ap.parse_args(argv)
    ocr = MangaOcrNarSmall(a.backend, a.model_dir, **({"int8": a.int8} if a.int8 else {}))
    out = sys.stdout
    if hasattr(out, "reconfigure"):
        out.reconfigure(encoding="utf-8")
    for path, text in zip(a.images, ocr(list(a.images))):
        out.write(f"{path}\t{text}\n")


if __name__ == "__main__":
    main()
