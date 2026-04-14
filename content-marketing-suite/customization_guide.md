# 🛠️ Customization Guide
## Content Marketing Suite — Client Edition

This guide walks you through customizing every part of the suite using **Cursor IDE** with UV.

---

## 📋 Table of Contents

1. [Changing AI Models](#changing-ai-models)
2. [Adding New Content Formats](#adding-new-content-formats)
3. [Customizing Writing Prompts](#customizing-writing-prompts)
4. [Adding New Social Platforms](#adding-new-social-platforms)
5. [Custom SEO Rules](#custom-seo-rules)
6. [WordPress Auto-Publishing](#wordpress-auto-publishing)
7. [Adding a New Dashboard Tab](#adding-a-new-dashboard-tab)
8. [Extending the CLI](#extending-the-cli)
9. [Environment Variables Reference](#environment-variables-reference)
10. [Cursor AI Composer Tips](#cursor-ai-composer-tips)

---

## 1. Changing AI Models

### Switch Groq Model
File: `agents/writer.py` (line ~20)

```python
# Default: llama-3.3-70b-versatile (fast, high quality)
GROQ_MODEL = "llama-3.3-70b-versatile"

# Other free Groq models:
# "mixtral-8x7b-32768"       — longer context window
# "llama3-8b-8192"           — faster, smaller
# "gemma2-9b-it"             — Google's open model
```

### Switch Gemini Model  
File: `agents/researcher.py` (line ~18)

```python
# Default: gemini-1.5-flash (fast, free)
model: str = "gemini-1.5-flash"

# Other free Gemini models:
# "gemini-1.5-pro"           — higher quality, lower rate limits
# "gemini-1.0-pro"           — stable, widely used
```

---

## 2. Adding New Content Formats

### Step 1: Add generation method to WriterAgent

File: `agents/writer.py`

```python
def write_email_newsletter(
    self,
    research: dict,
    subject_line: str = "",
    max_retries: int = 3,
) -> str:
    """Write an email newsletter from research."""
    
    topic = research.get("topic", "")
    
    prompt = f"""Write a marketing email newsletter about: {topic}
    
    FORMAT:
    Subject line options: (3 options)
    
    Body:
    [Opening hook]
    [Main value/insight]
    [3 bullet points]
    [Call to action]
    [Sign-off]
    
    Target: 300-400 words, conversational but professional."""
    
    # ... API call (copy pattern from write_blog_post)
```

### Step 2: Add to the pipeline

File: `agents/tasks.py` — add in the `run()` method:

```python
if "email" in formats:
    self._progress("📧 Generating email newsletter...", 55)
    content_outputs["email"] = self.writer.write_email_newsletter(research)
```

### Step 3: Add CLI format option

File: `cli.py` — update the `--format` choices:

```python
parser.add_argument(
    "--format",
    choices=["blog", "twitter", "linkedin", "email", "all"],
    ...
)
```

### Step 4: Add to Streamlit UI

File: `app.py` — in the Generate tab, add a checkbox:

```python
gen_email = st.checkbox("Email Newsletter", value=False)
```

---

## 3. Customizing Writing Prompts

All AI prompts are in the agent files. Here's how to customize the blog writing prompt:

File: `agents/writer.py` → `write_blog_post()` method

```python
# Find the prompt variable and customize it:
prompt = f"""You are an expert content writer for [YOUR BRAND NAME].

BRAND VOICE: {tone}, always optimistic, data-driven, never use jargon
TARGET AUDIENCE: {audience} at [COMPANY TYPE/SIZE]
TOPIC: {topic}

YOUR SPECIFIC REQUIREMENTS:
1. Always mention [YOUR PRODUCT/SERVICE] naturally in the context
2. Include a case study or example in every post
3. End with a link to [YOUR LANDING PAGE] as the CTA
4. Use our brand keyword: "[YOUR BRAND KEYWORD]" at least twice
...
"""
```

**Pro tip in Cursor:** Use Cursor's Composer (Ctrl+K or Cmd+K) to ask:
> "Update the blog writing prompt in agents/writer.py to match [MY BRAND VOICE DESCRIPTION]"

---

## 4. Adding New Social Platforms

### Add TikTok Script Generation

File: `agents/social_media_formatter.py`

```python
def format_tiktok_script(
    self,
    content: str,
    research: dict,
    duration_seconds: int = 60,
) -> str:
    """Format content as a TikTok video script."""
    
    topic = research.get("topic", "")
    
    prompt = f"""Write a {duration_seconds}-second TikTok video script about {topic}.

    FORMAT:
    [0-5s HOOK]: Attention-grabbing opening line (pattern interrupt)
    [5-15s SETUP]: Problem or context
    [15-45s VALUE]: 3 key insights, one per visual transition
    [45-55s CTA]: What to do next
    [55-60s OUTRO]: "Follow for more..."
    
    Include:
    - Text overlays (in brackets)
    - Suggested trending sounds (as comment)
    - Transition cues"""
    
    # ... API call
```

Then add it to `format_all()`:
```python
def format_all(self, blog_content: str, research: dict) -> dict:
    return {
        ...
        "tiktok_script": self.format_tiktok_script(blog_content, research),
    }
```

---

## 5. Custom SEO Rules

### Add Custom Keyword Rules

File: `agents/seo_specialist.py` → `_generate_recommendations()` method

```python
# Add industry-specific rules:
def _generate_recommendations(self, ...):
    recs = []  # existing logic...
    
    # Custom rule: check for brand keywords
    brand_keywords = ["your-brand", "your-product", "your-service"]
    content_lower = content.lower()
    missing_brand_kw = [kw for kw in brand_keywords if kw not in content_lower]
    if missing_brand_kw:
        recs.append(f"🏷️ Add brand keywords: {', '.join(missing_brand_kw[:2])}")
    
    # Custom rule: check for call-to-action near bottom
    last_third = content[int(len(content)*0.66):]
    if "contact" not in last_third.lower() and "get started" not in last_third.lower():
        recs.append("📞 Add contact/booking CTA in the final section")
    
    return recs
```

### Adjust SEO Scoring Weights

File: `agents/seo_specialist.py` → `_calculate_seo_score()` method

```python
def _calculate_seo_score(self, ...):
    score = 0
    
    # Adjust these weights for your priorities:
    # READABILITY: 25 → 30 points if you prioritize accessible writing
    if readability["reading_ease"] >= 60:
        score += 30  # increased from 25
    
    # WORD COUNT: Adjust minimum for your content strategy
    if word_count >= 2000:  # Changed from 1200 (long-form focus)
        score += 20
```

---

## 6. WordPress Auto-Publishing

### Set up credentials

In `.env`:
```env
WORDPRESS_URL=https://yourblog.com
WORDPRESS_USERNAME=admin
WORDPRESS_APP_PASSWORD=xxxx xxxx xxxx xxxx
```

> Create App Password: WordPress Dashboard → Users → Edit Profile → Application Passwords

### Add to pipeline

File: `utils/` → Create `wordpress_publisher.py`:

```python
import requests
import base64

class WordPressPublisher:
    def __init__(self, url, username, app_password):
        self.url = url.rstrip("/")
        self.auth = base64.b64encode(
            f"{username}:{app_password}".encode()
        ).decode()
    
    def publish_post(
        self, 
        title: str, 
        content: str, 
        status: str = "draft",  # "draft" or "publish"
        categories: list = [],
        tags: list = [],
    ) -> dict:
        """Publish a post to WordPress."""
        response = requests.post(
            f"{self.url}/wp-json/wp/v2/posts",
            headers={
                "Authorization": f"Basic {self.auth}",
                "Content-Type": "application/json",
            },
            json={
                "title": title,
                "content": content,
                "status": status,
                "categories": categories,
                "tags": tags,
            },
        )
        response.raise_for_status()
        return response.json()
```

---

## 7. Adding a New Dashboard Tab

File: `app.py`

```python
# Find the tab definition (currently 4 tabs):
tab1, tab2, tab3, tab4 = st.tabs([
    "✍️ Generate", "🔍 SEO Analysis", "📅 Content Calendar", "⚙️ Settings"
])

# Change to 5 tabs:
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "✍️ Generate", "🔍 SEO Analysis", "📅 Content Calendar", 
    "📊 Analytics", "⚙️ Settings"
])

# Add your new tab content:
with tab5:  # Analytics tab (was tab4, now tab5)
    # ... settings content (move existing)

with tab4:  # New Analytics tab
    st.markdown("### 📊 Content Analytics")
    # Your analytics content here
```

---

## 8. Extending the CLI

### Add a new subcommand (e.g., `--publish`)

File: `cli.py`

```python
# In create_parser():
action_group.add_argument(
    "--publish",
    type=str,
    metavar="FILE",
    help="Publish a markdown file to WordPress",
)

# Add handler:
def cmd_publish(args):
    """Publish file to WordPress."""
    from utils.wordpress_publisher import WordPressPublisher
    
    publisher = WordPressPublisher(
        os.getenv("WORDPRESS_URL"),
        os.getenv("WORDPRESS_USERNAME"),
        os.getenv("WORDPRESS_APP_PASSWORD"),
    )
    
    content = Path(args.publish).read_text()
    # Extract title from first H1
    title = re.search(r'^# (.+)', content, re.MULTILINE)
    title = title.group(1) if title else "Untitled"
    
    result = publisher.publish_post(title, content, status="draft")
    print(f"[UV] ✅ Published as draft: {result.get('link')}")

# In main():
elif args.publish:
    cmd_publish(args)
```

---

## 9. Environment Variables Reference

| Variable | Required | Description | Where to get |
|----------|----------|-------------|--------------|
| `GROQ_API_KEY` | ✅ Yes | Groq LLM API | [console.groq.com](https://console.groq.com) |
| `GEMINI_API_KEY` | ✅ Yes | Google Gemini API | [aistudio.google.com](https://aistudio.google.com) |
| `WORDPRESS_URL` | ❌ Optional | Your WordPress site URL | Your site |
| `WORDPRESS_USERNAME` | ❌ Optional | WordPress username | Your site |
| `WORDPRESS_APP_PASSWORD` | ❌ Optional | WP Application Password | WP → Users → Profile |
| `BUFFER_ACCESS_TOKEN` | ❌ Optional | Buffer API token | [buffer.com/developers](https://buffer.com/developers) |
| `DEFAULT_TOPIC` | ❌ Optional | Pre-fill topic field | Any string |
| `DEFAULT_TONE` | ❌ Optional | Default writing tone | professional/casual/etc |
| `DEFAULT_LANGUAGE` | ❌ Optional | Content language | en/es/fr/etc |
| `MAX_BLOG_WORDS` | ❌ Optional | Max word count | Number |
| `ENABLE_PLAGIARISM_CHECK` | ❌ Optional | Enable by default | true/false |

---

## 10. Cursor AI Composer Tips

Cursor's AI Composer (Ctrl+K / Cmd+K) is your fastest way to customize this codebase.

### Useful Cursor prompts:

**Change brand voice:**
> "Update the blog post writing prompt in agents/writer.py to use a voice that's [DESCRIPTION]. Always include a reference to [YOUR PRODUCT] as a solution."

**Add new content type:**
> "Add a write_video_script() method to agents/writer.py following the same pattern as write_twitter_thread(). The script should be formatted for a 5-minute YouTube video."

**Custom SEO rules:**
> "In agents/seo_specialist.py, add a check that warns if the content doesn't mention any of these brand keywords: [LIST]. Add this to the recommendations."

**New Streamlit chart:**
> "In app.py, add a bar chart in the Generate tab using plotly that shows the engagement prediction breakdown by dimension from results['engagement']['blog']['breakdown']."

**WordPress integration:**
> "Add a 'Publish to WordPress' button in app.py that appears after content generation. Use the WordPressPublisher class from utils/wordpress_publisher.py."

---

## 🔄 Workflow for Custom Changes

1. Open project in Cursor: `cursor .`
2. Use Cursor Composer (Cmd+K) to describe the change
3. Review the AI-suggested changes
4. Run tests: `uv run pytest tests/ -v`
5. Test locally: `uv run streamlit run app.py`
6. Commit your changes

---

*Need help customizing? Review the `.cursorrules` file for AI behavior guidelines, or consult the inline docstrings throughout the codebase.*
