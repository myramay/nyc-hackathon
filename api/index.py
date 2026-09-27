"""Vercel entry point: serves the whole app (API + web/ pages) from core.api.

Vercel's filesystem is read-only except /tmp, so the geocode and lottery caches are
copied there and read/written from there. Locally, run uvicorn core.api:app as usual.
"""
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

if os.environ.get("VERCEL"):
    import core.geo as _geo
    import vacancies.feed as _feed

    for _mod in (_geo, _feed):
        _tmp = Path("/tmp") / _mod.CACHE.name
        if not _tmp.exists() and _mod.CACHE.exists():
            shutil.copy(_mod.CACHE, _tmp)
        _mod.CACHE = _tmp

from core.api import app  # noqa: E402,F401
