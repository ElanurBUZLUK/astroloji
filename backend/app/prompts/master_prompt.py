"""Loader for the master system/developer prompts injected into LLM calls."""
from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from loguru import logger

try:  # pragma: no cover - optional dependency
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None  # type: ignore

DEFAULT_SYSTEM_PROMPT = (
    "You are the Astroloji Master Orchestrator. Provide grounded astrological guidance that blends natal "
    "interpretation, transit context, and retrieved knowledge. Maintain intellectual honesty, cite evidence "
    "verbatim, and clearly flag gaps or uncertainties. Prefer concise structure over verbosity, surface the "
    "most material insights first, and respect localisation settings."
)

DEFAULT_DEVELOPER_PROMPT = (
    "Implementation guardrails:\n"
    "- Treat retrieved documents, chart context, and safety policies as authoritative.\n"
    "- Never fabricate citations or planetary data; request recalculation if context is missing.\n"
    "- When providing deployment or operational guidance, ensure the relevant deploy.md instructions have "
    "been read and applied.\n"
    "- Honour degrade policies, latency budgets, and fallback pathways signalled by the orchestrator."
)


@dataclass(frozen=True)
class MasterPrompt:
    """In-memory representation of the master prompt bundle."""

    system: str
    developer: Optional[str] = None


class MasterPromptLoader:
    """Loads and caches master system/developer prompts from disk."""

    def __init__(
        self,
        prompt_path: str | Path | None = None,
        deploy_path: str | Path | None = None,
    ) -> None:
        base_dir = Path(__file__).resolve().parent
        if prompt_path is None:
            prompt_path = base_dir / "master_prompt.yaml"
        self._prompt_path = Path(prompt_path).expanduser()

        self._deploy_path = Path(deploy_path).expanduser() if deploy_path else self._discover_deploy_doc(base_dir)
        self._lock = threading.Lock()
        self._cached: Optional[MasterPrompt] = None

    def load(self, *, force_reload: bool = False) -> MasterPrompt:
        """Return the cached prompt contents, optionally forcing a reload."""
        with self._lock:
            if self._cached is not None and not force_reload:
                return self._cached
            prompt = self._load_from_disk()
            self._cached = prompt
            return prompt

    def _load_from_disk(self) -> MasterPrompt:
        system_text = DEFAULT_SYSTEM_PROMPT
        developer_text = DEFAULT_DEVELOPER_PROMPT

        if self._prompt_path.exists():
            try:
                payload = self._read_prompt_file(self._prompt_path)
                system_text = payload.get("system") or system_text
                developer_text = payload.get("developer") or developer_text
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.warning(
                    "Failed to load master prompt file.",
                    extra={"path": str(self._prompt_path), "error": str(exc)},
                )

        developer_text = self._attach_deploy_rule(developer_text)
        return MasterPrompt(system=system_text.strip(), developer=developer_text.strip() if developer_text else None)

    def _attach_deploy_rule(self, developer_text: Optional[str]) -> Optional[str]:
        if not self._deploy_path:
            return developer_text

        if not self._deploy_path.exists():
            return developer_text

        note = (
            "\n\nDeployment guardrail:\n"
            f"- Before describing release, canary, or rollback actions, read and apply '{self._deploy_path}'."
        )
        return (developer_text or "") + note

    def _read_prompt_file(self, path: Path) -> dict[str, str]:
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            return {}
        if path.suffix.lower() in {".yaml", ".yml"} and yaml is not None:
            data = yaml.safe_load(text)  # type: ignore[arg-type]
            if isinstance(data, dict):
                return {str(k): str(v) for k, v in data.items() if v is not None}
            return {}
        if path.suffix.lower() == ".json":
            data = json.loads(text)
            if isinstance(data, dict):
                return {str(k): str(v) for k, v in data.items() if v is not None}
            return {}
        # Fallback: simple key:value parsing
        payload: dict[str, str] = {}
        current_key: Optional[str] = None
        buffer: list[str] = []
        for line in text.splitlines():
            if ":" in line and line.strip().split(":", 1)[0].isidentifier():
                if current_key is not None and buffer:
                    payload[current_key] = "\n".join(buffer).strip()
                current_key, rest = line.split(":", 1)
                current_key = current_key.strip()
                buffer = [rest.strip()]
            else:
                buffer.append(line)
        if current_key is not None and buffer:
            payload[current_key] = "\n".join(buffer).strip()
        return payload

    def _discover_deploy_doc(self, base_dir: Path) -> Optional[Path]:
        # Search upwards for deploy.md to avoid hard-coding repository layout.
        for candidate in [
            base_dir / "deploy.md",
            base_dir.parent / "deploy.md",
            base_dir.parent.parent / "deploy.md",
            base_dir.parent.parent / "astroloji2" / "deploy.md",
        ]:
            if candidate.exists():
                return candidate
        return None


_GLOBAL_LOADER: Optional[MasterPromptLoader] = None


def get_master_prompt_loader() -> MasterPromptLoader:
    """Return a singleton loader configured from application settings when available."""
    global _GLOBAL_LOADER
    if _GLOBAL_LOADER is not None:
        return _GLOBAL_LOADER

    try:
        from backend.app.config import settings  # pylint: disable=import-error
    except Exception:  # pragma: no cover - settings unavailable during import
        _GLOBAL_LOADER = MasterPromptLoader()
        return _GLOBAL_LOADER

    prompt_path = getattr(settings, "MASTER_PROMPT_PATH", None)
    deploy_path = getattr(settings, "MASTER_PROMPT_DEPLOY_PATH", None)
    _GLOBAL_LOADER = MasterPromptLoader(prompt_path=prompt_path, deploy_path=deploy_path)
    return _GLOBAL_LOADER

