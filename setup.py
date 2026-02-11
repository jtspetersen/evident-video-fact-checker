#!/usr/bin/env python3
"""
Evident Video Fact Checker — Setup Wizard

Takes a fresh install from zero to a working pipeline run.
Native-first: local Python + local Ollama + SearXNG via Docker.

Each step follows check → act → verify: detects what's already done,
does only what's needed, and confirms it worked. Safe to re-run.

Usage:
    python setup.py            # Interactive setup
    python setup.py --check    # Validate existing setup (no changes)
"""

import os
import sys
import json
import time
import secrets
import platform
import subprocess
import shutil
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Tuple

# Fix Windows console encoding for Unicode markers
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


# ── Project root (setup.py lives here) ──────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent
COMPOSE_FILE = PROJECT_ROOT / "docker-compose.searxng.yml"
CONFIG_FILE = PROJECT_ROOT / "config.yaml"
ENV_FILE = PROJECT_ROOT / ".env"
REQUIREMENTS_FILE = PROJECT_ROOT / "Requirements.txt"
SEARXNG_DIR = PROJECT_ROOT / "searxng"

OLLAMA_URL = "http://localhost:11434"
SEARXNG_URL = "http://localhost:8080"

MODEL_TIERS = [
    # (min_vram, min_ram, label, extract, verify, write)
    (24, 32, "High-end GPU (24 GB+ VRAM)", "qwen3:8b", "qwen3:30b", "gemma3:27b"),
    (16, 32, "Mid-range GPU (16 GB VRAM)", "qwen3:8b", "qwen3:14b", "gemma3:12b"),
    (12, 32, "Entry GPU (12 GB VRAM)",     "qwen3:8b", "qwen3:8b",  "gemma3:9b"),
    (0,  64, "High-end CPU (64 GB+ RAM)",  "qwen3:8b", "qwen3:14b", "gemma3:9b"),
    (0,  32, "Mid-range CPU (32 GB+ RAM)", "qwen3:8b", "qwen3:8b",  "llama3:8b"),
    (0,  16, "Minimum (16 GB RAM)",        "phi3:mini","phi3:mini",  "phi3:mini"),
]

# AMD VRAM lookup for Windows WMI (32-bit AdapterRAM cap)
AMD_VRAM_TABLE = {
    "7900 XTX": 24.0, "7900 XT": 20.0, "7800 XT": 16.0,
    "7700 XT": 12.0,  "7600": 8.0,     "6950 XT": 16.0,
    "6900 XT": 16.0,  "6800 XT": 16.0, "6800": 16.0,
    "6750 XT": 12.0,  "6700 XT": 12.0,
}


# ═══════════════════════════════════════════════════════════════════
# Utilities
# ═══════════════════════════════════════════════════════════════════

def ok(msg: str)   -> None: print(f"  [OK]   {msg}")
def fail(msg: str) -> None: print(f"  [FAIL] {msg}", file=sys.stderr)
def warn(msg: str) -> None: print(f"  [WARN] {msg}")
def info(msg: str) -> None: print(f"  ...    {msg}")
def banner(title: str) -> None:
    print(f"\n{'=' * 64}")
    print(f"  {title}")
    print(f"{'=' * 64}\n")


def ask(question: str, default: bool = True) -> bool:
    hint = "Y/n" if default else "y/N"
    while True:
        answer = input(f"  {question} [{hint}] ").strip().lower()
        if not answer:
            return default
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False


def run(cmd: list, capture: bool = False, check: bool = True,
        timeout: int = 120) -> Optional[str]:
    try:
        r = subprocess.run(
            cmd, capture_output=capture, text=True,
            check=check, timeout=timeout
        )
        return r.stdout.strip() if capture else None
    except (subprocess.CalledProcessError, FileNotFoundError,
            subprocess.TimeoutExpired):
        if check:
            raise
        return None


def http_get(url: str, timeout: int = 10) -> Optional[str]:
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception:
        return None


def http_post_json(url: str, data: dict, timeout: int = 60) -> Optional[str]:
    try:
        payload = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════
# Step 1: Python & pip dependencies
# ═══════════════════════════════════════════════════════════════════

def step_python_deps(check_only: bool = False) -> bool:
    banner("Step 1 / 8 : Python & Dependencies")

    # Python version
    v = sys.version_info
    if v >= (3, 11):
        ok(f"Python {v.major}.{v.minor}.{v.micro}")
    else:
        fail(f"Python 3.11+ required (found {v.major}.{v.minor})")
        return False

    # Quick import check for key packages
    missing = []
    for pkg, module in [
        ("pydantic", "pydantic"), ("requests", "requests"),
        ("fastapi", "fastapi"), ("tqdm", "tqdm"),
        ("PyYAML", "yaml"), ("beautifulsoup4", "bs4"),
        ("python-dotenv", "dotenv"), ("psutil", "psutil"),
        ("jinja2", "jinja2"), ("uvicorn", "uvicorn"),
    ]:
        try:
            __import__(module)
        except ImportError:
            missing.append(pkg)

    if not missing:
        ok("All Python packages installed")
        return True

    warn(f"Missing packages: {', '.join(missing)}")

    if check_only:
        fail("Run: pip install -r Requirements.txt")
        return False

    if not REQUIREMENTS_FILE.exists():
        fail(f"{REQUIREMENTS_FILE} not found")
        return False

    info("Installing packages...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)],
            check=True, timeout=300
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        fail(f"pip install failed: {e}")
        return False

    # Verify
    still_missing = []
    for pkg, module in [("pydantic", "pydantic"), ("requests", "requests"),
                        ("fastapi", "fastapi"), ("tqdm", "tqdm"),
                        ("PyYAML", "yaml"), ("psutil", "psutil")]:
        try:
            __import__(module)
        except ImportError:
            still_missing.append(pkg)

    if still_missing:
        fail(f"Still missing after install: {', '.join(still_missing)}")
        return False

    ok("All packages installed")
    return True


# ═══════════════════════════════════════════════════════════════════
# Step 2: Ollama
# ═══════════════════════════════════════════════════════════════════

def step_ollama(check_only: bool = False) -> bool:
    banner("Step 2 / 8 : Ollama LLM Service")

    # Check CLI
    cli_ok = False
    try:
        ver = run(["ollama", "--version"], capture=True, check=False)
        if ver:
            ok(f"Ollama CLI: {ver}")
            cli_ok = True
    except Exception:
        pass

    if not cli_ok:
        fail("Ollama CLI not found in PATH")
        print()
        system = platform.system()
        if system == "Windows":
            print("  Install Ollama:")
            print("    winget install Ollama.Ollama")
            print("    -- or download from https://ollama.com/download")
        elif system == "Darwin":
            print("  Install Ollama:")
            print("    brew install ollama")
            print("    -- or download from https://ollama.com/download")
        else:
            print("  Install Ollama:")
            print("    curl -fsSL https://ollama.com/install.sh | sh")
        print()
        return False

    # Check service
    resp = http_get(f"{OLLAMA_URL}/api/tags")
    if resp:
        ok(f"Ollama service running at {OLLAMA_URL}")
        return True

    warn("Ollama installed but service not responding")

    if check_only:
        fail("Start Ollama and re-run")
        return False

    # Try to start it
    info("Attempting to start Ollama...")
    system = platform.system()
    if system == "Windows":
        # On Windows, 'ollama serve' blocks — try starting via the app
        try:
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                | subprocess.DETACHED_PROCESS
            )
            info("Started 'ollama serve' in background")
        except Exception:
            warn("Could not auto-start Ollama")
            print("  Start Ollama manually (system tray icon or 'ollama serve')")
            return False
    else:
        try:
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            info("Started 'ollama serve' in background")
        except Exception:
            warn("Could not auto-start Ollama")
            print("  Start Ollama manually: ollama serve &")
            return False

    # Wait for it
    for i in range(12):
        time.sleep(5)
        resp = http_get(f"{OLLAMA_URL}/api/tags")
        if resp:
            ok(f"Ollama service ready at {OLLAMA_URL}")
            return True
        info(f"Waiting for Ollama... ({(i+1)*5}s)")

    fail("Ollama did not start within 60s")
    print("  Start Ollama manually and re-run setup")
    return False


# ═══════════════════════════════════════════════════════════════════
# Step 3: Docker (for SearXNG) + FFmpeg
# ═══════════════════════════════════════════════════════════════════

def _check_ffmpeg() -> bool:
    """Check for FFmpeg, attempt install if missing."""
    try:
        ver = run(["ffmpeg", "-version"], capture=True, check=False)
        if ver:
            ok(f"FFmpeg: {ver.split(chr(10))[0]}")
            return True
    except Exception:
        pass

    warn("FFmpeg not found (needed only for YouTube Whisper fallback)")

    system = platform.system()
    if system == "Windows":
        info("Attempting install via winget...")
        try:
            r = subprocess.run(
                ["winget", "install", "--id", "Gyan.FFmpeg",
                 "--accept-source-agreements", "--accept-package-agreements"],
                timeout=300, capture_output=False, text=True
            )
            if r.returncode == 0:
                ok("FFmpeg installed (restart terminal for PATH)")
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        warn("Install FFmpeg manually: winget install Gyan.FFmpeg")
    elif system == "Linux":
        info("Attempting install via apt...")
        try:
            subprocess.run(["sudo", "apt-get", "install", "-y", "ffmpeg"],
                           check=True, timeout=120)
            ok("FFmpeg installed")
            return True
        except Exception:
            pass
        warn("Install FFmpeg manually: sudo apt install ffmpeg")
    elif system == "Darwin":
        info("Attempting install via brew...")
        try:
            subprocess.run(["brew", "install", "ffmpeg"], check=True, timeout=300)
            ok("FFmpeg installed")
            return True
        except Exception:
            pass
        warn("Install FFmpeg manually: brew install ffmpeg")

    warn("Caption-based YouTube transcripts still work without FFmpeg")
    return False


def step_docker_and_ffmpeg(check_only: bool = False) -> bool:
    banner("Step 3 / 8 : Docker & FFmpeg")

    # Docker
    docker_ok = False
    try:
        ver = run(["docker", "--version"], capture=True, check=False)
        if ver:
            ok(f"Docker: {ver}")
            docker_ok = True
    except Exception:
        pass

    if not docker_ok:
        fail("Docker not installed (needed to run SearXNG search engine)")
        system = platform.system()
        if system == "Windows":
            print("  Install Docker Desktop: https://www.docker.com/products/docker-desktop")
        elif system == "Darwin":
            print("  Install Docker Desktop: brew install --cask docker")
        else:
            print("  Install Docker: https://docs.docker.com/engine/install/")
        print()
        return False

    # Docker Compose
    try:
        ver = run(["docker", "compose", "version"], capture=True, check=False)
        if ver:
            ok(f"Docker Compose: {ver}")
        else:
            fail("Docker Compose v2 not available (need 'docker compose' subcommand)")
            return False
    except Exception:
        fail("Docker Compose v2 not available")
        return False

    # Docker daemon running?
    try:
        run(["docker", "info"], capture=True, check=True, timeout=15)
        ok("Docker daemon running")
    except Exception:
        fail("Docker daemon not running — start Docker Desktop and re-run")
        return False

    # FFmpeg (optional — don't fail on this)
    _check_ffmpeg()

    return True


# ═══════════════════════════════════════════════════════════════════
# Step 4: Hardware detection
# ═══════════════════════════════════════════════════════════════════

def _detect_nvidia() -> Tuple[bool, Optional[str], float]:
    try:
        out = run(
            ["nvidia-smi", "--query-gpu=name,memory.total",
             "--format=csv,noheader,nounits"],
            capture=True, check=False
        )
        if out:
            parts = out.split(",")
            name = parts[0].strip()
            vram = float(parts[1].strip()) / 1024
            return True, name, vram
    except Exception:
        pass
    return False, None, 0.0


def _detect_amd_windows() -> Tuple[bool, Optional[str], float]:
    if platform.system() != "Windows":
        return False, None, 0.0
    try:
        out = run(
            ["powershell", "-Command",
             "Get-WmiObject Win32_VideoController | "
             "Select-Object Name,AdapterRAM | Format-List"],
            capture=True, check=False
        )
        if not out:
            return False, None, 0.0

        gpu_name = None
        for line in out.split("\n"):
            line = line.strip()
            if line.startswith("Name") and ("Radeon" in line or "AMD" in line):
                gpu_name = line.split(":", 1)[1].strip() if ":" in line else None
            elif line.startswith("AdapterRAM") and gpu_name:
                # WMI AdapterRAM is 32-bit capped — use lookup table
                vram = 0.0
                for pattern, known_vram in AMD_VRAM_TABLE.items():
                    if pattern in gpu_name:
                        vram = known_vram
                        break
                if vram == 0.0:
                    # Try parsing reported value
                    try:
                        raw = line.split(":", 1)[1].strip()
                        vram = int(raw) / (1024 ** 3) if raw else 0.0
                    except (ValueError, IndexError):
                        pass
                return True, gpu_name, vram
    except Exception:
        pass
    return False, None, 0.0


def _detect_amd_rocm() -> Tuple[bool, Optional[str], float]:
    try:
        out = run(["rocm-smi", "--showproductname"], capture=True, check=False)
        if out and "GPU" in out:
            name = None
            for line in out.split("\n"):
                if "Card series:" in line or "Card model:" in line:
                    name = line.split(":")[-1].strip()
                    break
                if "Radeon" in line or "AMD" in line:
                    name = line.strip()
                    break
            if name:
                # Try VRAM detection
                vram = 0.0
                for pattern, known in AMD_VRAM_TABLE.items():
                    if pattern in name:
                        vram = known
                        break
                return True, name, vram
    except Exception:
        pass
    return False, None, 0.0


def _check_ollama_gpu() -> bool:
    """Check if Ollama is currently using GPU via 'ollama ps'."""
    try:
        out = run(["ollama", "ps"], capture=True, check=False)
        if out and "GPU" in out.upper():
            return True
    except Exception:
        pass
    return False


def step_hardware() -> dict:
    banner("Step 4 / 8 : Hardware Detection")

    import psutil

    # GPU detection
    has_gpu = False
    gpu_type = "none"
    gpu_name = None
    vram = 0.0

    found_nv, nv_name, nv_vram = _detect_nvidia()
    if found_nv:
        has_gpu, gpu_type, gpu_name, vram = True, "nvidia", nv_name, nv_vram
        ok(f"NVIDIA GPU: {nv_name} ({nv_vram:.0f} GB VRAM)")
    else:
        info("No NVIDIA GPU detected")

        found_amd, amd_name, amd_vram = False, None, 0.0
        if platform.system() == "Windows":
            found_amd, amd_name, amd_vram = _detect_amd_windows()
        if not found_amd:
            found_amd, amd_name, amd_vram = _detect_amd_rocm()

        if found_amd:
            has_gpu, gpu_type, gpu_name, vram = True, "amd", amd_name, amd_vram
            ok(f"AMD GPU: {amd_name} ({amd_vram:.0f} GB VRAM)")

            # Check if Ollama is actually using the GPU
            if _check_ollama_gpu():
                ok("Ollama is using GPU acceleration")
            else:
                warn("Ollama may not be using GPU (check 'ollama ps' after loading a model)")
        else:
            info("No AMD GPU detected — will use CPU mode")

    # RAM
    ram = psutil.virtual_memory().total / (1024 ** 3)
    ok(f"RAM: {ram:.0f} GB")

    # CPU
    cores = psutil.cpu_count(logical=False) or psutil.cpu_count()
    ok(f"CPU: {cores} cores")

    hw = {
        "has_gpu": has_gpu, "gpu_type": gpu_type,
        "gpu_name": gpu_name, "vram": vram,
        "ram": ram, "cores": cores,
    }
    return hw


# ═══════════════════════════════════════════════════════════════════
# Step 5: Model selection & download
# ═══════════════════════════════════════════════════════════════════

def _ollama_models() -> set:
    """Get set of model names currently available in Ollama."""
    resp = http_get(f"{OLLAMA_URL}/api/tags")
    if not resp:
        return set()
    try:
        data = json.loads(resp)
        return {m["name"] for m in data.get("models", [])}
    except (json.JSONDecodeError, KeyError):
        return set()


def step_models(hw: dict, check_only: bool = False) -> dict:
    banner("Step 5 / 8 : Model Selection & Download")

    vram = hw["vram"]
    ram = hw["ram"]

    # Find best tier
    extract = verify = write = "phi3:mini"
    tier_name = "Minimum"
    for min_vram, min_ram, label, e, v, w in MODEL_TIERS:
        if vram >= min_vram and ram >= min_ram:
            extract, verify, write = e, v, w
            tier_name = label
            break

    print(f"  Hardware tier: {tier_name}")
    print(f"  Recommended models:")
    print(f"    Extract:  {extract}")
    print(f"    Verify:   {verify}")
    print(f"    Write:    {write}")
    print()

    if not check_only and not ask("Use these models?"):
        extract = input(f"  Extract model [{extract}]: ").strip() or extract
        verify  = input(f"  Verify model  [{verify}]: ").strip() or verify
        write   = input(f"  Write model   [{write}]: ").strip() or write

    models = {"extract": extract, "verify": verify, "write": write}
    unique = list(set(models.values()))

    # Check what's already pulled
    available = _ollama_models()
    already = [m for m in unique if m in available]
    needed  = [m for m in unique if m not in available]

    if already:
        ok(f"Already pulled: {', '.join(already)}")
    if not needed:
        ok("All models available")
        return models

    if check_only:
        fail(f"Missing models: {', '.join(needed)}")
        return models

    print(f"\n  Need to download {len(needed)} model(s): {', '.join(needed)}")
    print(f"  This may take a while (models are 4-20 GB each).\n")

    if not ask("Download now?"):
        warn("Skipping model download — you can pull models later with 'ollama pull <model>'")
        return models

    for model in needed:
        info(f"Pulling {model}...")
        try:
            subprocess.run(["ollama", "pull", model], check=True)
            ok(f"Downloaded {model}")
        except subprocess.CalledProcessError:
            fail(f"Failed to download {model}")
            print(f"  Try manually: ollama pull {model}")

    # Verify
    available = _ollama_models()
    still_missing = [m for m in unique if m not in available]
    if still_missing:
        warn(f"Still missing: {', '.join(still_missing)}")
    else:
        ok("All models ready")

    return models


# ═══════════════════════════════════════════════════════════════════
# Step 6: SearXNG setup (Docker)
# ═══════════════════════════════════════════════════════════════════

def _searxng_is_running() -> bool:
    resp = http_get(f"{SEARXNG_URL}/search?q=test&format=json")
    return resp is not None


def _create_searxng_config() -> None:
    """Generate searxng/settings.yml and limiter.toml."""
    SEARXNG_DIR.mkdir(exist_ok=True)

    settings_path = SEARXNG_DIR / "settings.yml"
    if not settings_path.exists():
        secret = secrets.token_hex(32)
        settings_path.write_text(f"""# SearXNG settings — generated by setup.py
use_default_settings: true

server:
  secret_key: "{secret}"
  limiter: true
  image_proxy: true

redis:
  url: redis://redis:6379/0

ui:
  static_use_hash: true

search:
  safe_search: 0
  autocomplete: ""

enabled_plugins:
  - 'Hash plugin'
  - 'Self Information'
  - 'Tracker URL remover'

engines:
  - name: google
    disabled: false
  - name: bing
    disabled: false
  - name: duckduckgo
    disabled: false
  - name: wikipedia
    disabled: false
""", encoding="utf-8")
        ok("Created searxng/settings.yml")
    else:
        ok("searxng/settings.yml already exists")

    limiter_path = SEARXNG_DIR / "limiter.toml"
    if not limiter_path.exists():
        limiter_path.write_text("""# SearXNG rate limiter config
[botdetection.ip_limit]
link_token = true
""", encoding="utf-8")
        ok("Created searxng/limiter.toml")
    else:
        ok("searxng/limiter.toml already exists")


def step_searxng(check_only: bool = False) -> bool:
    banner("Step 6 / 8 : SearXNG Search Engine")

    # Already running?
    if _searxng_is_running():
        ok(f"SearXNG already running at {SEARXNG_URL}")
        return True

    if check_only:
        fail(f"SearXNG not responding at {SEARXNG_URL}")
        return False

    # Check compose file exists
    if not COMPOSE_FILE.exists():
        fail(f"Missing {COMPOSE_FILE}")
        return False

    # Generate config files
    _create_searxng_config()

    # Start containers
    info("Starting SearXNG + Redis via Docker Compose...")
    try:
        run(["docker", "compose", "-f", str(COMPOSE_FILE), "up", "-d"], timeout=60)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        fail(f"Docker Compose failed: {e}")
        print("  Check: is Docker Desktop running?")
        print(f"  Manual start: docker compose -f {COMPOSE_FILE} up -d")
        return False

    # Wait for health
    info("Waiting for SearXNG to be ready (this can take 30-90s)...")
    for i in range(18):  # 90 seconds
        time.sleep(5)
        if _searxng_is_running():
            ok(f"SearXNG ready at {SEARXNG_URL}")
            return True
        info(f"Waiting... ({(i+1)*5}s)")

    # Might still be starting — check container status
    warn("SearXNG not responding yet")
    try:
        out = run(["docker", "compose", "-f", str(COMPOSE_FILE), "ps"],
                  capture=True, check=False)
        if out:
            print(f"\n{out}\n")
    except Exception:
        pass
    warn("SearXNG may need more time. Check: docker compose -f docker-compose.searxng.yml logs searxng")
    return False


# ═══════════════════════════════════════════════════════════════════
# Step 7: Configuration files
# ═══════════════════════════════════════════════════════════════════

CONFIG_TEMPLATE = """\
ollama:
  base_url: "{ollama_url}"

  model_extract: "{extract}"
  model_verify: "{verify}"
  model_write: "{write}"
  model_consolidate: "{extract}"
  model_verify_group: "{verify}"

  temperature_extract: 0.0
  temperature_verify: 0.0
  temperature_consolidate: 0.1
  temperature_write: 0.5
  model_query_gen: "{extract}"
  temperature_query_gen: 0.3

searx:
  base_url: "{searxng_url}"
  format: "json"
  num_results: 10

  deny_domains:
    - "pinterest.com"
    - "facebook.com"
    - "twitter.com"
    - "x.com"
    - "tiktok.com"
    - "instagram.com"
    - "medium.com"
    - "substack.com"
    - "reddit.com"
    - "quora.com"
    - "yahoo.com"
    - "tumblr.com"
    - "blogger.com"
    - "blogspot.com"
    - "wordpress.com"

budgets:
  max_claims: 25
  max_sources_per_claim: 5
  max_failures_per_domain: 6
  max_fetches_per_run: 80
  fetch_timeout_sec: 25
  snippets_per_source: 4
  snippet_max_chars: 1200
  extract_chunk_overlap: 8

  queries_per_claim: 3
  enable_query_generation: true
  query_gen_workers: 3
  enable_source_prefilter: true
  min_preview_score: 0.15
  enable_factcheck_query: true

  second_pass_enabled: true
  second_pass_max_claims: 12
  second_pass_extra_sources_per_claim: 5
  second_pass_extra_fetches: 60

output:
  timezone: "America/Los_Angeles"

logging:
  level: "INFO"

cache:
  url_cache_days: 7
"""


def step_config(models: dict, hw: dict, check_only: bool = False) -> bool:
    banner("Step 7 / 8 : Configuration Files")

    # config.yaml
    if CONFIG_FILE.exists():
        ok(f"config.yaml exists")
        # Validate it's parseable
        try:
            import yaml
            with open(CONFIG_FILE, encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
            if "ollama" in cfg and "searx" in cfg:
                ok("config.yaml is valid")
            else:
                warn("config.yaml missing 'ollama' or 'searx' sections")
        except Exception as e:
            warn(f"config.yaml parse error: {e}")
    else:
        if check_only:
            fail("config.yaml does not exist")
            return False
        info("Generating config.yaml...")
        content = CONFIG_TEMPLATE.format(
            ollama_url=OLLAMA_URL,
            searxng_url=SEARXNG_URL,
            extract=models["extract"],
            verify=models["verify"],
            write=models["write"],
        )
        CONFIG_FILE.write_text(content, encoding="utf-8")
        ok("Created config.yaml")

    # .env file
    if ENV_FILE.exists():
        ok(".env file exists")
    else:
        if check_only:
            warn(".env file does not exist (optional — config.yaml is primary)")
        else:
            info("Generating .env...")
            env_content = f"""# Evident Video Fact Checker — generated by setup.py
EVIDENT_OLLAMA_BASE_URL={OLLAMA_URL}
EVIDENT_SEARXNG_BASE_URL={SEARXNG_URL}
EVIDENT_MODEL_EXTRACT={models['extract']}
EVIDENT_MODEL_VERIFY={models['verify']}
EVIDENT_MODEL_WRITE={models['write']}
EVIDENT_TEMPERATURE_EXTRACT=0.0
EVIDENT_TEMPERATURE_VERIFY=0.0
EVIDENT_TEMPERATURE_WRITE=0.5
EVIDENT_GPU_ENABLED={'true' if hw['has_gpu'] else 'false'}
EVIDENT_GPU_TYPE={hw['gpu_type']}
EVIDENT_GPU_MEMORY_GB={hw['vram']:.1f}
EVIDENT_RAM_GB={hw['ram']:.1f}
EVIDENT_MAX_CLAIMS=25
EVIDENT_CACHE_TTL_DAYS=7
EVIDENT_LOG_LEVEL=INFO
"""
            ENV_FILE.write_text(env_content, encoding="utf-8")
            ok("Created .env")

    # Directories
    dirs = ["cache", "runs", "store", "inbox", "logs"]
    for d in dirs:
        (PROJECT_ROOT / d).mkdir(exist_ok=True)
    ok(f"Runtime directories ready: {', '.join(dirs)}")

    return True


# ═══════════════════════════════════════════════════════════════════
# Step 8: Validation & Smoke Test
# ═══════════════════════════════════════════════════════════════════

def step_validate_and_test(models: dict, check_only: bool = False) -> bool:
    banner("Step 8 / 8 : Validation & Smoke Test")

    all_ok = True

    # ── Service checks ────────────────────────────────────────────
    print("  Service checks:")

    # Ollama API
    resp = http_get(f"{OLLAMA_URL}/api/tags")
    if resp:
        ok("Ollama API responding")
        # Check required models
        available = _ollama_models()
        for role, model in models.items():
            if model in available:
                ok(f"Model '{model}' ({role}) available")
            else:
                warn(f"Model '{model}' ({role}) NOT available — run 'ollama pull {model}'")
                all_ok = False
    else:
        fail(f"Ollama not responding at {OLLAMA_URL}")
        all_ok = False

    # SearXNG API
    if _searxng_is_running():
        ok("SearXNG API responding")
    else:
        fail(f"SearXNG not responding at {SEARXNG_URL}")
        all_ok = False

    # Config
    if CONFIG_FILE.exists():
        ok("config.yaml present")
    else:
        fail("config.yaml missing")
        all_ok = False

    # Directories
    for d in ["cache", "runs", "store", "inbox", "logs"]:
        p = PROJECT_ROOT / d
        if p.is_dir():
            ok(f"Directory: {d}/")
        else:
            fail(f"Directory missing: {d}/")
            all_ok = False

    if not all_ok:
        fail("Some checks failed — fix issues above and re-run 'python setup.py --check'")
        return False

    # ── Smoke test ────────────────────────────────────────────────
    print()
    print("  Smoke test (end-to-end pipeline check):")

    smoke_ok = True
    t0 = time.time()

    # 1. LLM test — send a simple prompt to Ollama
    info("Testing LLM (Ollama)...")
    llm_resp = http_post_json(f"{OLLAMA_URL}/api/generate", {
        "model": models["extract"],
        "prompt": "Say hello in one word. /no_think",
        "stream": False,
        "options": {"num_predict": 32, "temperature": 0.0},
    }, timeout=120)
    if llm_resp:
        try:
            data = json.loads(llm_resp)
            text = data.get("response", "").strip()
            duration = data.get("total_duration", 0) / 1e9  # nanoseconds → seconds
            ok(f"LLM responded in {duration:.1f}s ({models['extract']})")
        except json.JSONDecodeError:
            ok(f"LLM responded ({models['extract']})")
    else:
        fail("LLM did not respond within 120s")
        smoke_ok = False

    # 2. Search test — query SearXNG
    info("Testing search (SearXNG)...")
    search_resp = http_get(
        f"{SEARXNG_URL}/search?q=python+programming&format=json"
    )
    if search_resp:
        try:
            data = json.loads(search_resp)
            n = len(data.get("results", []))
            ok(f"Search returned {n} results")
        except json.JSONDecodeError:
            warn("Search response not valid JSON")
    else:
        fail("Search did not respond")
        smoke_ok = False

    # 3. HTTP fetch test
    info("Testing HTTP fetch...")
    fetch_resp = http_get("https://httpbin.org/get", timeout=15)
    if fetch_resp:
        ok("HTTP fetch working")
    else:
        # httpbin might be blocked; try a simpler test
        fetch_resp2 = http_get("https://example.com", timeout=15)
        if fetch_resp2:
            ok("HTTP fetch working")
        else:
            warn("HTTP fetch failed (may be a network issue)")

    elapsed = time.time() - t0
    print()

    if smoke_ok:
        ok(f"Smoke test passed ({elapsed:.1f}s)")
    else:
        fail("Smoke test had failures — check issues above")

    return smoke_ok


# ═══════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════

def main():
    check_only = "--check" in sys.argv

    mode = "VALIDATE" if check_only else "SETUP"
    print(f"""
{'=' * 64}
  Evident Video Fact Checker — {mode} Wizard
{'=' * 64}

  This wizard will:
    1. Check Python & install pip dependencies
    2. Verify Ollama LLM service
    3. Verify Docker (for SearXNG) & FFmpeg
    4. Detect hardware (GPU, RAM, CPU)
    5. Select & download Ollama models
    6. Start SearXNG search engine
    7. Generate configuration files
    8. Validate everything & run smoke test
""")

    if not check_only and not ask("Continue?"):
        print("  Setup cancelled.")
        sys.exit(0)

    # Change to project root so all relative paths work
    os.chdir(PROJECT_ROOT)

    # Step 1: Python & deps
    if not step_python_deps(check_only):
        fail("Cannot continue without Python dependencies")
        sys.exit(1)

    # Step 2: Ollama
    if not step_ollama(check_only):
        fail("Cannot continue without Ollama")
        sys.exit(1)

    # Step 3: Docker & FFmpeg
    if not step_docker_and_ffmpeg(check_only):
        fail("Cannot continue without Docker (needed for SearXNG)")
        sys.exit(1)

    # Step 4: Hardware (always runs — informational)
    hw = step_hardware()

    # Step 5: Models
    models = step_models(hw, check_only)

    # Step 6: SearXNG
    if not step_searxng(check_only):
        warn("SearXNG setup had issues — search may not work")
        if check_only:
            sys.exit(1)

    # Step 7: Config & directories
    if not step_config(models, hw, check_only):
        if check_only:
            sys.exit(1)

    # Step 8: Validate & smoke test
    success = step_validate_and_test(models, check_only)

    # ── Done ──────────────────────────────────────────────────────
    print()
    if success:
        banner("SETUP COMPLETE")
        print("""  Everything is working! Here's how to run:

  From a YouTube URL:
    python -m app.main --url "https://www.youtube.com/watch?v=VIDEO_ID"

  From a transcript file:
    python -m app.main --infile inbox/transcript.txt --channel "ChannelName"

  With interactive review:
    python -m app.main --url "..." --review

  Web UI:
    python -m app.web.server
    Then open http://localhost:8000

  Manage services:
    docker compose -f docker-compose.searxng.yml logs     # SearXNG logs
    docker compose -f docker-compose.searxng.yml restart   # Restart SearXNG
    docker compose -f docker-compose.searxng.yml down      # Stop SearXNG

  Re-validate setup:
    python setup.py --check
""")
    else:
        banner("SETUP INCOMPLETE")
        print("  Some steps had issues. Fix the problems above and re-run:")
        print("    python setup.py")
        print()
        print("  Or validate without changes:")
        print("    python setup.py --check")
        print()
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Setup cancelled.")
        sys.exit(1)
    except Exception as e:
        fail(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
