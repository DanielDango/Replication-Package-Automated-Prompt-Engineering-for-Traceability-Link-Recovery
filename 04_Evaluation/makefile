# Parent Makefile to run experiments in subdirectories

# Find all experiment subdirectories (adjust pattern as needed)
EXPERIMENT_DIRS := $(shell find . -mindepth 1 -maxdepth 1 -type d ! -name '.*')

# Java source configuration (relative to parent dir)
JAVA_SRC_DIR := ../../../03_Code/LiSSA_RATLR
SRC_DIR := $(JAVA_SRC_DIR)/src
TARGET_DIR := $(JAVA_SRC_DIR)/target
REQ2REQ_SRC := $(JAVA_SRC_DIR)/datasets/req2req
ENV_SRC := $(JAVA_SRC_DIR)/.env
SHARED_ENV := .env

# Output configuration
OUTPUT_DIR := ../../Document/tables
PROMPT_DIR := ../../Document/prompts

.PHONY: all clean help list-experiments ensure-env

# Ensure shared .env exists
ensure-env: $(SHARED_ENV)

$(SHARED_ENV):
	@echo "Shared .env not found, copying from $(ENV_SRC)"
	@if [ -f "$(ENV_SRC)" ]; then \
		cp "$(ENV_SRC)" "$(SHARED_ENV)"; \
		echo "Copied .env to parent directory"; \
	else \
		echo "Warning: Source .env file not found at $(ENV_SRC)"; \
		echo "Please create .env file manually"; \
	fi

# Default: run all experiments
all: ensure-env
	@for dir in $(EXPERIMENT_DIRS); do \
		echo "======================================"; \
		echo "Running experiment in $$dir"; \
		echo "======================================"; \
		if [ -f "$(abspath $(SHARED_ENV))" ]; then set -a; . "$(abspath $(SHARED_ENV))"; set +a; fi; \
		$(MAKE) -C $$dir -f ../Makefile.evaluation EXPERIMENT_DIR=$$dir || exit 1; \
	done

# Run specific experiment
run-%: ensure-env
	@if [ -d "$*" ]; then \
		echo "Running experiment in $*"; \
		if [ -f "$(abspath $(SHARED_ENV))" ]; then set -a; . "$(abspath $(SHARED_ENV))"; set +a; fi; \
		$(MAKE) -C $* -f ../Makefile.evaluation EXPERIMENT_DIR=$*; \
	else \
		echo "Error: Directory $* not found"; \
		exit 1; \
	fi

# Clean all experiments
clean:
	@for dir in $(EXPERIMENT_DIRS); do \
		echo "Cleaning $$dir"; \
		if [ -f "$(abspath $(SHARED_ENV))" ]; then set -a; . "$(abspath $(SHARED_ENV))"; set +a; fi; \
		$(MAKE) -C $$dir -f ../Makefile.evaluation clean EXPERIMENT_DIR=$$dir || true; \
	done
	@rm -f $(SHARED_ENV)
	@echo "Removed shared .env"

# List all experiments
list:
	@echo "Available experiments:"
	@for dir in $(EXPERIMENT_DIRS); do \
		echo "  - $$(basename $$dir)"; \
	done

# Generate tables for all experiments
generate-tables: ensure-env
	@for dir in $(EXPERIMENT_DIRS); do \
		echo "Generating table for $$dir"; \
		if [ -f "$(abspath $(SHARED_ENV))" ]; then set -a; . "$(abspath $(SHARED_ENV))"; set +a; fi; \
		$(MAKE) -C $$dir -f ../Makefile.evaluation generate_table EXPERIMENT_DIR=$$dir || true; \
	done

# Help target
help:
	@echo "Available targets:"
	@echo "  all              - Run all experiments"
	@echo "  run-<name>       - Run specific experiment"
	@echo "  clean            - Clean all experiments"
	@echo "  list 			  - List all experiment directories"
	@echo "  generate-tables  - Generate tables for all experiments"
	@echo "  help             - Show this help message"
