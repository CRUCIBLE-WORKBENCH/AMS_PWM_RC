# Launch this workflow through Crucible in Linux/WSL.
IGNY ?= igny
IGNY_ENV ?= ams-pwm-rc
IGNY_SCRIPT = $(IGNY) run script --env $(IGNY_ENV)
.DEFAULT_GOAL := help
.NOTPARALLEL:
.PHONY: help setup check sed build run smoke report preflight digital analogue

help:
	@echo "igny run --env $(IGNY_ENV) make run - execute the complete experiment and independent checks"
	@echo "igny run --env $(IGNY_ENV) make build - prepare the project build artifacts"
	@echo "igny run --env $(IGNY_ENV) make smoke - verify existing results; does not rebuild"
	@echo "igny run --env $(IGNY_ENV) make setup - prepare pinned project-local observer dependencies"
	@echo "igny run --env $(IGNY_ENV) make check - check Python observer imports"
	@echo "igny run --env $(IGNY_ENV) make sed - normalise public shell inputs to LF"
	@echo "igny run --env $(IGNY_ENV) make report - print generated result summaries"
	@echo "igny run --env $(IGNY_ENV) make preflight - review public package paths, links and hashes"

setup:
	$(IGNY_SCRIPT) scripts/demo_info.py -- setup

check:
	$(IGNY_SCRIPT) scripts/demo_info.py -- check

sed:
	$(IGNY_SCRIPT) scripts/demo_info.py -- normalise

report:
	$(IGNY_SCRIPT) scripts/demo_info.py -- report

preflight:
	$(IGNY_SCRIPT) scripts/preflight_git.py

build: sed digital

run: sed check build analogue smoke

digital:
	$(IGNY_SCRIPT) scripts/run.sh -- digital

analogue:
	$(IGNY_SCRIPT) scripts/run.sh -- analogue

smoke:
	$(IGNY_SCRIPT) scripts/demo_info.py -- verify
