# Cursor-compatible + UV-ready
# Run: uv run pytest tests/test_engagement.py -v
"""Tests for EngagementPredictor."""

import pytest


HIGH_ENGAGEMENT_LINKEDIN = """
Most content marketers are wasting 80% of their time.

Here's the proven framework that's transforming results right now:

• AI tools produce 3x more content in 50% less time — discover this game-changer
• SEO-optimized posts get 40% better organic traffic
• Repurposing content saves 6 hours every week
• Data-driven decisions are essential for sustainable growth

The marketers winning today aren't working harder. They're working smarter.

Start implementing these strategies and watch your numbers transform.

What's your biggest content marketing challenge? Share below! 👇

#ContentMarketing #Marketing #DigitalMarketing #B2B #Strategy
"""

LOW_ENGAGEMENT_BLOG = "Content is good. Marketing helps businesses."

GOOD_TWITTER_THREAD = """
[1/5] 🧵 The secret to viral content marketing nobody talks about:

[2/5] 📊 73% of marketers use AI tools in 2024 — but only 12% use them effectively.
Here's the difference:

[3/5] 💡 Effective AI users start with research, not writing.
They use AI to find patterns in top-performing content first.

[4/5] 🎯 Then they create content that matches those patterns — but with their unique insight.
This beats pure AI generation every time.

[5/5] ✅ Your action step: Analyze your top 3 competitor posts before writing anything.
Follow for more growth tactics! #ContentMarketing #Marketing #GrowthHacking
"""

BLOG_WITH_STATS = """
# The Complete Guide to AI Content Marketing

META DESCRIPTION: Discover proven AI content marketing strategies that 10x your output.

Content marketing drives 3x more leads than paid search. Yet 91% of B2B companies 
report struggling with consistent content creation.

## Why AI Changes Everything

Research shows that teams using AI writing tools produce 5x more content at 60% 
lower cost. The ROI is undeniable.

- 73% faster first draft generation
- 40% improvement in SEO scores
- 85% reduction in editing time

## Getting Started Today

The best time to start with AI content tools was 6 months ago. The second best time is now.

Implement these 5 strategies and you will see results within 30 days.

Ready to transform your content marketing? Let's get started!
"""


class TestEngagementPredictor:
    """Tests for EngagementPredictor."""

    @pytest.fixture
    def predictor(self):
        """Create EngagementPredictor instance."""
        from utils.engagement import EngagementPredictor
        return EngagementPredictor()

    def test_predict_returns_dict(self, predictor):
        """predict() should return a dict."""
        result = predictor.predict(HIGH_ENGAGEMENT_LINKEDIN, "linkedin")
        assert isinstance(result, dict)

    def test_predict_has_overall_score(self, predictor):
        """predict() should return an overall_score."""
        result = predictor.predict(HIGH_ENGAGEMENT_LINKEDIN, "linkedin")
        assert "overall_score" in result
        assert isinstance(result["overall_score"], (int, float))

    def test_score_in_valid_range(self, predictor):
        """overall_score should be between 0 and 100."""
        result = predictor.predict(HIGH_ENGAGEMENT_LINKEDIN, "linkedin")
        assert 0 <= result["overall_score"] <= 100

    def test_predict_has_grade(self, predictor):
        """predict() should return a letter grade."""
        result = predictor.predict(HIGH_ENGAGEMENT_LINKEDIN, "linkedin")
        assert "grade" in result
        assert result["grade"] in {"A", "B", "C", "D", "F"}

    def test_predict_has_breakdown(self, predictor):
        """predict() should return breakdown of scoring dimensions."""
        result = predictor.predict(HIGH_ENGAGEMENT_LINKEDIN, "linkedin")
        assert "breakdown" in result
        assert isinstance(result["breakdown"], dict)
        assert len(result["breakdown"]) > 0

    def test_predict_has_recommendations(self, predictor):
        """predict() should return list of recommendations."""
        result = predictor.predict(LOW_ENGAGEMENT_BLOG, "blog")
        assert "recommendations" in result
        assert isinstance(result["recommendations"], list)

    def test_predict_has_platform_field(self, predictor):
        """predict() should return the platform name."""
        result = predictor.predict(HIGH_ENGAGEMENT_LINKEDIN, "linkedin")
        assert "platform" in result

    def test_high_engagement_content_scores_higher(self, predictor):
        """Content with engagement signals should score higher than minimal content."""
        high_result = predictor.predict(HIGH_ENGAGEMENT_LINKEDIN, "linkedin")
        low_result = predictor.predict(LOW_ENGAGEMENT_BLOG, "blog")
        assert high_result["overall_score"] > low_result["overall_score"]

    def test_question_detection(self, predictor):
        """Questions in content should improve engagement score."""
        content_with_question = HIGH_ENGAGEMENT_LINKEDIN  # has "What's your biggest..."
        content_no_question = "This is content without any questions. Just statements."

        result_with = predictor.predict(content_with_question, "linkedin")
        result_without = predictor.predict(content_no_question, "linkedin")

        # Question dimension should score higher with questions
        q_score_with = result_with["breakdown"].get("questions", {}).get("score", 0)
        q_score_without = result_without["breakdown"].get("questions", {}).get("score", 0)
        assert q_score_with >= q_score_without

    def test_power_words_scoring(self, predictor):
        """Content with power words should score higher on that dimension."""
        result = predictor.predict(HIGH_ENGAGEMENT_LINKEDIN, "linkedin")
        power_score = result["breakdown"].get("power_words", {}).get("score", 0)
        max_score = result["breakdown"].get("power_words", {}).get("max", 15)
        assert power_score > 0
        assert power_score <= max_score

    def test_hashtag_scoring_linkedin(self, predictor):
        """LinkedIn post with 3-5 hashtags should score well."""
        result = predictor.predict(HIGH_ENGAGEMENT_LINKEDIN, "linkedin")
        hashtag_score = result["breakdown"].get("hashtags", {}).get("score", 0)
        assert hashtag_score > 0

    def test_hashtag_scoring_blog(self, predictor):
        """Blog posts shouldn't be penalized for no hashtags."""
        result = predictor.predict(BLOG_WITH_STATS, "blog")
        hashtag_data = result["breakdown"].get("hashtags", {})
        # Blog hashtag scoring should not heavily penalize zero hashtags
        assert hashtag_data.get("score", 0) >= 3

    def test_length_scoring_optimal_range(self, predictor):
        """Content within optimal length range should get high length score."""
        result = predictor.predict(BLOG_WITH_STATS, "blog")
        length_data = result["breakdown"].get("length", {})
        # Blog with 100+ words should score reasonably
        assert length_data.get("score", 0) > 0

    def test_stats_improve_structure_score(self, predictor):
        """Content with numbers/statistics should score higher on structure."""
        result_with_stats = predictor.predict(BLOG_WITH_STATS, "blog")
        result_no_stats = predictor.predict("Content is good. Marketing works. Trust us.", "blog")

        struct_with = result_with_stats["breakdown"].get("structure", {}).get("score", 0)
        struct_without = result_no_stats["breakdown"].get("structure", {}).get("score", 0)
        assert struct_with >= struct_without

    def test_cta_detection(self, predictor):
        """Content with clear CTA should score higher on that dimension."""
        result = predictor.predict(HIGH_ENGAGEMENT_LINKEDIN, "linkedin")
        cta_score = result["breakdown"].get("call_to_action", {}).get("score", 0)
        assert cta_score > 0

    def test_predict_multi_returns_dict(self, predictor):
        """predict_multi() should return scores for each platform."""
        content_dict = {
            "blog": BLOG_WITH_STATS,
            "linkedin": HIGH_ENGAGEMENT_LINKEDIN,
            "twitter": GOOD_TWITTER_THREAD,
        }
        results = predictor.predict_multi(content_dict)
        assert isinstance(results, dict)
        assert "blog" in results
        assert "linkedin" in results
        assert "twitter" in results

    def test_predict_multi_all_have_scores(self, predictor):
        """All platform results should have overall_score."""
        content_dict = {
            "blog": BLOG_WITH_STATS,
            "linkedin": HIGH_ENGAGEMENT_LINKEDIN,
        }
        results = predictor.predict_multi(content_dict)
        for platform, result in results.items():
            assert "overall_score" in result, f"{platform} missing overall_score"

    def test_short_content_returns_zero(self, predictor):
        """Very short content should return score of 0 or near zero."""
        result = predictor.predict("Hi.", "blog")
        assert result["overall_score"] == 0

    def test_empty_content_handled(self, predictor):
        """Empty content should not raise an exception."""
        result = predictor.predict("", "blog")
        assert isinstance(result, dict)
        assert result["overall_score"] == 0

    def test_score_to_grade_a(self, predictor):
        """Score 85+ should return grade A."""
        assert predictor._score_to_grade(90) == "A"
        assert predictor._score_to_grade(85) == "A"

    def test_score_to_grade_b(self, predictor):
        """Score 70-84 should return grade B."""
        assert predictor._score_to_grade(75) == "B"
        assert predictor._score_to_grade(70) == "B"

    def test_score_to_grade_f(self, predictor):
        """Score below 40 should return grade F."""
        assert predictor._score_to_grade(30) == "F"
        assert predictor._score_to_grade(0) == "F"

    def test_performance_labels(self, predictor):
        """_performance_label() should return string labels."""
        labels = [
            predictor._performance_label(90),
            predictor._performance_label(75),
            predictor._performance_label(60),
            predictor._performance_label(45),
            predictor._performance_label(20),
        ]
        for label in labels:
            assert isinstance(label, str)
            assert len(label) > 0

    def test_word_count_in_result(self, predictor):
        """predict() should include word_count in result."""
        result = predictor.predict(HIGH_ENGAGEMENT_LINKEDIN, "linkedin")
        assert "word_count" in result
        assert result["word_count"] > 0

    def test_char_count_in_result(self, predictor):
        """predict() should include char_count in result."""
        result = predictor.predict(HIGH_ENGAGEMENT_LINKEDIN, "linkedin")
        assert "char_count" in result
        assert result["char_count"] > 0

    def test_platform_normalization(self, predictor):
        """Platform names should be normalized (Twitter/X -> twitter)."""
        result1 = predictor.predict(GOOD_TWITTER_THREAD, "twitter")
        result2 = predictor.predict(GOOD_TWITTER_THREAD, "Twitter")
        # Both should return valid results
        assert result1["overall_score"] >= 0
        assert result2["overall_score"] >= 0

    def test_recommendations_are_strings(self, predictor):
        """All recommendations should be non-empty strings."""
        result = predictor.predict(LOW_ENGAGEMENT_BLOG, "blog")
        for rec in result["recommendations"]:
            assert isinstance(rec, str)
            assert len(rec) > 0

    def test_breakdown_scores_sum_to_total(self, predictor):
        """Sum of breakdown scores should approximately equal overall score."""
        result = predictor.predict(HIGH_ENGAGEMENT_LINKEDIN, "linkedin")
        breakdown = result["breakdown"]

        total_score = sum(d.get("score", 0) for d in breakdown.values())
        total_max = sum(d.get("max", 0) for d in breakdown.values())

        if total_max > 0:
            calculated = round((total_score / total_max) * 100)
            # Allow small rounding differences
            assert abs(calculated - result["overall_score"]) <= 2
