# Cursor-compatible + UV-ready
# Run: uv run python -m agents
"""
Content Marketing Suite - AI Agents Package

Implements a CrewAI-style sequential pipeline:
  Researcher -> Writer -> SEO Specialist -> Social Media Formatter
"""

from agents.researcher import ResearcherAgent
from agents.writer import WriterAgent
from agents.seo_specialist import SEOSpecialistAgent
from agents.social_media_formatter import SocialMediaFormatterAgent
from agents.tasks import ContentPipeline

__all__ = [
    "ResearcherAgent",
    "WriterAgent",
    "SEOSpecialistAgent",
    "SocialMediaFormatterAgent",
    "ContentPipeline",
]
