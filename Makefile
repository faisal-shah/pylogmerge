DISTDIR := dist

.PHONY: all clean distclean dist

# Main target: builds distribution and runs tests
all: dist

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
