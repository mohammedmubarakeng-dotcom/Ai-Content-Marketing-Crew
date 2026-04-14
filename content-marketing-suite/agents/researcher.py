# Cursor-compatible + UV-ready
# Run: uv run python agents/researcher.py
"""
Researcher Agent - Uses Google Gemini to gather research on a topic.
Produces structured research notes for the Writer agent.
"""

import os
import time
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class ResearcherAgent:
    """
    AI agent that researches a topic using Google Gemini.
    
    Produces structured research notes including:
    - Key facts and statistics
    - Current trends
    - Target audience insights
    - Content angles
    """

    def __init__(self, model: str = "gemini-1.5-flash"):
        """
        Initialize the Researcher agent.

        Args:
            model: Gemini model to use (default: gemini-1.5-flash for free tier)
        """
        self.model_name = model
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self._client = None

    def _get_client(self):
        """Lazy-load Gemini client to avoid import errors on missing API key."""
        if self._client is None:
            try:
                import google.generativeai as genai
                if not self.api_key:
                    raise ValueError("[UV] GEMINI_API_KEY not set in .env file")
                genai.configure(api_key=self.api_key)
                self._client = genai.GenerativeModel(self.model_name)
            except ImportError:
                raise ImportError(
                    "[UV] google-generativeai not installed. Run: uv sync"
                )
        return self._client

    def research(
        self,
        topic: str,
        tone: str = "professional",
        target_audience: str = "marketing professionals",
        max_retries: int = 3,
    ) -> dict:
        """
        Research a topic and return structured notes.

        Args:
            topic: The content topic to research
            tone: Writing tone (professional, casual, educational, etc.)
            target_audience: Who the content is for
            max_retries: Number of retry attempts on API failure

        Returns:
            dict with keys: topic, key_facts, trends, angles, audience_pain_points, stats
        """
        prompt = f"""You are an expert content researcher. Research the following topic thoroughly.

Topic: {topic}
Target Audience: {target_audience}
Tone: {tone}

Provide a comprehensive research brief with the following sections:

## KEY FACTS
(5-7 important, accurate facts about this topic)

## CURRENT TRENDS
(3-5 current trends relevant to this topic in 2024-2025)

## CONTENT ANGLES
(4-6 unique angles or perspectives to cover this topic)

## AUDIENCE PAIN POINTS
(3-5 specific challenges the target audience faces related to this topic)

## STATISTICS & DATA POINTS
(4-6 compelling statistics or data points — use realistic estimates if exact data unavailable, note them as estimates)

## RECOMMENDED STRUCTURE
(Suggested blog post outline with 5-7 sections)

Be specific, actionable, and focused on what would make genuinely useful content for {target_audience}.
"""

        for attempt in range(max_retries):
            try:
                client = self._get_client()
                response = client.generate_content(prompt)
                research_text = response.text

                return self._parse_research(topic, research_text, tone, target_audience)

            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"[UV] Researcher retry {attempt + 1}/{max_retries} after {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    print(f"[UV] Researcher failed after {max_retries} attempts: {e}")
                    return self._fallback_research(topic, tone, target_audience)

    def _parse_research(
        self, topic: str, raw_text: str, tone: str, audience: str
    ) -> dict:
        """Parse raw research text into structured dict."""
        sections = {
            "topic": topic,
            "tone": tone,
            "target_audience": audience,
            "raw_research": raw_text,
            "key_facts": "",
            "trends": "",
            "angles": "",
            "audience_pain_points": "",
            "stats": "",
            "recommended_structure": "",
        }

        # Extract sections from markdown-style output
        current_section = None
        section_map = {
            "KEY FACTS": "key_facts",
            "CURRENT TRENDS": "trends",
            "CONTENT ANGLES": "angles",
            "AUDIENCE PAIN POINTS": "audience_pain_points",
            "STATISTICS & DATA POINTS": "stats",
            "RECOMMENDED STRUCTURE": "recommended_structure",
        }

        lines = raw_text.split("\n")
        buffer = []

        for line in lines:
            line_upper = line.strip().upper().replace("##", "").strip()
            matched = False
            for key, attr in section_map.items():
                if key in line_upper:
                    if current_section and buffer:
                        sections[current_section] = "\n".join(buffer).strip()
                    current_section = attr
                    buffer = []
                    matched = True
                    break
            if not matched and current_section:
                buffer.append(line)

        if current_section and buffer:
            sections[current_section] = "\n".join(buffer).strip()

        return sections

    def _fallback_research(self, topic: str, tone: str, audience: str) -> dict:
        """Return minimal research if API fails — allows pipeline to continue."""
        return {
            "topic": topic,
            "tone": tone,
            "target_audience": audience,
            "raw_research": f"Research on: {topic}",
            "key_facts": f"Key information about {topic} for {audience}.",
            "trends": f"Current trends in {topic}.",
            "angles": f"Various perspectives on {topic}.",
            "audience_pain_points": f"Common challenges related to {topic}.",
            "stats": "Statistics and data points (research API unavailable).",
            "recommended_structure": "Introduction, Main Points, Conclusion.",
        }


if __name__ == "__main__":
    # Quick test
    agent = ResearcherAgent()
    result = agent.research(
        topic="AI tools for content marketing",
        target_audience="small business owners",
    )
    print(f"[UV] Research complete for: {result['topic']}")
    print(f"[UV] Key facts preview: {result['key_facts'][:200]}...")
