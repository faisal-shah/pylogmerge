DISTDIR := dist
DOCBUILD := build
VENV_DIR := $(DOCBUILD)/.venv
VENV_ACTIVATE := $(VENV_DIR)/bin/activate

.PHONY: all clean distclean dist

# Main target: builds distribution and runs tests
all: dist

# Virtual environment setup
# This target creates the virtual environment and installs dependencies.
# It runs if the activate script doesn't exist or if pyproject.toml has changed.
$(VENV_ACTIVATE): pyproject.toml
	@echo "Setting up virtual environment in $(VENV_DIR)..."
	python3 -m venv $(VENV_DIR)
	. $(VENV_ACTIVATE) && pip install -e .[dev]
	@echo "Virtual environment setup complete."

# Distribution package
dist:
	@echo "Building distribution package..."
	@python3 -m build
	@echo "Distribution package built."

# Cleaning targets
# clean: Cleans both distribution and documentation/build artifacts.
clean: distclean
	@echo "Workspace cleaned (distribution and build artifacts, including venv)."

# distclean: Cleans only the distribution directory.
distclean:
	@echo "Cleaning distribution directory..."
	rm -rf $(DISTDIR)
	@echo "Distribution directory cleaned."
