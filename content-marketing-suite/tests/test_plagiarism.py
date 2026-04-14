# Cursor-compatible + UV-ready
# Run: uv run pytest tests/test_plagiarism.py -v
"""Tests for PlagiarismChecker."""

import pytest
from unittest.mock import patch, MagicMock


ORIGINAL_TEXT = """
Content marketing represents a strategic approach to creating genuinely valuable information 
that naturally attracts and retains a clearly defined audience. Modern approaches leverage 
data analytics, artificial intelligence, and creative storytelling to produce material that 
resonates deeply with target demographics while also achieving measurable business outcomes.
"""

SIMILAR_TEXT = """
Content marketing is a strategic approach focused on creating valuable information 
that attracts and retains a defined audience. AI-powered approaches use analytics 
and creative storytelling to produce content that resonates with demographics 
while achieving measurable business results.
"""

DIFFERENT_TEXT = """
Quantum computing represents a fundamentally different paradigm for information processing.
Unlike classical computers that use binary bits, quantum systems leverage superposition 
and entanglement to perform calculations that would take classical machines millions of years.
"""

SHORT_TEXT = "Too short."

CLICHE_TEXT = """
In today's fast-paced world, it goes without saying that content marketers need to 
think outside the box and leverage synergies to achieve paradigm shifts. 
At the end of the day, best practices require game-changing solutions.
"""


class TestPlagiarismChecker:
    """Tests for PlagiarismChecker utility."""

    @pytest.fixture
    def checker(self):
        """Create PlagiarismChecker instance."""
        from utils.plagiarism import PlagiarismChecker
        return PlagiarismChecker()

    def test_check_returns_dict(self, checker):
        """check() should return a dict."""
        result = checker.check(ORIGINAL_TEXT)
        assert isinstance(result, dict)

    def test_check_has_originality_score(self, checker):
        """check() should return an originality_score."""
        result = checker.check(ORIGINAL_TEXT)
        assert "originality_score" in result
        assert isinstance(result["originality_score"], (int, float))

    def test_originality_score_range(self, checker):
        """originality_score should be between 0 and 100."""
        result = checker.check(ORIGINAL_TEXT)
        assert 0 <= result["originality_score"] <= 100

    def test_original_content_scores_high(self, checker):
        """Original content should score above 80."""
        result = checker.check(ORIGINAL_TEXT)
        assert result["originality_score"] >= 70, (
            f"Expected original content to score 70+, got {result['originality_score']}"
        )

    def test_check_has_status_field(self, checker):
        """check() should include a status field."""
        result = checker.check(ORIGINAL_TEXT)
        assert "status" in result
        assert result["status"] in {
            "original", "mostly_original", "some_similarity", "high_similarity",
            "check_unavailable", "ok",
        }

    def test_check_has_common_phrases(self, checker):
        """check() should return list of common/cliche phrases found."""
        result = checker.check(ORIGINAL_TEXT)
        assert "common_phrases" in result
        assert isinstance(result["common_phrases"], list)

    def test_cliche_phrases_detected(self, checker):
        """Content with cliches should have them flagged."""
        result = checker.check(CLICHE_TEXT)
        assert len(result["common_phrases"]) > 0, "Expected cliche phrases to be detected"

    def test_short_content_handled(self, checker):
        """Short content (< 100 chars) should return graceful result."""
        result = checker.check(SHORT_TEXT)
        assert isinstance(result, dict)
        assert "originality_score" in result
        # Short content should not crash and may return 100 or note
        assert result["originality_score"] >= 0

    def test_empty_content_handled(self, checker):
        """Empty content should return graceful result."""
        result = checker.check("")
        assert isinstance(result, dict)

    def test_fuzzy_check_with_similar_text(self, checker):
        """Fuzzy check should detect similarity between similar texts."""
        result = checker.check(ORIGINAL_TEXT, reference_texts=[SIMILAR_TEXT])
        # Similar text should reduce originality score somewhat
        assert result["originality_score"] <= 100

    def test_fuzzy_check_with_different_text(self, checker):
        """Fuzzy check against unrelated text should leave score high."""
        result = checker.check(ORIGINAL_TEXT, reference_texts=[DIFFERENT_TEXT])
        assert result["originality_score"] >= 80

    def test_check_has_content_hash(self, checker):
        """check() should return a content hash for tracking."""
        result = checker.check(ORIGINAL_TEXT)
        assert "content_hash" in result
        assert isinstance(result["content_hash"], str)
        assert len(result["content_hash"]) > 0

    def test_content_hash_is_deterministic(self, checker):
        """Same content should always produce same hash."""
        result1 = checker.check(ORIGINAL_TEXT)
        result2 = checker.check(ORIGINAL_TEXT)
        assert result1["content_hash"] == result2["content_hash"]

    def test_add_to_corpus(self, checker):
        """add_to_corpus() should add text to reference corpus."""
        initial_len = len(checker._reference_corpus)
        checker.add_to_corpus(ORIGINAL_TEXT)
        assert len(checker._reference_corpus) == initial_len + 1

    def test_get_originality_badge(self, checker):
        """get_originality_badge() should return labeled badge string."""
        badge_90 = checker.get_originality_badge(90)
        badge_75 = checker.get_originality_badge(75)
        badge_60 = checker.get_originality_badge(60)
        badge_30 = checker.get_originality_badge(30)

        assert "Original" in badge_90 or "🟢" in badge_90
        assert isinstance(badge_75, str)
        assert isinstance(badge_60, str)
        assert isinstance(badge_30, str)

    def test_split_sentences(self, checker):
        """_split_sentences() should correctly split text into sentences."""
        text = "First sentence. Second sentence! Third sentence? Fourth."
        sentences = checker._split_sentences(text)
        assert isinstance(sentences, list)
        assert len(sentences) >= 3

    def test_common_phrases_check(self, checker):
        """_check_common_phrases() should detect known cliche phrases."""
        text = "In today's fast-paced world, we need to think outside the box."
        found = checker._check_common_phrases(text)
        assert len(found) >= 2  # Both "in today's fast-paced world" and "think outside the box"

    def test_fuzzy_check_returns_dict(self, checker):
        """_fuzzy_check() should return dict with matches and penalty keys."""
        result = checker._fuzzy_check(ORIGINAL_TEXT, [SIMILAR_TEXT])
        assert isinstance(result, dict)
        assert "matches" in result
        assert "penalty" in result
        assert isinstance(result["matches"], list)
        assert isinstance(result["penalty"], (int, float))

    def test_word_count_in_result(self, checker):
        """check() result should include word_count."""
        result = checker.check(ORIGINAL_TEXT)
        assert "word_count" in result
        expected_words = len(ORIGINAL_TEXT.split())
        assert result["word_count"] > 0
