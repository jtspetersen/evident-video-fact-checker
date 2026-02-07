# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-02-05

### Added
- **YouTube URL Ingest**: Accept YouTube URLs via CLI (`--url`) and web UI to auto-fetch transcripts. Tries YouTube captions first, falls back to local Whisper transcription.
- **Video Metadata**: Automatically extracts title, channel, duration, and upload date from YouTube videos via yt-dlp.
- **Whisper Fallback**: Downloads audio and transcribes locally with faster-whisper (model=small, cpu, int8) when no captions are available.
- **FFmpeg Auto-Detection**: Searches winget packages, Chocolatey, Scoop, and Program Files paths when ffmpeg is not in PATH.
- **FFmpeg Setup**: Interactive setup wizard (`setup.py`) now offers to install ffmpeg automatically via winget/apt/brew.
- **Web UI URL Mode**: Toggle between file upload and YouTube URL input on the index page, with dedicated SSE progress panel for YouTube fetch stage.
- **YouTube Progress Events**: Real-time SSE updates during transcript fetch (caption lookup, audio download, Whisper transcription).

### Fixed
- **youtube-transcript-api v1.x Compatibility**: Updated from deprecated class methods to instance-based API (`YouTubeTranscriptApi()`, `.list()`, `.fetch()`, `.snippets`).
- **Timestamp Preservation**: Both caption and Whisper methods now include timestamps in M:SS/H:MM:SS format, compatible with `normalize_transcript`.
- **Web UI Crash on YouTube URLs**: Fixed `os.path.basename(None)` crash when `infile` is None for YouTube URL runs.
- **Channel Name Capture**: Channel slug and output directory are now updated after YouTube metadata is fetched, instead of showing "unknown".
- **H:MM:SS Timestamp Support**: `normalize_transcript` regex updated to handle hour-long videos with H:MM:SS timestamps.

### Changed
- **Dependencies**: Added youtube-transcript-api, yt-dlp, faster-whisper to Requirements.txt.
- **CLI**: `--url` and `--infile` are mutually exclusive; `--channel` auto-inferred from YouTube metadata.
- **Web Runner**: New `fetch_transcript` stage in pipeline, with outdir rename after metadata is available.
- **Documentation**: Updated README and CLAUDE.md with YouTube URL usage, FFmpeg requirements, and web UI features.

### Technical Details
**Commits**: 6 commits on `yt-transcript-ingest` branch
- New: `app/tools/youtube.py` (287 lines)
- Modified: `app/main.py`, `app/pipeline/ingest.py`, `app/web/runner.py`, `app/web/server.py`
- Modified: `app/web/templates/index.html`, `app/web/templates/progress.html`
- Modified: `Requirements.txt`, `setup.py`, `CLAUDE.md`, `Readme.md`

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
