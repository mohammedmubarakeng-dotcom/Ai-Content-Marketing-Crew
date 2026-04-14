# Cursor-compatible + UV-ready
"""
Content Marketing Suite - Utilities Package

Pure utility functions (no AI API calls):
- seo.py: Keyword extraction helpers
- plagiarism.py: Originality checker
- calendar_export.py: CSV/ICS export
- engagement.py: Rule-based engagement predictor
"""

from utils.seo import SEOUtils
from utils.plagiarism import PlagiarismChecker
from utils.calendar_export import CalendarExporter
from utils.engagement import EngagementPredictor

__all__ = [
    "SEOUtils",
    "PlagiarismChecker",
    "CalendarExporter",
    "EngagementPredictor",
]
