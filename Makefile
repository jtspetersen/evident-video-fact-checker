# Evident Video Fact Checker
# Shortcuts — all service management via setup.py

.PHONY: help setup check start stop status web run logs models pull clean

.DEFAULT_GOAL := help

help: ## Show all commands
	@echo ""
	@echo "  Evident Video Fact Checker"
	@echo "  ========================="
	@echo ""
	@echo "  Setup & Services:"
	@echo "    make setup           Run interactive setup wizard"
	@echo "    make check           Validate setup + smoke test"
	@echo "    make start           Start Ollama + SearXNG"
	@echo "    make stop            Stop SearXNG containers"
	@echo "    make status          Show service health"
	@echo ""
	@echo "  Run Pipeline:"
	@echo "    make web             Start web UI (http://localhost:8000)"
	@echo '    make run URL="..."   Fact-check a YouTube video'
	@echo '    make run FILE="..."  Fact-check a transcript file'
	@echo ""
	@echo "  Models & Maintenance:"
	@echo "    make models          List Ollama models"
	@echo "    make pull M=...      Pull an Ollama model"
	@echo "    make logs            Tail SearXNG logs"
	@echo "    make clean           Clear URL cache"
	@echo ""

setup:
	python setup.py

check:
	python setup.py --check

start:
	python setup.py start

stop:
	python setup.py stop

status:
	python setup.py status

web:
	python -m app.web.server

run:
	@if [ -n "$(URL)" ]; then \
		python -m app.main --url "$(URL)"; \
	elif [ -n "$(FILE)" ]; then \
		python -m app.main --infile "$(FILE)" $(if $(CHANNEL),--channel "$(CHANNEL)",); \
	else \
		echo 'Usage:'; \
		echo '  make run URL="https://www.youtube.com/watch?v=VIDEO_ID"'; \
		echo '  make run FILE="inbox/transcript.txt" CHANNEL="ChannelName"'; \
		exit 1; \
	fi

models:
	@ollama list

pull:
	@if [ -z "$(M)" ]; then echo "Usage: make pull M=qwen3:8b"; exit 1; fi
	ollama pull $(M)

logs:
	docker compose -f docker-compose.searxng.yml logs -f

clean:
	@echo "Clearing URL cache..."
	@rm -rf cache/url/*
	@echo "Done."
