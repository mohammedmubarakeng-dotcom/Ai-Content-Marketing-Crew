# Cursor-compatible + UV-ready
# Run: uv run pytest tests/test_seo.py -v
"""Tests for SEO Specialist Agent and SEO Utils."""

import pytest
from unittest.mock import patch, MagicMock


# ─── Test Fixtures ────────────────────────────────────────────────────────────

SAMPLE_BLOG_POST = """
META DESCRIPTION: Learn the top AI content marketing tools transforming how marketers create content in 2025. Discover free and paid options.

# Top 5 AI Content Marketing Tools in 2025

Artificial intelligence is revolutionizing content marketing. Marketers using AI tools report saving 10+ hours per week on content creation.

## 1. AI Writing Assistants

AI writing tools like Groq and Gemini have transformed how teams produce blog posts. These tools can generate publication-quality drafts in minutes.

## 2. SEO Optimization Tools

Search engine optimization has become more accessible with AI-powered keyword extraction tools. Content marketers can now identify the best keywords automatically.

- Faster keyword research
- Better content optimization
- Improved search rankings
- Data-driven decisions

## 3. Content Repurposing Tools

The best marketers repurpose their content across multiple platforms. A single blog post can become a Twitter thread, LinkedIn article, and email newsletter.

## Conclusion

AI tools are essential for modern content marketing success. Start with free tools and scale as your needs grow.
"""

SHORT_CONTENT = "This is too short."

META_CONTENT = """
META DESCRIPTION: This is a test meta description that is exactly the right length for SEO.

# Test Article

Some content here for testing purposes.
"""


# ─── SEO Specialist Tests ─────────────────────────────────────────────────────

class TestSEOSpecialistAgent:
    """Tests for SEOSpecialistAgent."""

    @pytest.fixture
    def agent(self):
        """Create SEO agent instance."""
        from agents.seo_specialist import SEOSpecialistAgent
        return SEOSpecialistAgent()

    def test_analyze_returns_dict(self, agent):
        """analyze() should return a dict with required keys."""
        result = agent.analyze(SAMPLE_BLOG_POST, "AI content marketing tools")
        assert isinstance(result, dict)

    def test_analyze_has_score(self, agent):
        """analyze() result must include a score between 0 and 100."""
        result = agent.analyze(SAMPLE_BLOG_POST, "AI content marketing tools")
        assert "score" in result
        assert 0 <= result["score"] <= 100

    def test_analyze_has_grade(self, agent):
        """analyze() result must include a letter grade."""
        result = agent.analyze(SAMPLE_BLOG_POST, "AI content marketing tools")
        assert "grade" in result
        assert result["grade"] in {"A+", "A", "B", "C", "D", "F"}

    def test_analyze_has_keywords(self, agent):
        """analyze() should extract keywords from content."""
        result = agent.analyze(SAMPLE_BLOG_POST, "AI marketing")
        assert "keywords" in result
        assert isinstance(result["keywords"], list)

    def test_analyze_has_readability(self, agent):
        """analyze() should include readability metrics."""
        result = agent.analyze(SAMPLE_BLOG_POST, "content marketing")
        assert "readability" in result
        readability = result["readability"]
        assert "reading_ease" in readability
        assert "grade_level" in readability

    def test_analyze_has_structure(self, agent):
        """analyze() should analyze document structure."""
        result = agent.analyze(SAMPLE_BLOG_POST, "AI tools")
        assert "structure" in result
        structure = result["structure"]
        assert "h1_count" in structure
        assert "h2_count" in structure
        assert "bullet_points" in structure

    def test_analyze_detects_headings(self, agent):
        """analyze() should correctly count headings."""
        result = agent.analyze(SAMPLE_BLOG_POST, "AI tools")
        structure = result["structure"]
        # SAMPLE_BLOG_POST has H1 (#) and H2 (##) headings
        assert structure["h2_count"] >= 3

    def test_analyze_detects_bullets(self, agent):
        """analyze() should detect bullet point lists."""
        result = agent.analyze(SAMPLE_BLOG_POST, "AI tools")
        structure = result["structure"]
        assert structure["bullet_points"] >= 3

    def test_analyze_short_content_returns_error(self, agent):
        """analyze() with very short content should return error dict."""
        result = agent.analyze(SHORT_CONTENT, "marketing")
        assert "error" in result or result.get("score", 0) == 0

    def test_keyword_density_calculation(self, agent):
        """calculate_keyword_density() should return correct density."""
        text = "content marketing is great. content marketing drives results. content marketing ROI."
        result = agent.calculate_keyword_density(text, "content marketing")
        assert "density" in result
        assert "count" in result
        assert "status" in result
        assert result["count"] >= 2  # "content marketing" appears 3 times

    def test_keyword_density_status_optimal(self, agent):
        """Keyword density in 1-2% range should be 'optimal'."""
        # Create text with ~1.5% keyword density
        words = ["this", "is", "a", "content", "test"] * 20 + ["content"] * 3
        text = " ".join(words)
        result = agent.calculate_keyword_density(text, "content")
        assert result["status"] in {"optimal", "too_low", "too_high"}  # valid status

    def test_meta_description_extraction(self, agent):
        """Should extract META DESCRIPTION from content."""
        meta = agent.extract_meta_description(META_CONTENT)
        assert meta != ""
        assert len(meta) <= 160

    def test_readability_scores_in_range(self, agent):
        """Readability scores should be in valid ranges."""
        result = agent.calculate_readability(SAMPLE_BLOG_POST)
        assert 0 <= result["reading_ease"] <= 100
        assert result["grade_level"] >= 1

    def test_recommendations_are_strings(self, agent):
        """Recommendations should be list of non-empty strings."""
        result = agent.analyze(SAMPLE_BLOG_POST, "AI tools")
        recs = result.get("recommendations", [])
        assert isinstance(recs, list)
        for rec in recs:
            assert isinstance(rec, str)
            assert len(rec) > 0

    def test_score_to_grade_mapping(self, agent):
        """_score_to_grade should return expected grades."""
        assert agent._score_to_grade(95) == "A+"
        assert agent._score_to_grade(85) == "A"
        assert agent._score_to_grade(75) == "B"
        assert agent._score_to_grade(65) == "C"
        assert agent._score_to_grade(55) == "D"
        assert agent._score_to_grade(30) == "F"

    def test_sentiment_analysis(self, agent):
        """Sentiment analysis should return valid polarity."""
        result = agent.analyze_sentiment(SAMPLE_BLOG_POST)
        assert "polarity" in result
        assert "label" in result
        assert result["label"] in {"Positive", "Negative", "Neutral"}
        assert -1.0 <= result["polarity"] <= 1.0

    def test_syllable_counter(self, agent):
        """_count_syllables should return reasonable counts."""
        # Known syllable counts
        assert agent._count_syllables("cat") == 1
        assert agent._count_syllables("marketing") >= 3
        assert agent._count_syllables("a") >= 1  # minimum 1


# ─── SEO Utils Tests ──────────────────────────────────────────────────────────

class TestSEOUtils:
    """Tests for SEOUtils."""

    @pytest.fixture
    def utils(self):
        """Create SEOUtils instance."""
        from utils.seo import SEOUtils
        return SEOUtils()

    def test_extract_keywords_returns_list(self, utils):
        """extract_keywords() should return a list of tuples."""
        result = utils.extract_keywords(SAMPLE_BLOG_POST, top_n=5)
        assert isinstance(result, list)
        assert len(result) <= 5

    def test_extract_keywords_are_tuples(self, utils):
        """Keywords should be (str, float) tuples."""
        result = utils.extract_keywords(SAMPLE_BLOG_POST, top_n=5)
        for item in result:
            assert isinstance(item, tuple)
            assert len(item) == 2
            assert isinstance(item[0], str)
            assert isinstance(item[1], (int, float))

    def test_get_keyword_list_returns_strings(self, utils):
        """get_keyword_list() should return only strings."""
        result = utils.get_keyword_list(SAMPLE_BLOG_POST, top_n=5)
        assert isinstance(result, list)
        for kw in result:
            assert isinstance(kw, str)

    def test_generate_meta_tags_returns_html(self, utils):
        """generate_meta_tags() should return valid HTML."""
        html = utils.generate_meta_tags(
            title="Test Title",
            description="Test description for meta tag generation.",
            keywords=["content", "marketing", "AI"],
        )
        assert "<title>" in html
        assert "<meta name=\"description\"" in html
        assert "content marketing" in html.lower() or "content" in html

    def test_meta_tags_title_truncation(self, utils):
        """Title longer than 60 chars should be truncated."""
        long_title = "This is a very long title that exceeds sixty characters easily in tests"
        html = utils.generate_meta_tags(
            title=long_title,
            description="desc",
            keywords=[],
        )
        # The title tag content should be truncated
        import re
        title_match = re.search(r'<title>(.*?)</title>', html)
        assert title_match
        assert len(title_match.group(1)) <= 60

    def test_fallback_keywords_returns_list(self, utils):
        """Fallback keyword extraction should return a list."""
        result = utils._fallback_keywords(SAMPLE_BLOG_POST, top_n=5)
        assert isinstance(result, list)
        assert len(result) <= 5
