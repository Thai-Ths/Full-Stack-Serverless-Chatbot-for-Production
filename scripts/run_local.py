#!/usr/bin/env python3
"""
Run backend (FastAPI via uvicorn) and frontend (Next.js) together for local dev.

Examples:
  python run_local.py
  python run_local.py --backend-port 8000 --frontend-port 3000

Behavior:
  - Backend: prefers `uv run uvicorn server:app --reload`, otherwise
    falls back to `python -m uvicorn ...`.
  - Frontend: `npm run dev -- -p <port>` with NEXT_PUBLIC_API_URL set to backend.
  - Graceful shutdown on Ctrl+C; stops both processes.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
import threading


def _stream_output(prefix: str, proc: subprocess.Popen) -> None:
    def _reader(stream):
        try:
            for line in iter(stream.readline, ""):
                if not line:
                    break
                msg = line.rstrip()
                if msg:
                    print(f"[{prefix}] {msg}")
        except Exception:
            pass
    # attach readers
    if proc.stdout is not None:
        t = threading.Thread(target=_reader, args=(proc.stdout,), daemon=True)
        t.start()


def which(cmd: str) -> str | None:
    return shutil.which(cmd)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run backend and frontend together")
    parser.add_argument("--backend-port", type=int, default=8000, help="Backend port (uvicorn)")
    parser.add_argument("--frontend-port", type=int, default=3000, help="Frontend port (Next.js dev)")
    parser.add_argument("--backend-host", type=str, default="0.0.0.0", help="Backend host bind")
    args = parser.parse_args()

    # scripts/ is one level below project root
    repo_root = Path(__file__).resolve().parent.parent
    backend_dir = repo_root / "backend"
    frontend_dir = repo_root / "frontend"
    memory_dir = repo_root / "memory"

    if not backend_dir.exists():
        print(f"❌ Backend directory not found: {backend_dir}")
        return 1
    if not frontend_dir.exists():
        print(f"❌ Frontend directory not found: {frontend_dir}")
        return 1

    # Backend command (prefer project venv python, then uv, then system python)
    if os.name == "nt":
        venv_python_path = backend_dir / ".venv" / "Scripts" / "python.exe"
    else:
        venv_python_path = backend_dir / ".venv" / "bin" / "python"

    if venv_python_path.exists():
        python_exec = str(venv_python_path)
        backend_cmd = [
            python_exec, "-m", "uvicorn", "server:app",
            "--reload", "--host", args.backend_host, "--port", str(args.backend_port),
        ]
    elif which("uv"):
        backend_cmd = [
            "uv", "run", "uvicorn", "server:app",
            "--reload", "--host", args.backend_host, "--port", str(args.backend_port),
        ]
    else:
        backend_cmd = [
            sys.executable, "-m", "uvicorn", "server:app",
            "--reload", "--host", args.backend_host, "--port", str(args.backend_port),
        ]

    # Frontend command
    if not which("npm") and not which("npm.cmd"):
        print("❌ npm not found in PATH. Please install Node.js/npm.")
        return 1
    frontend_cmd = ["npm", "run", "dev", "--", "-p", str(args.frontend_port)]

    # Envs
    env_backend = os.environ.copy()
    # Ensure CORS allows frontend origin if server checks env
    env_backend.setdefault("CORS_ORIGINS", f"http://localhost:{args.frontend_port}")
    # Force local file memory for dev, and point to repo memory dir
    env_backend.setdefault("USE_S3", "false")
    env_backend.setdefault("MEMORY_DIR", str(memory_dir))
    env_backend.setdefault("S3_BUCKET", "")

    env_frontend = os.environ.copy()
    env_frontend["NEXT_PUBLIC_API_URL"] = f"http://localhost:{args.backend_port}"
    env_frontend.setdefault("PORT", str(args.frontend_port))

    print("🚀 Starting local development...")
    print(f"🟦 Backend: {' '.join(backend_cmd)} (cwd={backend_dir})")
    print(f"🟩 Frontend: {' '.join(frontend_cmd)} (cwd={frontend_dir})")
    print(f"🗂️  Memory dir: {memory_dir}")
    print("")
    print(f"📡 API       http://localhost:{args.backend_port}")
    print(f"🌐 Frontend  http://localhost:{args.frontend_port}")
    print("")

    backend_proc = None
    frontend_proc = None

    try:
        # Backend: spawn normally
        backend_proc = subprocess.Popen(
            backend_cmd,
            cwd=str(backend_dir),
            env=env_backend,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        _stream_output("Backend", backend_proc)

        # Ensure frontend deps installed if missing
        node_modules_dir = frontend_dir / "node_modules"
        if not node_modules_dir.exists():
            print("📦 Installing frontend dependencies...")
            install_cmd = "npm install" if os.name != "nt" else "npm.cmd install"
            subprocess.run(install_cmd, cwd=str(frontend_dir), env=env_frontend, shell=True, check=True)

        # Frontend: on Windows npm is a .cmd, use shell=True to ensure it launches
        is_windows = os.name == "nt"
        if is_windows:
            frontend_cmd_str = " ".join(frontend_cmd)
            frontend_proc = subprocess.Popen(
                frontend_cmd_str,
                cwd=str(frontend_dir),
                env=env_frontend,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
        else:
            frontend_proc = subprocess.Popen(
                frontend_cmd,
                cwd=str(frontend_dir),
                env=env_frontend,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
        _stream_output("Frontend", frontend_proc)

        # Wait until one exits
        while True:
            b_code = backend_proc.poll()
            f_code = frontend_proc.poll()
            if b_code is not None:
                print(f"⚠️ Backend exited with code {b_code}")
                if frontend_proc.poll() is None:
                    frontend_proc.terminate()
                return b_code
            if f_code is not None:
                print(f"⚠️ Frontend exited with code {f_code}")
                if backend_proc.poll() is None:
                    backend_proc.terminate()
                return f_code
    except KeyboardInterrupt:
        print("\n🛑 Ctrl+C received, stopping...")
        return 0
    finally:
        for proc in (frontend_proc, backend_proc):
            if proc and proc.poll() is None:
                try:
                    proc.terminate()
                except Exception:
                    pass


if __name__ == "__main__":
    raise SystemExit(main())
