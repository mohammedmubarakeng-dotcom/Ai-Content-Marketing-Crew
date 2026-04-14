# Cursor-compatible + UV-ready
# Run: uv run python utils/plagiarism.py
"""
Plagiarism Checker - Uses sentence-transformers + fuzzy matching.
Compares content against a reference corpus for originality scoring.
"""

import re
import hashlib
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


# Common content patterns used to detect potential plagiarism
COMMON_PHRASES = [
    "in today's fast-paced world",
    "in the digital age",
    "it goes without saying",
    "at the end of the day",
    "think outside the box",
    "synergy",
    "leverage",
    "paradigm shift",
    "game changer",
    "best practices",
    "move the needle",
    "low-hanging fruit",
    "circle back",
    "deep dive",
    "bandwidth",
    "scalable solution",
    "disruptive innovation",
]


class PlagiarismChecker:
    """
    Checks content originality using:
    1. Sentence-transformers (semantic similarity)
    2. RapidFuzz (fuzzy string matching)
    3. Common phrase detection
    
    NOTE: This is a local similarity check — not a web plagiarism checker.
    It compares against a reference corpus (or previously generated content).
    """

    SIMILARITY_THRESHOLD = 0.85  # 85% similarity = potential plagiarism

    def __init__(self):
        """Initialize plagiarism checker."""
        self._model = None
        self._reference_corpus = []

    def _get_model(self):
        """Lazy-load sentence-transformers model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                # Use a small, fast model — free to use
                self._model = SentenceTransformer("all-MiniLM-L6-v2")
                print("[UV] Loaded sentence-transformers model: all-MiniLM-L6-v2")
            except ImportError:
                raise ImportError("[UV] sentence-transformers not installed. Run: uv sync")
        return self._model

    def check(
        self,
        content: str,
        reference_texts: Optional[list] = None,
        use_fuzzy: bool = True,
    ) -> dict:
        """
        Check content for plagiarism/similarity.

        Args:
            content: Text to check
            reference_texts: Optional list of reference texts to compare against
            use_fuzzy: Whether to use fuzzy matching in addition to semantic

        Returns:
            dict with originality_score, similar_passages, common_phrases, status
        """
        if not content or len(content.strip()) < 100:
            return {
                "originality_score": 100,
                "status": "ok",
                "note": "Content too short to analyze",
                "similar_passages": [],
                "common_phrases": [],
            }

        results = {
            "originality_score": 100,
            "status": "original",
            "similar_passages": [],
            "common_phrases": [],
            "word_count": len(content.split()),
        }

        # Check for common cliche phrases
        cliche_hits = self._check_common_phrases(content)
        results["common_phrases"] = cliche_hits
        
        # Deduct points for excessive cliches
        if len(cliche_hits) > 3:
            results["originality_score"] -= min(10, len(cliche_hits) * 2)

        # Fuzzy matching against reference corpus
        if use_fuzzy and (reference_texts or self._reference_corpus):
            refs = reference_texts or self._reference_corpus
            fuzzy_results = self._fuzzy_check(content, refs)
            results["similar_passages"].extend(fuzzy_results["matches"])
            results["originality_score"] -= fuzzy_results["penalty"]

        # Semantic similarity check (if reference texts provided)
        if reference_texts and len(reference_texts) > 0:
            try:
                semantic_results = self._semantic_check(content, reference_texts)
                results["similar_passages"].extend(semantic_results["matches"])
                results["originality_score"] -= semantic_results["penalty"]
            except Exception as e:
                results["semantic_check"] = f"unavailable: {e}"

        # Ensure score stays in valid range
        results["originality_score"] = max(0, min(100, round(results["originality_score"])))
        
        # Set status based on score
        score = results["originality_score"]
        if score >= 90:
            results["status"] = "original"
        elif score >= 70:
            results["status"] = "mostly_original"
        elif score >= 50:
            results["status"] = "some_similarity"
        else:
            results["status"] = "high_similarity"

        # Add content fingerprint for tracking
        results["content_hash"] = hashlib.md5(content.encode()).hexdigest()[:12]
        
        return results

    def _check_common_phrases(self, content: str) -> list:
        """Check for overused/cliche phrases."""
        content_lower = content.lower()
        found = []
        for phrase in COMMON_PHRASES:
            if phrase in content_lower:
                found.append(phrase)
        return found

    def _fuzzy_check(self, content: str, references: list) -> dict:
        """Fuzzy string matching against references."""
        try:
            from rapidfuzz import fuzz, process
        except ImportError:
            return {"matches": [], "penalty": 0}

        # Split content into sentences
        sentences = self._split_sentences(content)
        matches = []
        total_penalty = 0

        for ref in references:
            ref_sentences = self._split_sentences(ref)
            
            for sentence in sentences:
                if len(sentence) < 30:
                    continue
                
                # Find best fuzzy match
                best_match = process.extractOne(
                    sentence,
                    ref_sentences,
                    scorer=fuzz.token_sort_ratio,
                )
                
                if best_match and best_match[1] > 80:  # 80% similarity
                    matches.append({
                        "original": sentence[:100] + "..." if len(sentence) > 100 else sentence,
                        "similar_to": best_match[0][:100] + "..." if len(best_match[0]) > 100 else best_match[0],
                        "similarity": best_match[1],
                        "method": "fuzzy",
                    })
                    
                    if best_match[1] > 90:
                        total_penalty += 5
                    elif best_match[1] > 80:
                        total_penalty += 2

        return {"matches": matches[:5], "penalty": min(30, total_penalty)}

    def _semantic_check(self, content: str, references: list) -> dict:
        """Semantic similarity using sentence-transformers."""
        try:
            import numpy as np
            model = self._get_model()
            
            # Split into sentences
            content_sentences = self._split_sentences(content)[:20]  # Limit for performance
            
            if not content_sentences:
                return {"matches": [], "penalty": 0}
            
            # Encode content sentences
            content_embeddings = model.encode(content_sentences)
            
            matches = []
            total_penalty = 0
            
            for ref in references[:3]:  # Limit references for performance
                ref_sentences = self._split_sentences(ref)[:20]
                if not ref_sentences:
                    continue
                
                ref_embeddings = model.encode(ref_sentences)
                
                # Calculate cosine similarity
                for i, (c_emb, c_sent) in enumerate(zip(content_embeddings, content_sentences)):
                    for j, (r_emb, r_sent) in enumerate(zip(ref_embeddings, ref_sentences)):
                        # Cosine similarity
                        similarity = np.dot(c_emb, r_emb) / (
                            np.linalg.norm(c_emb) * np.linalg.norm(r_emb) + 1e-8
                        )
                        
                        if similarity > self.SIMILARITY_THRESHOLD:
                            matches.append({
                                "original": c_sent[:100],
                                "similar_to": r_sent[:100],
                                "similarity": round(float(similarity) * 100, 1),
                                "method": "semantic",
                            })
                            total_penalty += (float(similarity) - 0.8) * 20
            
            return {"matches": matches[:5], "penalty": min(25, total_penalty)}
        
        except Exception as e:
            return {"matches": [], "penalty": 0, "error": str(e)}

    def add_to_corpus(self, content: str):
        """Add content to the reference corpus for future checks."""
        self._reference_corpus.append(content)

    def _split_sentences(self, text: str) -> list:
        """Split text into sentences."""
        # Remove markdown formatting
        clean = re.sub(r'[#*_`]', '', text)
        sentences = re.split(r'(?<=[.!?])\s+', clean)
        return [s.strip() for s in sentences if len(s.strip()) > 20]

    def get_originality_badge(self, score: int) -> str:
        """Get a human-readable badge for the originality score."""
        if score >= 90:
            return "🟢 Highly Original"
        elif score >= 75:
            return "🟡 Mostly Original"
        elif score >= 60:
            return "🟠 Some Similarities"
        else:
            return "🔴 High Similarity Detected"


if __name__ == "__main__":
    checker = PlagiarismChecker()
    
    original_text = """
    Content marketing represents a strategic approach to creating valuable information 
    that attracts and engages target audiences. Modern AI tools are revolutionizing 
    how marketers produce content at unprecedented scale and quality.
    """
    
    similar_text = """
    Content marketing is a strategic approach focused on creating valuable information 
    that attracts and engages audiences. AI tools are revolutionizing content production 
    at scale.
    """
    
    result = checker.check(original_text, reference_texts=[similar_text])
    print(f"[UV] Originality Score: {result['originality_score']}%")
    print(f"[UV] Status: {result['status']}")
    print(f"[UV] Badge: {checker.get_originality_badge(result['originality_score'])}")
