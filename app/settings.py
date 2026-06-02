import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

SETTINGS_FILE = Path(__file__).resolve().parent.parent / "data" / "settings.json"

DEFAULT_SETTINGS = {
    "llm": {
        "model": "opencode/deepseek-v4-flash-free",
        "enabled": True,
    },
    "rag": {
        "enabled": True,
        "k": 3,
    },
    "colors": {
        "semis_serre_chaude": "#e65100",
        "semis_serre_froide": "#7cb342",
        "semis_direct": "#1565c0",
        "semis_interieur": "#7b1fa2",
        "plantation": "#2e7d32",
        "action": "#c62828",
        "bouturage": "#ad1457",
        "recolte": "#f9a825",
    },
    "labels": {
        "semis_serre_chaude": "Semis serre chaude",
        "semis_serre_froide": "Semis serre froide",
        "semis_direct": "Semis direct",
        "semis_interieur": "Semis intérieur + repiquage",
        "plantation": "Plantation",
        "action": "Action à mener",
        "bouturage": "Bouturage",
        "recolte": "Récolte",
    },
}

_settings_cache = None


def load() -> dict:
    global _settings_cache
    if _settings_cache is not None:
        return _settings_cache
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE) as f:
                data = json.load(f)
            merged = _merge(DEFAULT_SETTINGS, data)
            _settings_cache = merged
            return merged
        except Exception as e:
            logger.warning(f"Erreur chargement settings: {e}")
    _settings_cache = dict(DEFAULT_SETTINGS)
    return _settings_cache


def save(data: dict):
    global _settings_cache
    merged = _merge(DEFAULT_SETTINGS, data)
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_FILE, "w") as f:
        json.dump(merged, f, indent=2)
    _settings_cache = merged
    logger.info("Settings sauvegardés")


def _merge(defaults: dict, overrides: dict) -> dict:
    result = dict(defaults)
    for k, v in overrides.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _merge(result[k], v)
        else:
            result[k] = v
    return result


def reset():
    global _settings_cache
    _settings_cache = dict(DEFAULT_SETTINGS)
    save(_settings_cache)
