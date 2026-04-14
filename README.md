# 🚀 Automated Content Marketing Suite

> **AI-powered content creation** using **Groq + Google Gemini** (both free tier)  
> Built for **UV** package manager + **Cursor IDE** | CrewAI-style pipeline

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue)](https://python.org)
[![UV](https://img.shields.io/badge/package%20manager-UV-orange)](https://docs.astral.sh/uv/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-red)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## ⚡ Quick Start (3 Steps)

```bash
# 1. Install UV (one-time, takes ~2 seconds)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Clone and enter the project
git clone https://github.com/your-repo/content-marketing-suite
cd content-marketing-suite

# 3. Setup and run
uv sync                              # Installs all dependencies
uv run python -m spacy download en_core_web_sm  # Download NLP model
uv run streamlit run app.py          # Opens at http://localhost:8501
```

**Or use the CLI directly:**
```bash
uv run content-suite --topic "AI marketing trends 2025" --format all
```

---

## 🔑 API Keys (Both Free)

Copy `.env.example` to `.env` and add your keys:

```bash
cp .env.example .env
```

```env
# Get free key at: https://console.groq.com
GROQ_API_KEY=gsk_your_groq_key_here

# Get free key at: https://aistudio.google.com  
GEMINI_API_KEY=AIza_your_gemini_key_here
```

> Both keys have generous free tiers — no credit card required.

---

## 📋 Features

| Feature | Description | Tech |
|---------|-------------|------|
| **Blog Post Generation** | Markdown + HTML, 500-3000 words | Groq llama-3.3-70b |
| **Twitter/X Thread** | 8-tweet threads, <280 chars each | Groq |
| **LinkedIn Post** | Professional, 200-300 words | Groq |
| **Research Agent** | Topic research, trends, angles | Gemini 1.5 Flash |
| **SEO Analysis** | Keywords, readability, structure score | YAKE + spaCy |
| **Plagiarism Check** | Semantic + fuzzy similarity | sentence-transformers |
| **Engagement Prediction** | Rule-based score before publishing | TextBlob |
| **Content Calendar** | CSV + ICS export | pandas + ics |
| **Streamlit Dashboard** | 4-tab visual interface | Streamlit |
| **CLI Interface** | Headless operation via terminal | argparse |

---

## 🖥️ Streamlit Dashboard

```bash
uv run streamlit run app.py
```

**4 Tabs:**
1. **✍️ Generate** — Configure and run the full AI pipeline
2. **🔍 SEO Analysis** — Analyze any content for SEO score
3. **📅 Content Calendar** — Build and export CSV/ICS calendars
4. **⚙️ Settings** — Configure API keys and defaults

---

## 💻 CLI Reference

```bash
# Generate all formats
uv run content-suite --topic "AI trends 2025" --format all

# Blog post only, custom settings
uv run content-suite \
  --topic "Email marketing tips" \
  --format blog \
  --tone casual \
  --audience "small business owners" \
  --word-count 1500 \
  --output-dir ./my_content

# Twitter thread only
uv run content-suite --topic "SEO tips" --format twitter

# LinkedIn post (professional tone)
uv run content-suite --topic "B2B strategy" --format linkedin --tone professional

# SEO analysis of a file
uv run content-suite --analyze-seo ./blog_post.md --keyword "content marketing"

# Generate content calendar
uv run content-suite \
  --calendar "AI tools,SEO basics,LinkedIn growth,Email automation" \
  --frequency weekly \
  --output-dir ./calendar

# Skip plagiarism check (faster)
uv run content-suite --topic "AI trends" --format all --no-plagiarism

# JSON output (for piping)
uv run content-suite --topic "AI trends" --format blog --json > output.json
```

---

## 🏗️ Architecture

```
content-marketing-suite/
├── app.py                    # Streamlit dashboard (4 tabs)
├── cli.py                    # CLI entry point
├── agents/
│   ├── researcher.py         # Gemini: research & trends
│   ├── writer.py             # Groq: blog/twitter/linkedin
│   ├── seo_specialist.py     # spaCy + YAKE: SEO analysis
│   ├── social_media_formatter.py  # Groq: platform reformatting
│   └── tasks.py              # ContentPipeline orchestrator
├── utils/
│   ├── seo.py                # SEO utilities (keywords, meta tags)
│   ├── plagiarism.py         # Originality checker
│   ├── calendar_export.py    # CSV + ICS export
│   └── engagement.py         # Rule-based engagement predictor
└── tests/
    ├── test_seo.py
    ├── test_plagiarism.py
    └── test_engagement.py
```

### AI Pipeline Flow

```
Topic Input
    │
    ▼
[1] ResearcherAgent (Gemini)
    → Key facts, trends, content angles, recommended structure
    │
    ▼
[2] WriterAgent (Groq llama-3.3-70b)
    → Blog post (MD + HTML), Twitter thread, LinkedIn post
    │
    ▼
[3] SEOSpecialistAgent (YAKE + spaCy)
    → Keyword extraction, readability score, SEO recommendations
    │
    ▼
[4] SocialMediaFormatterAgent (Groq)
    → Instagram, Facebook, additional reformatting
    │
    ▼
[5] PlagiarismChecker (sentence-transformers + RapidFuzz)
    → Originality score, similar passages, cliche detection
    │
    ▼
[6] EngagementPredictor (Rule-based + TextBlob)
    → Engagement score per platform, recommendations
    │
    ▼
Results Dashboard / File Output
```

---

## 🧪 Testing

```bash
# Run all tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ --tb=short

# Run specific test file
uv run pytest tests/test_seo.py -v
uv run pytest tests/test_engagement.py -v
uv run pytest tests/test_plagiarism.py -v
```

---

## 📦 UV Commands Reference

```bash
uv sync                   # Install all production deps
uv sync --all-extras      # Install with dev deps (pytest, ruff)
uv run streamlit run app.py  # Run dashboard
uv run content-suite      # Run CLI
uv run pytest             # Run tests
uv run ruff check .       # Lint
uv build                  # Build distributable package
uv lock --upgrade         # Update all dependencies
```

---

## 🔧 Just Commands

If you have [just](https://github.com/casey/just) installed:

```bash
just setup     # Full install + spaCy model download
just run       # Launch Streamlit
just test      # Run test suite
just lint      # Ruff linting
just demo      # Generate sample output
just samples   # Generate all sample outputs
just clean     # Remove caches and build files
```

---

## 🌐 Optional Integrations

### WordPress Publishing
Set in `.env` or Settings tab:
```env
WORDPRESS_URL=https://yourblog.com
WORDPRESS_USERNAME=your_username
WORDPRESS_APP_PASSWORD=xxxx xxxx xxxx xxxx  # WordPress > Users > Application Passwords
```

### Buffer Social Scheduling
```env
BUFFER_ACCESS_TOKEN=your_buffer_token  # From buffer.com/developers
```

---

## 🚀 Deploying

### Build a distributable package
```bash
uv build
# Creates dist/content_marketing_suite-1.0.0-py3-none-any.whl
# Can be installed with: pip install dist/*.whl
```

### Deploy Streamlit to Streamlit Cloud
1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo, set `app.py` as entry point
4. Add API keys as Streamlit Secrets

---

## 📝 License

MIT — free to use, modify, and distribute.

---

*Built with ❤️ using UV + Cursor + Groq + Gemini | Invoice: "UV-powered AI content crew – 10x faster content. Fixed $800"*
