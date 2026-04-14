# Content Marketing Suite - Justfile
# Install just: https://github.com/casey/just
# Usage: just <command>

# Default: show available commands
default:
    @just --list

# Install all dependencies (production + dev)
setup:
    @echo "[UV] Installing dependencies..."
    uv sync --all-extras
    @echo "[UV] Downloading spaCy English model..."
    uv run python -m spacy download en_core_web_sm
    @echo "[UV] Setup complete! Run: just run"

# Install production deps only
install:
    uv sync

# Run Streamlit dashboard
run:
    uv run streamlit run app.py

# Run CLI with a sample topic
demo:
    uv run content-suite --topic "Top 5 AI marketing trends 2025" --format blog --output demo_output.md

# Run all tests
test:
    uv run pytest tests/ -v

# Run tests with coverage
test-cov:
    uv run pytest tests/ -v --tb=short

# Lint and format check
lint:
    uv run ruff check .

# Auto-fix linting issues
fix:
    uv run ruff check . --fix
    uv run ruff format .

# Build distributable package
build:
    uv build

# Clean generated files and caches
clean:
    rm -rf dist/ build/ .pytest_cache/ __pycache__/
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    @echo "[UV] Clean complete"

# Show installed package versions
versions:
    uv run python -c "import streamlit, groq, spacy; print('streamlit:', streamlit.__version__); print('groq:', groq.__version__); print('spacy:', spacy.__version__)"

# Update all dependencies to latest compatible versions
update:
    uv lock --upgrade
    uv sync

# Generate sample outputs
samples:
    uv run content-suite --topic "AI marketing trends 2025" --format blog --output sample_outputs/blog_example.md
    uv run content-suite --topic "AI marketing trends 2025" --format twitter --output sample_outputs/twitter_example.txt
    uv run content-suite --topic "AI marketing trends 2025" --format linkedin --output sample_outputs/linkedin_example.txt
    @echo "[UV] Sample outputs generated in sample_outputs/"

# Open Cursor IDE
cursor:
    cursor .
