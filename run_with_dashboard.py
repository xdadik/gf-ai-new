# pyre-ignore-all-errors
"""
Lily Bot + Dashboard Launcher
Starts the FastAPI dashboard in a background thread and the Telegram bot in the main thread.
"""
import os  # type: ignore  # pyre-ignore
import sys  # type: ignore  # pyre-ignore
import time  # type: ignore  # pyre-ignore
import threading  # type: ignore  # pyre-ignore
import logging  # type: ignore  # pyre-ignore
import importlib.util  # type: ignore  # pyre-ignore

import uvicorn  # type: ignore  # pyre-ignore
from dashboard import app, bot_state  # type: ignore  # pyre-ignore

# Best-effort: make stdout/stderr UTF-8 to avoid UnicodeEncodeError on some Windows consoles.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore  # pyre-ignore
        except Exception:
            pass

# ── Logging ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("lily.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("LilyRunner")


def _kill_zombie_bots() -> None:  # type: ignore  # pyre-ignore
    """Kill any stale Python processes that are running the bot or dashboard."""
    current_pid = os.getpid()
    try:
        import psutil  # type: ignore  # pyre-ignore
        killed = 0
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):  # type: ignore  # pyre-ignore
            try:
                if proc.pid == current_pid:
                    continue
                cmdline = " ".join(proc.info.get("cmdline") or []).lower()
                if ("lily_bot" in cmdline or "run_with_dashboard" in cmdline) and "python" in (proc.info.get("name") or "").lower():
                    proc.kill()
                    killed += 1
            except Exception:
                pass
        if killed:
            logger.info(f"Cleaned up {killed} stale bot process(es). Waiting 2s for Telegram to release the slot...")
            time.sleep(2)
    except ImportError:
        pass  # psutil not available – skip


def _check_ollama() -> None:  # type: ignore  # pyre-ignore
    """Warn if Ollama is not reachable."""
    try:
        import urllib.request  # type: ignore  # pyre-ignore
        from config import SETTINGS  # type: ignore  # pyre-ignore
        url = SETTINGS.ollama_base_url.rstrip("/") + "/api/tags"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=3):
            # Keep this ASCII-safe for Windows terminals that can't print emoji reliably.
            logger.info("Ollama is reachable (OK)")
    except Exception as e:
        logger.warning(
            f"Ollama not reachable at configured URL ({e}). "
            "The bot will start but LLM responses will fail until Ollama is running."
        )


def run_dashboard() -> None:  # type: ignore  # pyre-ignore
    """Run FastAPI dashboard server with WebSocket support."""
    logger.info("Starting dashboard server on http://localhost:8000")

    # uvicorn WebSocket support requires either `websockets` or `wsproto`.
    if importlib.util.find_spec("websockets") is not None:
        ws_impl = "websockets"
    elif importlib.util.find_spec("wsproto") is not None:
        ws_impl = "wsproto"
    else:
        ws_impl = "none"
        logger.warning(
            "Dashboard live updates (WebSockets) are disabled because neither `websockets` nor `wsproto` is installed. "
            "Install `websockets` and restart to enable them."
        )

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="warning",
        ws=ws_impl,
    )


def run_bot() -> None:  # type: ignore  # pyre-ignore
    """Run Telegram bot (blocks until stopped)."""
    logger.info("Starting Telegram bot")

    # Lazy import so the dashboard can still start even if bot deps fail.
    from config import SETTINGS  # type: ignore  # pyre-ignore

    if not SETTINGS.telegram_bot_token:
        logger.error("TELEGRAM_BOT_TOKEN is not set. Bot will not start; dashboard will keep running.")
        return

    from lily_bot import main as bot_main  # type: ignore  # pyre-ignore

    bot_main()


def main() -> None:  # type: ignore  # pyre-ignore
    logger.info("=" * 50)
    logger.info("Lily Bot + Dashboard Launcher")
    logger.info("=" * 50)

    # 1. Kill any zombie instances first
    # _kill_zombie_bots()

    # 2. Check Ollama
    _check_ollama()

    # 3. Start dashboard in daemon thread
    dashboard_thread = threading.Thread(target=run_dashboard, daemon=True, name="DashboardThread")
    dashboard_thread.start()

    logger.info("Dashboard available at: http://localhost:8000")
    logger.info("Starting bot...")
    logger.info("-" * 50)

    # 4. Run bot in main thread (blocks with polling)
    try:
        run_bot()
    except KeyboardInterrupt:
        logger.info("\nShutdown requested. Goodbye!")
        bot_state["running"] = False
    except Exception as e:
        logger.error(f"Bot crashed: {e}", exc_info=True)
        logger.info("Dashboard will continue running. Press Ctrl+C to stop.")
        try:
            while dashboard_thread.is_alive():
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("\nShutdown requested. Goodbye!")
            bot_state["running"] = False


if __name__ == "__main__":
    main()

