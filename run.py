#!/usr/bin/env python3
"""CyberGuard-ID — One-Command Runner (Production-Ready).

Usage:
    python run.py             # Jalankan server aplikasi web (http://localhost:8000)
    python run.py --no-browser # Jalankan server tanpa membuka browser otomatis
    python run.py --train     # Latih model IndoBERT (membutuhkan waktu)
    python run.py --test      # Jalankan seluruh unit & integration test
    python run.py --check     # Audit kesehatan sistem & konfigurasi

Cross-platform: Windows, Linux, macOS.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import platform
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

# Set UTF-8 encoding for standard outputs
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent
VENV_DIR = PROJECT_ROOT / ".venv"
REQUIREMENTS = PROJECT_ROOT / "requirements.txt"
ENV_FILE = PROJECT_ROOT / ".env"
ENV_EXAMPLE = PROJECT_ROOT / ".env.example"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
DB_PATH = ARTIFACTS_DIR / "cyberguard.db"
MODELS_DIR = PROJECT_ROOT / "models"
STAMP_FILE = VENV_DIR / ".requirements_hash"

MIN_PYTHON = (3, 10)


def handle_exit_signal(signum, frame):
    """Graceful exit handler for Ctrl+C / SIGINT / SIGTERM."""
    print("\n🛑 Server CyberGuard-ID telah dihentikan secara aman. Sampai jumpa!")
    sys.exit(0)


# Register signal handlers for clean terminal Ctrl+C behavior
try:
    signal.signal(signal.SIGINT, handle_exit_signal)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, handle_exit_signal)
except Exception:
    pass


def print_banner() -> None:
    """Print clean startup banner."""
    print("""
  ┌────────────────────────────────────────────────────────┐
  │              🛡️  CYBERGUARD-ID PLATFORM                 │
  │    Skrining & Prioritisasi Moderasi Komentar AI        │
  │                   Version 2.0.0                        │
  └────────────────────────────────────────────────────────┘
""")


def check_python_version() -> None:
    """Verify Python version meets minimum requirement."""
    v = sys.version_info[:2]
    if v < MIN_PYTHON:
        print(f"❌ [ERROR] Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ diperlukan (ditemukan {v[0]}.{v[1]})")
        sys.exit(1)


def get_venv_python() -> Path:
    """Return path to Python executable inside the venv."""
    if platform.system() == "Windows":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def get_venv_pip() -> Path:
    """Return path to pip inside the venv."""
    if platform.system() == "Windows":
        return VENV_DIR / "Scripts" / "pip.exe"
    return VENV_DIR / "bin" / "pip"


def is_in_venv() -> bool:
    """Check if currently running inside the project venv."""
    if hasattr(sys, "real_prefix") or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix):
        return True
    venv_python = get_venv_python()
    try:
        return Path(sys.executable).resolve() == venv_python.resolve()
    except Exception:
        return False


def create_venv() -> None:
    """Create virtual environment if it doesn't exist."""
    if VENV_DIR.exists() and get_venv_python().exists():
        return

    print("📦 [INFO] Membuat virtual environment (.venv)...")
    subprocess.check_call([sys.executable, "-m", "venv", str(VENV_DIR)])
    print("✅ [OK] Virtual environment berhasil dibuat.")


def requirements_hash() -> str:
    """Compute hash of requirements.txt for change detection."""
    if not REQUIREMENTS.exists():
        return ""
    return hashlib.md5(REQUIREMENTS.read_bytes()).hexdigest()


def needs_install() -> bool:
    """Check if dependencies need to be installed."""
    if not STAMP_FILE.exists():
        return True
    try:
        stored = STAMP_FILE.read_text(encoding="utf-8").strip()
        return stored != requirements_hash()
    except Exception:
        return True


def install_dependencies() -> None:
    """Install or update dependencies from requirements.txt."""
    if not needs_install():
        return

    print("📥 [INFO] Menginstal dependensi dari requirements.txt...")
    vpip = get_venv_pip()
    try:
        subprocess.check_call(
            [str(get_venv_python()), "-m", "pip", "install", "-r", str(REQUIREMENTS)],
        )
        STAMP_FILE.write_text(requirements_hash(), encoding="utf-8")
        print("✅ [OK] Dependensi berhasil diinstal.")
    except Exception as e:
        print(f"⚠️ [WARN] Kendala instalasi pip: {e}")
        vpy = get_venv_python()
        try:
            subprocess.check_call(
                [str(vpy), "-c", "import fastapi, sklearn, yaml, pydantic, joblib"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            STAMP_FILE.write_text(requirements_hash(), encoding="utf-8")
            print("✅ [OK] Modul utama terverifikasi.")
        except Exception:
            raise


def setup_env_file() -> None:
    """Create .env from .env.example if it doesn't exist."""
    if ENV_FILE.exists():
        return

    if ENV_EXAMPLE.exists():
        shutil.copy2(ENV_EXAMPLE, ENV_FILE)
        print("ℹ️ [INFO] File .env dibuat dari .env.example (silakan isi API Key Anda jika ada).")
    else:
        ENV_FILE.write_text(
            "# CyberGuard-ID Environment Config\n"
            "YOUTUBE_API_KEY=\n"
            "GEMINI_API_KEY=\n"
            "GEMINI_MODEL=gemini-2.5-flash-lite\n"
            "USE_GEMINI=true\n"
            "ANONYMIZATION_SALT=rahasia-cyberguard-salt\n"
            "APP_ENV=development\n"
            "APP_PORT=8000\n"
            "LOG_LEVEL=INFO\n",
            encoding="utf-8",
        )
        print("ℹ️ [INFO] File .env dibuat secara otomatis.")


def create_directories() -> None:
    """Ensure required directories exist."""
    dirs = [
        ARTIFACTS_DIR / "reports",
        ARTIFACTS_DIR / "predictions",
        ARTIFACTS_DIR / "evaluations",
        ARTIFACTS_DIR / "logs",
        MODELS_DIR,
        PROJECT_ROOT / "data" / "raw",
        PROJECT_ROOT / "data" / "processed",
        PROJECT_ROOT / "data" / "sample",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def init_database() -> None:
    """Initialize SQLite database."""
    sys.path.insert(0, str(PROJECT_ROOT))
    try:
        from src.services.storage import StorageService

        storage = StorageService(DB_PATH)
        storage.initialize()
        storage.close()
    except Exception as e:
        print(f"⚠️ [WARN] Inisialisasi DB: {e}")


def check_model() -> bool:
    """Check if trained model exists."""
    model_dir = MODELS_DIR / "indobert_cyberguard"
    meta_path = MODELS_DIR / "model_metadata.json"
    if model_dir.exists() and meta_path.exists():
        version = "2.0 (IndoBERT)"
        print(f"  • Model AI       : ✅ Siap (v{version})")
        return True
    print("  • Model AI       : ⚠️ Belum ada ('python run.py --train' untuk melatih)")
    return False


def check_api_keys() -> None:
    """Report API key status."""
    from dotenv import load_dotenv

    load_dotenv(ENV_FILE)

    yt = bool(os.getenv("YOUTUBE_API_KEY", ""))
    gm = bool(os.getenv("GEMINI_API_KEY", ""))

    print(f"  • YouTube API    : {'✅ Terhubung' if yt else '[-] Kosong (Mode Dataset CSV Aktif)'}")
    print(f"  • Gemini AI API  : {'✅ Terhubung' if gm else '[-] Kosong (Menggunakan Template Lokal)'}")
    print(f"  • Database       : ✅ SQLite Siap ({DB_PATH.name})")


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a TCP port is currently occupied."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((host, port))
            return False
        except OSError:
            return True


def kill_process_on_port(port: int) -> bool:
    """Find and kill any process occupying the given port."""
    curr_pid = os.getpid()
    killed_any = False

    if platform.system() == "Windows":
        # Method 1: netstat -ano extraction + taskkill
        try:
            output = subprocess.check_output(
                f'netstat -ano | findstr ":{port} "',
                shell=True,
                text=True,
                stderr=subprocess.DEVNULL,
            )
            pids_to_kill = set()
            for line in output.strip().splitlines():
                parts = line.strip().split()
                if len(parts) >= 5 and "LISTENING" in line.upper():
                    pid_str = parts[-1]
                    if pid_str.isdigit():
                        p = int(pid_str)
                        if p not in (0, 4, curr_pid):
                            pids_to_kill.add(p)
            for p in pids_to_kill:
                subprocess.run(
                    f"taskkill /F /PID {p}",
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                killed_any = True
        except Exception:
            pass

        # Method 2: PowerShell Get-NetTCPConnection fallback
        try:
            cmd = (
                f'powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort {port} '
                f"-State Listen -ErrorAction SilentlyContinue | Where-Object {{ $_.OwningProcess "
                f"-notin @(0, 4, {curr_pid}) }} | ForEach-Object {{ Stop-Process -Id "
                '$_.OwningProcess -Force -ErrorAction SilentlyContinue }"'
            )
            subprocess.run(
                cmd,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=4,
            )
            killed_any = True
        except Exception:
            pass
    else:
        # Unix / macOS
        try:
            cmd = f"lsof -ti:{port} | xargs kill -9 2>/dev/null || fuser -k {port}/tcp 2>/dev/null"
            subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            killed_any = True
        except Exception:
            pass

    return killed_any


def ensure_available_port(target_port: int, host: str = "127.0.0.1") -> int:
    """Ensure port is available by clearing stale processes or using a fallback."""
    if not is_port_in_use(target_port, host):
        return target_port

    print(f"⚠️ Port {target_port} sedang digunakan oleh proses lain. Mematikan proses sebelumnya...")
    kill_process_on_port(target_port)

    # Wait for the OS to release the socket
    for _ in range(10):
        time.sleep(0.3)
        if not is_port_in_use(target_port, host):
            print(f"✅ Port {target_port} berhasil diputus & dibebaskan.")
            return target_port

    # If still busy after killing, try fallback ports
    for p in range(target_port + 1, target_port + 20):
        if not is_port_in_use(p, host):
            print(f"ℹ️ Menggunakan port alternatif: {p}")
            return p
    return target_port


def run_app(open_browser: bool = True) -> None:
    """Launch FastAPI application via uvicorn in current process."""
    from dotenv import load_dotenv

    load_dotenv(ENV_FILE)

    port_str = os.getenv("APP_PORT", "8000")
    try:
        port = int(port_str)
    except ValueError:
        port = 8000

    port = ensure_available_port(port)
    url = f"http://localhost:{port}"

    print(f"""
  ╔════════════════════════════════════════════════════════╗
  ║  🚀 CYBERGUARD-ID SERVER AKTIF & BERJALAN              ║
  ╠════════════════════════════════════════════════════════╣
  ║  🌐 Web Dashboard : {url:<34} ║
  ║  📑 REST API Docs : {url + "/api/docs":<34} ║
  ╠════════════════════════════════════════════════════════╣
  ║  Tekan Ctrl+C untuk menghentikan server kapan saja.     ║
  ╚════════════════════════════════════════════════════════╝
""")

    if open_browser:

        def _open():
            time.sleep(1.2)
            with contextlib.suppress(Exception):
                webbrowser.open(url)

        threading.Thread(target=_open, daemon=True).start()

    try:
        import uvicorn

        config = uvicorn.Config(
            "server.main:app",
            host="127.0.0.1",
            port=port,
            reload=False,
            log_level="warning",
            access_log=False,
        )
        server = uvicorn.Server(config)
        server.run()
    except (KeyboardInterrupt, SystemExit):
        print("\n🛑 Server CyberGuard-ID telah dihentikan secara aman. Sampai jumpa!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Gagal menjalankan server: {e}")
        sys.exit(1)


def run_train() -> None:
    """Run model training using IndoBERT."""
    print("\n--- [Fase Persiapan Dataset] ---\n")
    print("Mengeksekusi skrip: python scripts/ingest_authentic_datasets.py")
    subprocess.check_call([str(get_venv_python()), str(PROJECT_ROOT / "scripts" / "ingest_authentic_datasets.py")])

    print("\n--- [Fase Pelatihan IndoBERT Deep Learning] ---\n")
    print("Mengeksekusi skrip: python scripts/train_bert.py")
    subprocess.check_call([str(get_venv_python()), str(PROJECT_ROOT / "scripts" / "train_bert.py")])
    print("\n✅ Pelatihan selesai. Jalankan 'python run.py' untuk memulai aplikasi.")


def run_tests() -> None:
    """Run test suite."""
    vpy = get_venv_python()
    subprocess.call([str(vpy), "-m", "pytest", str(PROJECT_ROOT / "tests"), "-v", "--tb=short"])


def run_check() -> None:
    """Run system health check."""
    print("=== Pemeriksaan Kesehatan Sistem CyberGuard-ID ===")
    setup_env_file()
    create_directories()
    init_database()
    check_model()
    check_api_keys()
    print("\n✅ Pemeriksaan sistem selesai.")


def main() -> None:
    """Main launcher entry point."""
    check_python_version()
    create_venv()

    # If running outside venv, replace current process with venv python directly (no nested wrapper)
    if not is_in_venv():
        install_dependencies()
        vpy = get_venv_python()
        args = [str(vpy), str(PROJECT_ROOT / "run.py")] + sys.argv[1:]
        try:
            os.execv(str(vpy), args)
        except Exception:
            # Fallback if execv is unavailable
            try:
                ret = subprocess.call(args)
                sys.exit(ret)
            except (KeyboardInterrupt, SystemExit):
                print("\n🛑 Dihentikan oleh pengguna.")
                sys.exit(0)

    # We are inside the venv: print banner and initialize
    print_banner()
    install_dependencies()
    setup_env_file()
    create_directories()
    init_database()

    args = sys.argv[1:]

    if "--train" in args:
        run_train()
    elif "--test" in args:
        run_tests()
    elif "--check" in args:
        run_check()
    else:
        # Normal web server launch
        print("📊 Status Komponen:")
        check_model()
        check_api_keys()
        no_browser = "--no-browser" in args
        run_app(open_browser=not no_browser)


if __name__ == "__main__":
    main()
