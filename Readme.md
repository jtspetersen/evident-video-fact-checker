# Evident Video Fact Checker

A local fact-checking pipeline for analyzing video transcripts and verifying claims using evidence-based research.

## Features

- **Transcript ingestion** - Upload a file or paste a YouTube URL; auto-fetches captions or transcribes locally with Whisper
- **Claim extraction** - Overlapping chunks prevent missing claims at segment boundaries
- **Evidence retrieval** - 6-tier quality system prioritizes scholarly sources over forums/blogs
- **Claim verification** - LLM reasoning with citations, confidence scoring, and rhetorical analysis
- **Report generation** - Detailed verdicts with verdict count summaries, and video script outline

## Setup

### Prerequisites

| Requirement | Purpose | Install |
|-------------|---------|---------|
| **Python 3.11+** | Runtime | [python.org](https://www.python.org/downloads/) |
| **Ollama** | Local LLM server (GPU recommended) | [ollama.com](https://ollama.com/) |
| **SearXNG + Redis** | Metasearch for evidence retrieval | See Docker step below |
| **FFmpeg** | YouTube Whisper fallback (optional) | `winget install Gyan.FFmpeg` / `apt install ffmpeg` / `brew install ffmpeg` |

### Install

```bash
# 1. Install Python dependencies
pip install -r Requirements.txt

# 2. Start Ollama (if not already running)
ollama serve

# 3. Pull recommended models
ollama pull qwen3:8b
ollama pull qwen3:30b
ollama pull gemma3:27b

# 4. Start SearXNG (metasearch engine)
docker compose -f docker/docker-compose.yml up -d searxng redis
```

Or use the interactive setup wizard for guided configuration:

```bash
python setup.py
```

### Hardware Recommendations

| VRAM | RAM | Recommended Models |
|------|-----|-------------------|
| 24GB+ | 32GB+ | qwen3:30b, gemma3:27b |
| 12-16GB | 32GB+ | qwen3:14b, llama3:8b |
| 8GB | 16GB+ | qwen3:8b, llama3:8b |
| None | 32GB+ | qwen3:8b (CPU mode) |

## Web UI

Start the web server and open **http://localhost:8000** in your browser:

```bash
python -m app.web.server
```

The web UI provides:
- Upload transcripts via drag-and-drop or paste a YouTube URL
- Real-time progress dashboard with per-stage progress bars
- Live counters for claims, sources, snippets, and failures
- Optional claim review step — edit or drop claims before verification
- Rendered report with verdict summary badges and artifact downloads
- Past runs history

## CLI

### From a YouTube URL

```bash
python -m app.main --url "https://www.youtube.com/watch?v=VIDEO_ID"
```

Auto-fetches captions when available, or transcribes with Whisper as fallback. Channel name is inferred from YouTube metadata.

### From a transcript file

```bash
python -m app.main --infile "inbox/transcript.txt" --channel "Channel Name"
```

Place transcript files in `inbox/`. If `--infile` is omitted, the newest file in `inbox/` is used.

### Flags

| Flag | Description | Default |
|------|-------------|---------|
| `--url <youtube-url>` | YouTube video URL | — |
| `--infile <path>` | Path to transcript file | Newest in `inbox/` |
| `--channel <name>` | Channel/creator name | Inferred from filename or YouTube metadata |
| `--review` | Interactive claim review mode | Disabled |
| `--verbose` | Show DEBUG output | Disabled |
| `--quiet` | Errors/warnings only | Disabled |

`--url` and `--infile` are mutually exclusive.

## Configuration

### Environment Variables (.env)

```bash
# Service URLs
EVIDENT_OLLAMA_BASE_URL=http://localhost:11434
EVIDENT_SEARXNG_BASE_URL=http://localhost:8080

# Model selections
EVIDENT_MODEL_EXTRACT=qwen3:8b
EVIDENT_MODEL_VERIFY=qwen3:30b
EVIDENT_MODEL_WRITE=gemma3:27b
```

### config.yaml

```yaml
ollama:
  model_extract: "qwen3:8b"      # Claim extraction
  model_verify: "qwen3:30b"      # Verification
  model_write: "gemma3:27b"      # Script writing

budgets:
  max_claims: 25
  max_sources_per_claim: 5
  max_fetches_per_run: 80
```

### Verdict Ratings

| Rating | Meaning |
|--------|---------|
| VERIFIED | Confirmed by strong evidence |
| LIKELY TRUE | Supported but not fully confirmed |
| INSUFFICIENT EVIDENCE | Not enough quality sources found |
| CONFLICTING EVIDENCE | Credible sources disagree |
| LIKELY FALSE | Evidence suggests the claim is wrong |
| FALSE | Clearly contradicted by strong evidence |

### Source Quality Tiers

| Tier | Description | Examples |
|------|-------------|----------|
| 1 | Top scholarly journals | Nature, Science, NEJM |
| 2 | Academic institutions | .edu, .ac.uk |
| 3 | Government/International orgs | .gov, WHO, UN |
| 4 | Research organizations | Pew Research, Brookings |
| 5 | Established news agencies | Reuters, AP, BBC |
| 6 | Everything else | - |

## Output

Each run creates a timestamped directory:

```
runs/YYYYMMDD_HHMMSS__channel__video_title/
├── 00_transcript.raw.txt           # Original input
├── 01_transcript.json              # Normalized segments
├── 02_claims.json                  # Extracted claims
├── 03_sources.json                 # Retrieved evidence
├── 04_snippets.json                # Evidence snippets
├── 05_verdicts.json                # Verification results
├── 06_scorecard.md                 # Verdict counts and source tiers
├── 07_summary.md                   # Fact-check report
├── run.json                        # Run metadata
└── run.log                         # Execution log
```

## Project Structure

```
evident-video-fact-checker/
├── app/                    # Application code
│   ├── main.py             # CLI entry point
│   ├── pipeline/           # Processing stages
│   ├── schemas/            # Pydantic models
│   ├── store/              # Store modules
│   ├── tools/              # Utilities (fetch, parse, ollama, youtube)
│   └── web/                # Web UI (FastAPI + HTMX)
│       ├── server.py       # Routes and SSE endpoint
│       ├── runner.py       # Background pipeline runner
│       ├── templates/      # Jinja2 HTML templates
│       └── static/         # Vendored CSS/JS (Pico.css, HTMX)
├── docker/                 # Docker configuration
│   ├── docker-compose.yml
│   ├── docker-compose.gpu.yml      # NVIDIA GPU override
│   ├── docker-compose.amd.yml      # AMD ROCm override
│   └── Dockerfile
├── inbox/                  # Input transcripts
├── runs/                   # Output directories (timestamped)
├── cache/                  # URL cache (gitignored)
├── store/                  # Persistent storage (gitignored)
├── searxng/                # SearXNG configuration
├── config.yaml             # Application config
├── .env                    # Environment variables
├── setup.py                # Interactive setup wizard
└── Makefile                # Make commands
```

## Docker

For a fully containerized setup, see [DOCKER.md](DOCKER.md).

```bash
# Start all services
docker compose -f docker/docker-compose.yml up -d

# Run pipeline in Docker
docker compose -f docker/docker-compose.yml run --rm app python -m app.main --infile inbox/transcript.txt
```

## Make Commands

```bash
make help              # Show all commands
make setup             # Run setup wizard
make web               # Start web UI at http://localhost:8000
make runvid ARGS='...' # Run natively (recommended)
make start             # Start Docker services
make stop              # Stop Docker services
make status            # Show service status
make logs              # Tail all logs
make models            # List Ollama models
```

## Documentation

- [DOCKER.md](DOCKER.md) - Detailed Docker setup guide
- [MIGRATION.md](MIGRATION.md) - Migration from legacy setup
- [CLAUDE.md](CLAUDE.md) - Project context for AI assistants
