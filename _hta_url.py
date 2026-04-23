"""Resolve the HTA app's index.html for selenium scripts and ad-hoc tests.

The legacy root-level Python scripts (not the canonical Jest suite under
``tests/``) used to hardcode an absolute drive-prefixed path to the app's
index.html, which made every script clone-broken and tripped Sentinel's
hardcoded-path rule. This helper restores portability.

Resolution order:
  1. ``HTA_INDEX_PATH`` env var (any user-chosen location)
  2. Repo-root ``index.html`` (the canonical app, ships with this repo)
  3. The legacy ``Downloads/HTA`` location under the user's home dir

Fails closed if none of the candidates exist.
"""

from __future__ import annotations

import os
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent


def hta_index_path() -> Path:
    """Return an absolute Path to the HTA app's index.html."""
    candidates: list[Path] = []
    env = os.environ.get("HTA_INDEX_PATH", "")
    if env:
        candidates.append(Path(env).expanduser())
    candidates.append(_REPO_ROOT / "index.html")
    candidates.append(Path.home() / "Downloads" / "HTA" / "index.html")

    for c in candidates:
        if c.is_file():
            return c.resolve()

    searched = ", ".join(str(c) for c in candidates)
    raise FileNotFoundError(
        f"HTA index.html not found. Set HTA_INDEX_PATH env var, or place the "
        f"file at the repo root, or restore ~/Downloads/HTA/. Searched: {searched}"
    )


def hta_index_url() -> str:
    """Return a ``file://`` URI suitable for ``driver.get(...)``."""
    return hta_index_path().as_uri()
