import httpx
import os
import asyncio
import subprocess
import logging
import signal
import sys
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

OPENCODE_URL = os.getenv("OPENCODE_SERVER_URL", "http://localhost:4096")
OPENCODE_PORT = os.getenv("OPENCODE_SERVER_PORT", "4096")
OPENCODE_PASSWORD = os.getenv("OPENCODE_SERVER_PASSWORD", "")
OPENCODE_BIN = os.getenv("OPENCODE_BIN", "opencode")
OPENCODE_MODEL = os.getenv("OPENCODE_MODEL", "opencode/deepseek-v4-flash-free")

_server_process: subprocess.Popen | None = None

GARDEN_SYSTEM_PROMPT = (
    "Tu es un expert en jardinage en sol vivant, permaculture et culture potagère. "
    "Tu réponds aux questions sur la culture des légumes, les maladies, les traitements naturels, "
    "le calendrier de culture, les associations de plantes, la rotation des cultures, "
    "les engrais verts, le compost, le paillage, et toutes les techniques de jardinage naturel. "
    "Donne des conseils pratiques, précis et adaptés à chaque situation. "
    "Réponds en français. Sois concis et utile."
)


def _headers():
    h = {"Content-Type": "application/json"}
    if OPENCODE_PASSWORD:
        import base64

        token = base64.b64encode(f"opencode:{OPENCODE_PASSWORD}".encode()).decode()
        h["Authorization"] = f"Basic {token}"
    return h


async def _health_check() -> bool:
    try:
        async with httpx.AsyncClient(timeout=3) as cl:
            r = await cl.get(
                urljoin(OPENCODE_URL, "/global/health"), headers=_headers()
            )
            ok = r.status_code == 200
            logger.debug(
                f"Health check {OPENCODE_URL}: HTTP {r.status_code} {'OK' if ok else 'FAIL'}"
            )
            return ok
    except Exception as e:
        logger.warning(f"Health check échoué ({OPENCODE_URL}): {e}")
        return False


def _start_server_process() -> tuple[bool, str]:
    global _server_process
    try:
        from . import settings as app_settings

        model = app_settings.load()["llm"]["model"]
        logger.info(f"Modèle LLM configuré: {model}")
        _server_process = subprocess.Popen(
            [
                OPENCODE_BIN,
                "serve",
                "--pure",
                "--model",
                model,
                "--port",
                OPENCODE_PORT,
                "--hostname",
                "127.0.0.1",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            preexec_fn=os.setsid if sys.platform != "win32" else None,
        )
        logger.info(f"opencode serve démarré (PID {_server_process.pid})")
        return True, f"PID {_server_process.pid}"
    except FileNotFoundError:
        return (
            False,
            f"Commande '{OPENCODE_BIN}' introuvable. Installe opencode ou vérifie le PATH.",
        )
    except Exception as e:
        logger.error(f"Échec démarrage opencode serve: {e}")
        return False, str(e)


async def ensure_server(timeout: int = 30) -> dict:
    if await _health_check():
        logger.info("Serveur opencode déjà en ligne")
        return {"ok": True, "started": False, "message": "Serveur déjà en ligne"}

    logger.info("Tentative de démarrage opencode serve...")
    ok, msg = _start_server_process()
    if not ok:
        logger.error(f"Impossible de démarrer: {msg}")
        return {"ok": False, "message": msg}

    logger.info(f"Attente du serveur ({timeout}s)...")
    for i in range(timeout):
        await asyncio.sleep(1)
        if await _health_check():
            logger.info(f"Serveur opencode démarré après {i + 1}s")
            return {"ok": True, "started": True, "message": f"Serveur démarré ({msg})"}
    logger.error(f"Serveur pas répond après {timeout}s")
    return {"ok": False, "message": "Le serveur n'a pas répondu dans les délais"}


async def check_health(auto_start: bool = True) -> dict:
    logger.debug(f"check_health(auto_start={auto_start})")
    if await _health_check():
        return {"ok": True, "data": {"healthy": True}}
    if auto_start:
        result = await ensure_server()
        if result["ok"]:
            return {"ok": True, "data": {"healthy": True, "started": result["started"]}}
        logger.error(f"ensure_server a échoué: {result}")
        return {"ok": False, "error": result["message"]}
    logger.warning("Serveur opencode indisponible")
    return {"ok": False, "error": "Serveur opencode indisponible"}


async def create_session(title="Potager - Assistant") -> str | None:
    try:
        async with httpx.AsyncClient(timeout=10) as cl:
            r = await cl.post(
                urljoin(OPENCODE_URL, "/session"),
                json={"title": title},
                headers=_headers(),
            )
            if r.status_code == 200:
                return r.json().get("id")
            logger.warning(f"create_session: HTTP {r.status_code}")
            return None
    except Exception as e:
        logger.error(f"create_session error: {e}")
        return None


async def send_message(session_id: str, text: str, context: str = "") -> str | None:
    parts = [{"type": "text", "text": text}]
    system = GARDEN_SYSTEM_PROMPT
    if context:
        system += f"\n\nContexte actuel : {context}"
    body = {"parts": parts, "system": system}
    url = urljoin(OPENCODE_URL, f"/session/{session_id}/message")
    logger.info(
        f"Envoi message à opencode: {url}, text_len={len(text)}, system_len={len(system)}"
    )
    try:
        async with httpx.AsyncClient(timeout=120) as cl:
            r = await cl.post(url, json=body, headers=_headers())
            logger.info(f"Réponse opencode: HTTP {r.status_code}")
            data = r.json()
            if r.status_code == 200:
                parts = data.get("parts", [])
                texts = [
                    p.get("text", "")
                    for p in (parts if isinstance(parts, list) else [])
                    if isinstance(p, dict) and p.get("type") == "text"
                ]
                if texts:
                    return "\n".join(texts)
                error_info = data.get("info", {}).get("error")
                if error_info:
                    msg = error_info.get("data", {}).get("message", str(error_info))
                    logger.error(f"Erreur LLM retournée par opencode: {msg}")
                    return f"⚠️ Erreur LLM : {msg}"
                logger.warning(
                    f"Réponse vide (parts=[]) sans info.error. data: {str(data)[:300]}"
                )
                return None
            logger.warning(f"send_message: HTTP {r.status_code} {str(data)[:500]}")
            return None
    except httpx.TimeoutException:
        logger.error("Timeout opencode (120s dépassé)")
        return None
    except Exception as e:
        logger.error(f"send_message error: {e}", exc_info=True)
        return None


async def get_history(session_id: str, limit: int = 20) -> list:
    try:
        async with httpx.AsyncClient(timeout=10) as cl:
            r = await cl.get(
                urljoin(OPENCODE_URL, f"/session/{session_id}/message"),
                params={"limit": limit},
                headers=_headers(),
            )
            if r.status_code == 200:
                return r.json()
            return []
    except Exception as e:
        logger.warning(f"get_history error: {e}")
        return []


def stop_server():
    global _server_process
    if _server_process and _server_process.poll() is None:
        try:
            if sys.platform != "win32":
                os.killpg(os.getpgid(_server_process.pid), signal.SIGTERM)
            else:
                _server_process.terminate()
            _server_process.wait(timeout=5)
            logger.info("Serveur opencode arrêté")
        except Exception as e:
            logger.warning(f"Arrêt serveur: {e}")
        _server_process = None
