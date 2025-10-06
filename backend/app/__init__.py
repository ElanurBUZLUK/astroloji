"""Astro backend application package."""
import sys as _sys

# Provide a backwards compatible alias so legacy imports using `app.*` continue
# to resolve even though the package lives under `backend.app`.
_sys.modules.setdefault("app", _sys.modules[__name__])

__all__ = []
