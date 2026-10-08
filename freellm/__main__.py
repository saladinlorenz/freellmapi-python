from __future__ import annotations
import argparse
import os
import sys
import uvicorn
from .config import get_config

def main():
    p = argparse.ArgumentParser(description="FreeLLMAPI Python — serveur OpenAI-compatible agrégateur de tiers gratuits")
    p.add_argument("--port", type=int, default=None, help="port (défaut 3001 ou $PORT)")
    p.add_argument("--host", type=str, default=None, help="host (défaut 0.0.0.0)")
    p.add_argument("--tray", action="store_true", help="lance avec icône système (tray) + dashboard auto")
    p.add_argument("--no-tray", action="store_true", help="sans tray (serveur seul)")
    p.add_argument("--background", action="store_true", help="lance en arrière-plan détaché et quitte")
    p.add_argument("--stop", action="store_true", help="arrête le serveur en arrière-plan")
    p.add_argument("--status", action="store_true", help="statut du serveur en arrière-plan")
    args = p.parse_args()

    if args.stop:
        from .service import stop_background
        ok = stop_background()
        sys.exit(0 if ok else 1)
    if args.status:
        from .service import status_background
        st = status_background()
        print(st)
        sys.exit(0)

    if args.background:
        from .service import start_background
        start_background(port=args.port, host=args.host)
        sys.exit(0)

    cfg = get_config()
    port = args.port if args.port is not None else (int(cfg.port) if isinstance(cfg.port, int) or str(cfg.port).isdigit() else 3001)
    host = args.host if args.host is not None else (str(cfg.host) if cfg.host != "::" else "0.0.0.0")
    use_tray = args.tray
    # Enregistre le PID pour permettre l'arret via --stop / freellm-stop.bat
    from pathlib import Path
    import atexit
    db_path = cfg.db_path or str(Path(__file__).resolve().parent.parent / "data" / "freeapi.db")
    pid_file = Path(db_path).parent / "freellm.pid"
    try:
        pid_file.parent.mkdir(parents=True, exist_ok=True)
        pid_file.write_text(str(os.getpid()), encoding="utf-8")
        atexit.register(lambda: pid_file.unlink(missing_ok=True))
    except Exception:
        pass

    if use_tray:
        import threading
        # pythonw sans console : sys.stdout/sys.stderr valent None ->
        # redirection vers data/logs/server.log pour garder logs et erreurs.
        if sys.stdout is None or sys.stderr is None:
            try:
                log_path = Path(db_path).parent / "logs" / "server.log"
                log_path.parent.mkdir(parents=True, exist_ok=True)
                log_file = open(log_path, "a", encoding="utf-8", buffering=1)
                if sys.stdout is None:
                    sys.stdout = log_file
                if sys.stderr is None:
                    sys.stderr = log_file
            except Exception:
                pass
        def _serve():
            try:
                print(f"Starting FreeLLMAPI Python on {host}:{port} (tray)")
                uvicorn.run("freellm.app:create_app", factory=True, host=host, port=port, reload=False, log_level="info")
            except BaseException:
                import traceback
                traceback.print_exc()
        t = threading.Thread(target=_serve, daemon=True)
        t.start()
        import time
        time.sleep(1.2)
        try:
            from .tray import run_tray
            run_tray(port=port)
        except BaseException:
            import traceback
            traceback.print_exc()
        return

    print(f"Starting FreeLLMAPI Python on {host}:{port}")
    uvicorn.run("freellm.app:create_app", factory=True, host=host, port=port, reload=False)

if __name__ == "__main__":
    main()
