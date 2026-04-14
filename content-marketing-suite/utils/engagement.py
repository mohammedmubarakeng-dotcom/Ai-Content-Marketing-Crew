# Cursor-compatible + UV-ready
# Run: uv run python utils/engagement.py
"""
Engagement Predictor - Rule-based engagement scoring.
Uses sentiment analysis + content signals (no AI API required).
"""

import re
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class EngagementPredictor:
    """
    Predicts content engagement using rule-based scoring.
    
    Factors analyzed:
    - Sentiment (positive content generally performs better)
    - Question presence (drives comments/replies)
    - Content length (platform-specific optimal ranges)
    - Power words (emotional triggers)
    - Call-to-action presence
    - Readability
    - Emoji usage (platform-dependent)
    - Hashtag count (for social platforms)
    - Numbered lists / stats (increase credibility)
    """

    # Power words that increase engagement
    POWER_WORDS = {
        "urgency": ["now", "today", "immediately", "limited", "urgent", "last chance", "deadline", "expires"],
        "curiosity": ["secret", "revealed", "surprising", "unexpected", "hidden", "truth", "discover", "finally"],
        "value": ["free", "proven", "guaranteed", "best", "ultimate", "complete", "essential", "powerful"],
        "social": ["you", "your", "we", "together", "community", "everyone", "people"],
        "action": ["learn", "get", "start", "build", "create", "achieve", "transform", "master"],
        "emotion": ["amazing", "incredible", "shocking", "inspiring", "breakthrough", "life-changing"],
    }

    # Platform-specific optimal content lengths (in words)
    OPTIMAL_LENGTH = {
        "blog": (1000, 2000),
        "twitter": (15, 40),  # per tweet
        "linkedin": (150, 300),
        "instagram": (100, 200),
        "facebook": (100, 200),
        "email": (200, 500),
    }

    # Optimal hashtag counts per platform
    OPTIMAL_HASHTAGS = {
        "twitter": (1, 3),
        "linkedin": (3, 5),
        "instagram": (15, 25),
        "facebook": (1, 3),
        "blog": (0, 0),
    }

    def predict(self, content: str, platform: str = "blog") -> dict:
        """
        Predict engagement score for content.

        Args:
            content: The content to analyze
            platform: Target platform ('blog', 'twitter', 'linkedin', etc.)

        Returns:
            dict with overall_score, grade, breakdown, and recommendations
        """
        if not content or len(content.strip()) < 20:
            return {
                "overall_score": 0,
                "grade": "F",
                "breakdown": {},
                "recommendations": ["Content too short to analyze"],
                "platform": platform,
            }

        platform = platform.lower().replace("/", "_").replace("x", "twitter")

        breakdown = {}

        # 1. Sentiment Analysis (20 points)
        sentiment_score = self._score_sentiment(content)
        breakdown["sentiment"] = sentiment_score

        # 2. Question presence (15 points)
        question_score = self._score_questions(content, platform)
        breakdown["questions"] = question_score

        # 3. Content length (20 points)
        length_score = self._score_length(content, platform)
        breakdown["length"] = length_score

        # 4. Power words (15 points)
        power_score = self._score_power_words(content)
        breakdown["power_words"] = power_score

        # 5. Call to action (10 points)
        cta_score = self._score_cta(content)
        breakdown["call_to_action"] = cta_score

        # 6. Structure signals (10 points)
        structure_score = self._score_structure(content, platform)
        breakdown["structure"] = structure_score

        # 7. Hashtags (5 points)
        hashtag_score = self._score_hashtags(content, platform)
        breakdown["hashtags"] = hashtag_score

        # 8. Emoji usage (5 points)
        emoji_score = self._score_emojis(content, platform)
        breakdown["emojis"] = emoji_score

        # Calculate total
        total = sum(s["score"] for s in breakdown.values())
        max_total = sum(s["max"] for s in breakdown.values())
        overall = round((total / max_total) * 100) if max_total > 0 else 0

        recommendations = self._generate_recommendations(breakdown, platform, content)

        return {
            "overall_score": overall,
            "grade": self._score_to_grade(overall),
            "predicted_performance": self._performance_label(overall),
            "breakdown": breakdown,
            "recommendations": recommendations[:5],
            "platform": platform,
            "word_count": len(content.split()),
            "char_count": len(content),
        }

    def predict_multi(self, content_dict: dict) -> dict:
        """
        Predict engagement for content across multiple platforms.

        Args:
            content_dict: Dict mapping platform -> content string

        Returns:
            Dict mapping platform -> prediction results
        """
        results = {}
        for platform, content in content_dict.items():
            if content:
                results[platform] = self.predict(content, platform)
        return results

    def _score_sentiment(self, content: str) -> dict:
        """Score based on sentiment — positive content performs better."""
        try:
            from textblob import TextBlob
            blob = TextBlob(content[:3000])
            polarity = blob.sentiment.polarity
            
            # Ideal: slightly positive (0.1 - 0.5)
            if 0.1 <= polarity <= 0.5:
                score = 20
                label = "Optimal positive tone"
            elif polarity > 0.5:
                score = 15
                label = "Very positive (may seem promotional)"
            elif -0.1 <= polarity < 0.1:
                score = 12
                label = "Neutral tone"
            else:
                score = 5
                label = "Negative tone detected"
            
            return {"score": score, "max": 20, "value": round(polarity, 3), "label": label}
        
        except ImportError:
            return {"score": 12, "max": 20, "value": 0, "label": "Neutral (TextBlob unavailable)"}

    def _score_questions(self, content: str, platform: str) -> dict:
        """Score question usage — drives engagement/comments."""
        questions = len(re.findall(r'\?', content))
        
        if platform in ("linkedin", "facebook"):
            # 1-2 questions is ideal for comments
            if questions == 1:
                score = 15
                label = f"{questions} question (optimal for {platform})"
            elif questions == 2:
                score = 12
                label = f"{questions} questions (good)"
            elif questions >= 3:
                score = 8
                label = f"{questions} questions (may dilute focus)"
            else:
                score = 3
                label = "No questions (add one to drive comments)"
        elif platform == "twitter":
            if questions >= 1:
                score = 15
                label = f"{questions} question(s) — boosts replies"
            else:
                score = 8
                label = "No question — consider adding one"
        else:
            if questions >= 1:
                score = 12
                label = f"{questions} question(s)"
            else:
                score = 6
                label = "No questions"
        
        return {"score": score, "max": 15, "value": questions, "label": label}

    def _score_length(self, content: str, platform: str) -> dict:
        """Score content length against platform optimums."""
        word_count = len(content.split())
        optimal = self.OPTIMAL_LENGTH.get(platform, (100, 500))
        
        if optimal[0] <= word_count <= optimal[1]:
            score = 20
            label = f"{word_count} words — optimal range ({optimal[0]}-{optimal[1]})"
        elif word_count < optimal[0]:
            deficit = optimal[0] - word_count
            score = max(5, 20 - int(deficit / optimal[0] * 20))
            label = f"{word_count} words — too short (need {deficit} more)"
        else:
            excess = word_count - optimal[1]
            score = max(8, 20 - int(excess / optimal[1] * 10))
            label = f"{word_count} words — slightly long (optimal: {optimal[1]})"
        
        return {"score": score, "max": 20, "value": word_count, "label": label}

    def _score_power_words(self, content: str) -> dict:
        """Score presence of engagement-driving power words."""
        content_lower = content.lower()
        found_categories = set()
        found_words = []
        
        for category, words in self.POWER_WORDS.items():
            for word in words:
                if word in content_lower:
                    found_categories.add(category)
                    found_words.append(word)
        
        unique_categories = len(found_categories)
        
        if unique_categories >= 4:
            score = 15
            label = f"Strong ({unique_categories} categories of power words)"
        elif unique_categories >= 2:
            score = 10
            label = f"Good ({unique_categories} power word categories)"
        elif unique_categories == 1:
            score = 5
            label = "Limited power words"
        else:
            score = 2
            label = "No power words detected"
        
        return {
            "score": score,
            "max": 15,
            "value": len(set(found_words)),
            "label": label,
            "categories_found": list(found_categories),
        }

    def _score_cta(self, content: str) -> dict:
        """Score call-to-action presence."""
        cta_patterns = [
            r'\bfollow\b', r'\bsubscribe\b', r'\bshare\b', r'\bcomment\b',
            r'\bclick\b', r'\blearn more\b', r'\bget started\b', r'\bdownload\b',
            r'\bsign up\b', r'\bjoin\b', r'\bbook\b', r'\bcontact\b', r'\btry\b',
            r'\bstart\b', r'\bdiscover\b', r'\bexplore\b', r'\bread more\b',
            r'\bretweet\b', r'\brt\b', r'\btag\b', r'\blike\b',
        ]
        
        content_lower = content.lower()
        found_ctas = [p.strip(r'\b') for p in cta_patterns if re.search(p, content_lower)]
        
        if len(found_ctas) >= 2:
            score = 10
            label = f"Strong CTA ({len(found_ctas)} action words)"
        elif len(found_ctas) == 1:
            score = 7
            label = f"CTA present: {found_ctas[0]}"
        else:
            score = 0
            label = "No clear CTA — add one!"
        
        return {"score": score, "max": 10, "value": len(found_ctas), "label": label}

    def _score_structure(self, content: str, platform: str) -> dict:
        """Score content structure and formatting."""
        score = 0
        signals = []
        
        # Numbers/stats (credibility)
        number_count = len(re.findall(r'\b\d+(?:\.\d+)?(?:%|x|X)?\b', content))
        if number_count >= 3:
            score += 4
            signals.append(f"{number_count} numbers/stats")
        elif number_count >= 1:
            score += 2
        
        # Lists or line breaks (scannability)
        has_bullets = bool(re.search(r'^[-•*]\s', content, re.MULTILINE))
        has_numbers = bool(re.search(r'^\d+\.', content, re.MULTILINE))
        if has_bullets or has_numbers:
            score += 3
            signals.append("structured lists")
        
        # Bold/emphasis (for blog/LinkedIn)
        if platform in ("blog", "linkedin"):
            bold_count = len(re.findall(r'\*\*[^*]+\*\*', content))
            if bold_count >= 2:
                score += 3
                signals.append("emphasis formatting")
        
        if not signals:
            signals.append("minimal structure")
        
        return {
            "score": min(score, 10),
            "max": 10,
            "value": number_count,
            "label": ", ".join(signals) if signals else "basic structure",
        }

    def _score_hashtags(self, content: str, platform: str) -> dict:
        """Score hashtag usage for social platforms."""
        hashtags = re.findall(r'#\w+', content)
        count = len(hashtags)
        optimal = self.OPTIMAL_HASHTAGS.get(platform, (0, 5))
        
        if optimal == (0, 0):
            return {"score": 5, "max": 5, "value": count, "label": "N/A for blog"}
        
        if optimal[0] <= count <= optimal[1]:
            score = 5
            label = f"{count} hashtags (optimal: {optimal[0]}-{optimal[1]})"
        elif count < optimal[0]:
            score = 2
            label = f"{count} hashtags (need {optimal[0]-count} more)"
        else:
            score = 1
            label = f"{count} hashtags (too many — max {optimal[1]})"
        
        return {"score": score, "max": 5, "value": count, "label": label}

    def _score_emojis(self, content: str, platform: str) -> dict:
        """Score emoji usage (platform-appropriate)."""
        # Simple emoji detection via unicode ranges
        emoji_pattern = re.compile(
            "[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF"
            "\U00002702-\U000027B0\U000024C2-\U0001F251]+",
            flags=re.UNICODE,
        )
        emoji_count = len(emoji_pattern.findall(content))
        
        if platform == "blog":
            # Minimal emojis for blog
            score = 5 if emoji_count == 0 else (3 if emoji_count <= 3 else 1)
            label = f"{emoji_count} emojis (minimal is fine for blogs)"
        elif platform in ("twitter", "linkedin"):
            if 3 <= emoji_count <= 8:
                score = 5
                label = f"{emoji_count} emojis (optimal)"
            elif emoji_count < 3:
                score = 3
                label = f"{emoji_count} emojis (add a few for engagement)"
            else:
                score = 2
                label = f"{emoji_count} emojis (too many — may look spammy)"
        elif platform == "instagram":
            if emoji_count >= 5:
                score = 5
                label = f"{emoji_count} emojis (great for Instagram)"
            else:
                score = 2
                label = f"{emoji_count} emojis (Instagram loves more emojis)"
        else:
            score = 3 if emoji_count > 0 else 4
            label = f"{emoji_count} emojis"
        
        return {"score": score, "max": 5, "value": emoji_count, "label": label}

    def _generate_recommendations(self, breakdown: dict, platform: str, content: str) -> list:
        """Generate actionable improvement recommendations."""
        recs = []
        
        # Check each dimension for improvements
        for dimension, data in breakdown.items():
            score = data.get("score", 0)
            max_score = data.get("max", 10)
            
            if score < max_score * 0.5:
                if dimension == "questions":
                    recs.append("❓ Add a question at the end to drive comments/replies")
                elif dimension == "call_to_action":
                    recs.append("📢 Add a clear CTA (e.g., 'Share this with your team')")
                elif dimension == "power_words":
                    recs.append("💥 Add power words: 'proven', 'essential', 'discover', 'you'")
                elif dimension == "hashtags":
                    optimal = self.OPTIMAL_HASHTAGS.get(platform, (2, 5))
                    recs.append(f"#️⃣ Add {optimal[0]}-{optimal[1]} relevant hashtags")
                elif dimension == "emojis" and platform != "blog":
                    recs.append("😊 Add 3-5 emojis to increase visual appeal")
                elif dimension == "structure":
                    recs.append("📋 Add numbers/statistics to boost credibility")
                elif dimension == "length":
                    optimal = self.OPTIMAL_LENGTH.get(platform, (100, 500))
                    word_count = len(content.split())
                    if word_count < optimal[0]:
                        recs.append(f"📏 Expand content to {optimal[0]}+ words (currently {word_count})")
        
        if not recs:
            recs.append("✅ Content is well-optimized for engagement!")
        
        return recs

    def _score_to_grade(self, score: int) -> str:
        """Convert score to letter grade."""
        if score >= 85:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 55:
            return "C"
        elif score >= 40:
            return "D"
        else:
            return "F"

    def _performance_label(self, score: int) -> str:
        """Human-readable performance prediction."""
        if score >= 85:
            return "🚀 High Performance Expected"
        elif score >= 70:
            return "📈 Good Performance Expected"
        elif score >= 55:
            return "📊 Average Performance Expected"
        elif score >= 40:
            return "📉 Below Average — Optimize Before Publishing"
        else:
            return "⚠️ Needs Significant Improvement"


if __name__ == "__main__":
    predictor = EngagementPredictor()

    linkedin_post = """
    Most content marketers are wasting 80% of their effort.

    Here's what actually drives results in 2025:

    • AI tools are 3x faster than manual writing
    • SEO-optimized posts get 40% more organic traffic  
    • Repurposing one blog post into 5 formats saves 6 hours/week
    • Consistency beats viral posts every single time

    The marketers winning right now aren't working harder — they're working smarter.

    What's the biggest content challenge in your business right now? 👇

    #ContentMarketing #Marketing #DigitalMarketing #B2B
    """

    result = predictor.predict(linkedin_post, platform="linkedin")
    print(f"[UV] LinkedIn Engagement Score: {result['overall_score']}/100 ({result['grade']})")
    print(f"[UV] Predicted: {result['predicted_performance']}")
    print(f"[UV] Recommendations: {result['recommendations'][:2]}")
