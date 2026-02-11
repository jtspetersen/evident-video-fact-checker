# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2026-02-10

### Added
- **Web UI Overhaul**: Redesigned all templates with consistent layout — logo, nav buttons ("Start New" / "History"), and unified page headers across progress, review, report, and runs pages.
- **Dynamic Video Titles**: Progress and review pages display "Fact-Checking Video: {title}" with real-time SSE updates from YouTube metadata.
- **Token Usage Tracking**: Captures prompt and completion token counts from Ollama API responses per-stage and per-run, stored in `run.json` manifest under `token_usage` and `timings.{stage}.tokens`.
- **Video Title & Channel in Run History**: Runs table now shows Video Title and Channel columns with fallback enrichment from manifests for older runs.
- **Report Metadata**: Report page shows Video Title, Channel, ID, and Date inline, replacing the LLM-generated header.
- **Upload Form Improvements**: Video Title and Channel fields shown only in Upload File mode, both required with per-mode JS validation.

### Changed
- **Pipeline Stages Simplified**: Merged 9 stages into 6 in web UI (Prepare Transcript, Extract Claims, Review Claims, Gather Evidence, Check Claims, Fact-Check Summary).
- **Stage Timeline**: Server-side CSS class rendering from manifest timings survives page reloads and navigation between progress/review pages.
- **Review Page**: Header matches progress page layout; added "Review Extracted Claims" H2 with claim count instruction; Edit feature deprecated.
- **Download Artifacts**: Restyled as a collapsible details section with background panel.

### Fixed
- **Review Redirect Bug**: Completed stage indicators no longer reset to grey when navigating to/from the review page.

## [0.3.0] - 2026-02-05

### Added
- **YouTube URL Ingest**: Accept YouTube URLs via CLI (`--url`) and web UI to auto-fetch transcripts. Tries YouTube captions first, falls back to local Whisper transcription via faster-whisper.
- **Video Metadata**: Automatically extracts title, channel, duration, and upload date from YouTube videos via yt-dlp.
- **FFmpeg Auto-Detection**: Searches winget packages, Chocolatey, Scoop, and Program Files paths when ffmpeg is not in PATH.
- **Web UI**: Browser-based interface (FastAPI + HTMX + Jinja2 + Pico.css, all vendored) with real-time progress dashboard, claim review, report rendering, and past runs history.
- **Web UI URL Mode**: Toggle between file upload and YouTube URL input, with dedicated SSE progress panel for YouTube fetch stage.
- **Docker support**: Full Docker setup with `docker-compose.yml`, GPU overrides for NVIDIA and AMD, and interactive setup wizard (`setup.py`).
- **Claim Consolidation**: Deduplication and narrative grouping of related claims with group-level verdicts.

### Fixed
- **youtube-transcript-api v1.x Compatibility**: Updated from deprecated class methods to instance-based API (`YouTubeTranscriptApi()`, `.list()`, `.fetch()`, `.snippets`).
- **Timestamp Preservation**: Both caption and Whisper methods now include timestamps in M:SS/H:MM:SS format, compatible with `normalize_transcript`.
- **Web UI Crash on YouTube URLs**: Fixed `os.path.basename(None)` crash when `infile` is None for YouTube URL runs.
- **Channel Name Capture**: Channel slug and output directory are now updated after YouTube metadata is fetched, instead of showing "unknown".

### Changed
- **Verdict ratings**: Replaced `UNCERTAIN` with `INSUFFICIENT EVIDENCE` and `CONFLICTING EVIDENCE`.
- **Score removal**: Removed numerical 0-100 score. Reports now show verdict count badges instead.
- **Dependencies**: Added youtube-transcript-api, yt-dlp, faster-whisper to Requirements.txt.
- **CLI**: `--url` and `--infile` are mutually exclusive; `--channel` auto-inferred from YouTube metadata.
- **Parallel processing**: `ThreadPoolExecutor` for evidence fetching (8 workers) and verification (3 workers).

### Removed
- `runvid` / `runvid.bat` scripts (replaced by `run.sh` and `make` commands)
- Numerical truthfulness score from scorecard, reports, and creator profiles

## [0.2.0] - 2026-02-05

### Fixed
- **Verification Accuracy**: Fixed asymmetric archetype gates - relaxed tier requirements for FALSE/LIKELY FALSE ratings while maintaining strict requirements for VERIFIED/LIKELY TRUE. FALSE ratings improved from 7% → 60% in test runs.
- **Source Quality**: Enhanced 6-tier source quality system now properly categorizes scholarly journals (tier 1), academic institutions (tier 2), government/international orgs (tier 3), research organizations (tier 4), news agencies (tier 5), and general websites (tier 6).
- **Claim Extraction**: Implemented overlapping chunks (5 segment overlap) with 85% similarity-based deduplication to prevent missing claims at chunk boundaries.
- **Empty Content Handling**: Added comprehensive diagnostic logging for when Ollama returns empty responses, capturing model parameters, prompt lengths, and response metadata.

### Added
- **Citation Enforcement**: Added explicit CRITICAL CITATION RULES to LLM prompts requiring all evidence snippets used in reasoning to be cited.
- **Rhetorical Analysis**: Added detection of when true facts are used to support false conclusions (false causation, cherry-picking, correlation as causation, appeal to fear, false dichotomies).
- **Source Filtering**: Expanded deny_domains to exclude reddit, forums, blogs, and social media platforms.
- **runvid Script**: New bash script that auto-activates virtual environment before running the pipeline.
- **Progress Bars**: Added tqdm progress indicators for LLM generation (streaming mode).

### Changed
- **README**: Comprehensive documentation update with CLI flags, configuration details, and usage examples.
- **Claim Prompts**: Enhanced extraction prompts to require COMPLETE and SELF-CONTAINED claims, with instructions to COMBINE related claims forming single logical arguments.
- **Requirements**: Added tqdm dependency for progress bars.

### Technical Details
**Files Modified**: 14 files (+892/-101 lines)
- Core: verify_claims.py, extract_claims.py, retrieve_evidence.py
- Tools: ollama_client.py
- Schema: verdict.py
- Config: config.yaml
- Docs: README.md
- New: runvid, runvid.bat

## [0.1.0] - 2026-02-04

### Added
- Initial MVP release
- Transcript normalization pipeline
- LLM-based claim extraction
- Web evidence retrieval via SearX
- Claim verification with LLM reasoning
- Scorecard generation (0-100 truthfulness score)
- Review video script generation
- Interactive claim review mode
- Configurable budgets and rate limits
- URL caching with TTL
- JSON-based data persistence
