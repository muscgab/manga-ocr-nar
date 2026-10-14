"""Old import name of manga_ocr_nar_small (the project was renamed from mangaocr-nar-small to manga-ocr-nar-small on
2026-10-14). Kept so that existing code keeps working; new code should use `from manga_ocr_nar_small import MangaOcrNarSmall`."""
import warnings

from manga_ocr_nar_small import *  # noqa: F401,F403
from manga_ocr_nar_small import MangaOcrNarSmall, __version__  # noqa: F401

warnings.warn("mangaocr_nar_small was renamed to manga_ocr_nar_small; please update the import", DeprecationWarning, stacklevel=2)
