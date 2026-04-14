# Cursor-compatible + UV-ready
# Run: uv run python agents/seo_specialist.py
"""
SEO Specialist Agent - Analyzes content and optimizes for search engines.
Uses spaCy + YAKE for free keyword extraction (no paid APIs).
"""

import os
import re
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class SEOSpecialistAgent:
    """
    AI agent that performs SEO analysis and optimization on content.
    
    Uses free tools:
    - YAKE: Keyword extraction
    - spaCy: NLP analysis (entities, noun phrases)
    - TextBlob: Sentiment analysis
    - Readability scoring (custom Flesch-Kincaid)
    """

    def __init__(self):
        """Initialize SEO Specialist with NLP tools."""
        self._nlp = None
        self._yake_extractor = None

    def _get_nlp(self):
        """Lazy-load spaCy model."""
        if self._nlp is None:
            try:
                import spacy
                try:
                    self._nlp = spacy.load("en_core_web_sm")
                except OSError:
                    print("[UV] Downloading spaCy model en_core_web_sm...")
                    os.system("python -m spacy download en_core_web_sm")
                    try:
                        self._nlp = spacy.load("en_core_web_sm")
                    except OSError:
                        # Fallback: use blank English model
                        self._nlp = spacy.blank("en")
                        print("[UV] Using blank spaCy model (limited NLP features)")
            except ImportError:
                raise ImportError("[UV] spacy not installed. Run: uv sync")
        return self._nlp

    def _get_yake(self):
        """Lazy-load YAKE keyword extractor."""
        if self._yake_extractor is None:
            try:
                import yake
                self._yake_extractor = yake.KeywordExtractor(
                    lan="en",
                    n=3,  # max n-gram size
                    dedupLim=0.7,
                    top=20,
                    features=None,
                )
            except ImportError:
                raise ImportError("[UV] yake not installed. Run: uv sync")
        return self._yake_extractor

    def analyze(self, content: str, topic: str, target_keywords: Optional[list] = None) -> dict:
        """
        Perform comprehensive SEO analysis on content.

        Args:
            content: The content to analyze
            topic: The main topic (used as primary keyword context)
            target_keywords: Optional list of target keywords to check

        Returns:
            dict with SEO metrics and recommendations
        """
        if not content or len(content.strip()) < 50:
            return {"error": "Content too short for analysis", "score": 0}

        # Run all analyses
        keywords = self.extract_keywords(content)
        readability = self.calculate_readability(content)
        structure = self.analyze_structure(content)
        sentiment = self.analyze_sentiment(content)
        entities = self.extract_entities(content)
        density = self.calculate_keyword_density(content, topic)
        meta = self.extract_meta_description(content)

        # Calculate overall SEO score (0-100)
        score = self._calculate_seo_score(
            readability, structure, density, keywords, content, meta
        )

        recommendations = self._generate_recommendations(
            score, readability, structure, density, keywords, meta
        )

        return {
            "score": score,
            "grade": self._score_to_grade(score),
            "keywords": keywords[:10],
            "top_keyword": keywords[0] if keywords else topic,
            "keyword_density": density,
            "readability": readability,
            "structure": structure,
            "sentiment": sentiment,
            "entities": entities[:10],
            "meta_description": meta,
            "word_count": len(content.split()),
            "recommendations": recommendations,
            "optimized_title": self._suggest_title(topic, keywords),
        }

    def extract_keywords(self, content: str) -> list:
        """
        Extract keywords using YAKE algorithm.

        Args:
            content: Text to extract keywords from

        Returns:
            list of (keyword, score) tuples, sorted by relevance
        """
        try:
            extractor = self._get_yake()
            # YAKE returns (keyword, score) — lower score = more relevant
            raw_keywords = extractor.extract_keywords(content)
            # Sort by score ascending (most relevant first), return just keywords
            sorted_kw = sorted(raw_keywords, key=lambda x: x[1])
            return [kw for kw, score in sorted_kw]
        except Exception as e:
            print(f"[UV] YAKE extraction failed: {e}")
            # Simple fallback: word frequency
            words = re.findall(r'\b[a-zA-Z]{4,}\b', content.lower())
            freq = {}
            stopwords = {"that", "this", "with", "have", "from", "they", "will", "your", "been", "were"}
            for w in words:
                if w not in stopwords:
                    freq[w] = freq.get(w, 0) + 1
            return sorted(freq.keys(), key=lambda x: freq[x], reverse=True)[:20]

    def calculate_readability(self, content: str) -> dict:
        """
        Calculate Flesch-Kincaid readability scores.

        Args:
            content: Text to analyze

        Returns:
            dict with reading_ease, grade_level, and interpretation
        """
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        words = content.split()
        
        if not sentences or not words:
            return {"reading_ease": 0, "grade_level": 0, "interpretation": "Unknown"}

        syllable_count = sum(self._count_syllables(w) for w in words)
        
        avg_sentence_length = len(words) / len(sentences) if sentences else 0
        avg_syllables_per_word = syllable_count / len(words) if words else 0

        # Flesch Reading Ease
        reading_ease = (
            206.835
            - (1.015 * avg_sentence_length)
            - (84.6 * avg_syllables_per_word)
        )
        reading_ease = max(0, min(100, reading_ease))

        # Flesch-Kincaid Grade Level
        grade_level = (
            0.39 * avg_sentence_length
            + 11.8 * avg_syllables_per_word
            - 15.59
        )
        grade_level = max(1, grade_level)

        interpretations = [
            (90, "Very Easy (5th grade)"),
            (80, "Easy (6th grade)"),
            (70, "Fairly Easy (7th grade)"),
            (60, "Standard (8th-9th grade)"),
            (50, "Fairly Difficult (10th-12th grade)"),
            (30, "Difficult (College level)"),
            (0, "Very Difficult (Professional)"),
        ]
        interpretation = "Very Difficult"
        for threshold, label in interpretations:
            if reading_ease >= threshold:
                interpretation = label
                break

        return {
            "reading_ease": round(reading_ease, 1),
            "grade_level": round(grade_level, 1),
            "interpretation": interpretation,
            "avg_sentence_length": round(avg_sentence_length, 1),
            "avg_syllables_per_word": round(avg_syllables_per_word, 2),
        }

    def analyze_structure(self, content: str) -> dict:
        """Analyze content structure (headings, paragraphs, lists, etc.)."""
        lines = content.split('\n')
        
        h1_count = sum(1 for l in lines if l.strip().startswith('# ') and not l.strip().startswith('## '))
        h2_count = sum(1 for l in lines if l.strip().startswith('## '))
        h3_count = sum(1 for l in lines if l.strip().startswith('### '))
        bullet_count = sum(1 for l in lines if l.strip().startswith(('- ', '* ', '• ')))
        numbered_count = sum(1 for l in lines if re.match(r'^\d+\.', l.strip()))
        
        paragraphs = [p for p in content.split('\n\n') if len(p.strip()) > 50]
        
        has_intro = len(paragraphs) > 0 and len(paragraphs[0]) > 100
        has_conclusion = len(paragraphs) > 1 and len(paragraphs[-1]) > 100
        
        # Check for bold/emphasis
        bold_count = len(re.findall(r'\*\*[^*]+\*\*', content))
        
        return {
            "h1_count": h1_count,
            "h2_count": h2_count,
            "h3_count": h3_count,
            "paragraph_count": len(paragraphs),
            "bullet_points": bullet_count,
            "numbered_items": numbered_count,
            "bold_emphasis": bold_count,
            "has_introduction": has_intro,
            "has_conclusion": has_conclusion,
            "has_subheadings": h2_count >= 2,
            "has_lists": bullet_count + numbered_count > 0,
        }

    def analyze_sentiment(self, content: str) -> dict:
        """Analyze content sentiment using TextBlob."""
        try:
            from textblob import TextBlob
            blob = TextBlob(content[:3000])  # Limit for performance
            
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity
            
            if polarity > 0.1:
                label = "Positive"
            elif polarity < -0.1:
                label = "Negative"
            else:
                label = "Neutral"
                
            return {
                "polarity": round(polarity, 3),
                "subjectivity": round(subjectivity, 3),
                "label": label,
            }
        except ImportError:
            return {"polarity": 0, "subjectivity": 0.5, "label": "Neutral"}

    def extract_entities(self, content: str) -> list:
        """Extract named entities using spaCy."""
        try:
            nlp = self._get_nlp()
            doc = nlp(content[:5000])  # Limit for performance
            entities = [
                {"text": ent.text, "label": ent.label_}
                for ent in doc.ents
                if ent.label_ in {"ORG", "PRODUCT", "PERSON", "GPE", "NORP", "TECHNOLOGY"}
            ]
            # Deduplicate
            seen = set()
            unique = []
            for e in entities:
                if e["text"] not in seen:
                    seen.add(e["text"])
                    unique.append(e)
            return unique
        except Exception:
            return []

    def calculate_keyword_density(self, content: str, keyword: str) -> dict:
        """Calculate keyword density for the target keyword."""
        words = content.lower().split()
        keyword_lower = keyword.lower()
        keyword_words = keyword_lower.split()
        
        total_words = len(words)
        if total_words == 0:
            return {"density": 0.0, "count": 0, "status": "unknown"}
        
        # Count exact phrase occurrences
        text_lower = content.lower()
        count = text_lower.count(keyword_lower)
        
        # Also count individual keyword words
        word_count = sum(words.count(w) for w in keyword_words)
        
        density = (count / total_words) * 100
        
        if density < 0.5:
            status = "too_low"
        elif density > 3.0:
            status = "too_high"
        else:
            status = "optimal"
        
        return {
            "density": round(density, 2),
            "count": count,
            "word_count": word_count,
            "status": status,
            "total_words": total_words,
        }

    def extract_meta_description(self, content: str) -> str:
        """Extract or generate a meta description from content."""
        # Look for explicit meta description
        meta_match = re.search(
            r'META DESCRIPTION[:\s]+(.+?)(?:\n|$)', content, re.IGNORECASE
        )
        if meta_match:
            return meta_match.group(1).strip()[:160]
        
        # Extract first meaningful paragraph
        paragraphs = [p.strip() for p in content.split('\n\n') if len(p.strip()) > 50]
        if paragraphs:
            # Remove markdown formatting
            clean = re.sub(r'[#*_`]', '', paragraphs[0])
            clean = re.sub(r'\s+', ' ', clean).strip()
            return clean[:157] + "..." if len(clean) > 157 else clean
        
        return ""

    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word (simple heuristic)."""
        word = word.lower().strip(".,!?;:")
        if not word:
            return 0
        
        vowels = "aeiouy"
        count = 0
        prev_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_was_vowel:
                count += 1
            prev_was_vowel = is_vowel
        
        # Adjust for silent 'e'
        if word.endswith('e') and count > 1:
            count -= 1
        
        return max(1, count)

    def _calculate_seo_score(
        self, readability, structure, density, keywords, content, meta
    ) -> int:
        """Calculate overall SEO score (0-100)."""
        score = 0
        
        # Readability: 25 points
        if readability["reading_ease"] >= 60:
            score += 25
        elif readability["reading_ease"] >= 40:
            score += 15
        else:
            score += 5
        
        # Structure: 30 points
        if structure["has_subheadings"]:
            score += 10
        if structure["has_lists"]:
            score += 8
        if structure["has_introduction"] and structure["has_conclusion"]:
            score += 7
        if structure["bold_emphasis"] > 0:
            score += 5
        
        # Content length: 20 points
        word_count = len(content.split())
        if word_count >= 1200:
            score += 20
        elif word_count >= 800:
            score += 15
        elif word_count >= 500:
            score += 10
        else:
            score += 5
        
        # Keyword density: 15 points
        if density["status"] == "optimal":
            score += 15
        elif density["status"] in ("too_low", "too_high"):
            score += 5
        
        # Meta description: 10 points
        if meta and 120 <= len(meta) <= 160:
            score += 10
        elif meta:
            score += 5
        
        return min(100, score)

    def _score_to_grade(self, score: int) -> str:
        """Convert numeric score to letter grade."""
        if score >= 90:
            return "A+"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 60:
            return "C"
        elif score >= 50:
            return "D"
        else:
            return "F"

    def _generate_recommendations(
        self, score, readability, structure, density, keywords, meta
    ) -> list:
        """Generate actionable SEO recommendations."""
        recs = []
        
        if readability["reading_ease"] < 60:
            recs.append("📖 Simplify sentences — target Flesch reading ease of 60+")
        
        if not structure["has_subheadings"]:
            recs.append("🏗️ Add H2 subheadings every 300-400 words")
        
        if not structure["has_lists"]:
            recs.append("📋 Add bullet points or numbered lists for scannability")
        
        if density["status"] == "too_low":
            recs.append(f"🔑 Increase keyword density — currently {density['density']}% (target: 1-2%)")
        elif density["status"] == "too_high":
            recs.append(f"⚠️ Reduce keyword density — currently {density['density']}% (target: 1-2%)")
        
        if not meta:
            recs.append("📝 Add a meta description (150-160 characters)")
        elif len(meta) < 120:
            recs.append(f"📝 Expand meta description to 150-160 characters (currently {len(meta)})")
        
        if len(keywords) < 5:
            recs.append("🔍 Content may need more topical depth — consider expanding")
        
        if not structure["has_introduction"]:
            recs.append("✍️ Strengthen the introduction paragraph")
        
        if not structure["has_conclusion"]:
            recs.append("🎯 Add a clear conclusion with call-to-action")
        
        if score >= 80:
            recs.append("✅ Great SEO foundation! Consider internal linking strategy")
        
        return recs[:6]  # Top 6 recommendations

    def _suggest_title(self, topic: str, keywords: list) -> str:
        """Suggest an SEO-optimized title."""
        if not keywords:
            return f"The Complete Guide to {topic.title()}"
        
        top_kw = keywords[0] if keywords else topic
        templates = [
            f"The Complete Guide to {topic.title()} in 2025",
            f"How to Master {top_kw.title()}: A Practical Guide",
            f"{topic.title()}: Everything You Need to Know",
            f"Top Strategies for {topic.title()} That Actually Work",
        ]
        return templates[0]


if __name__ == "__main__":
    agent = SEOSpecialistAgent()
    sample_content = """
# AI Marketing Tools in 2025

META DESCRIPTION: Discover the top AI marketing tools transforming content creation in 2025. Learn how to leverage AI for better ROI.

Artificial intelligence is revolutionizing content marketing. In 2025, marketers who embrace AI tools are seeing 3x better results.

## Why AI Marketing Tools Matter

The landscape of digital marketing has changed dramatically. AI-powered tools now handle everything from keyword research to content generation.

- Faster content production
- Better personalization
- Improved SEO performance
- Data-driven decisions

## Top Tools to Consider

Several platforms stand out for their capabilities and ease of use. The best AI marketing tools combine natural language processing with marketing analytics.
"""
    result = agent.analyze(sample_content, "AI marketing tools")
    print(f"[UV] SEO Score: {result['score']}/100 ({result['grade']})")
    print(f"[UV] Top keyword: {result['top_keyword']}")
    print(f"[UV] Recommendations: {result['recommendations'][:2]}")
