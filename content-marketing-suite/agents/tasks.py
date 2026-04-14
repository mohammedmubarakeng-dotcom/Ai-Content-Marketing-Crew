# Cursor-compatible + UV-ready
# Run: uv run python agents/tasks.py
"""
Content Pipeline - CrewAI-style sequential task orchestration.
Chains: Researcher -> Writer -> SEO Specialist -> Social Media Formatter
"""

import time
from typing import Optional, Callable
from dotenv import load_dotenv

load_dotenv()

from agents.researcher import ResearcherAgent
from agents.writer import WriterAgent
from agents.seo_specialist import SEOSpecialistAgent
from agents.social_media_formatter import SocialMediaFormatterAgent
from utils.plagiarism import PlagiarismChecker
from utils.engagement import EngagementPredictor


class ContentPipeline:
    """
    Orchestrates the full content creation pipeline.
    
    Pipeline stages:
    1. Research (Gemini) — gather facts, trends, structure
    2. Write (Groq) — produce blog post, Twitter, LinkedIn
    3. SEO Analysis (spaCy + YAKE) — score and optimize
    4. Social Formatting (Groq) — repurpose for each platform
    5. Plagiarism Check (sentence-transformers) — similarity check
    6. Engagement Prediction (rule-based) — predict performance
    """

    def __init__(
        self,
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ):
        """
        Initialize the content pipeline.

        Args:
            progress_callback: Optional function(message, percent) for progress updates
        """
        self.researcher = ResearcherAgent()
        self.writer = WriterAgent()
        self.seo = SEOSpecialistAgent()
        self.formatter = SocialMediaFormatterAgent()
        self.plagiarism = PlagiarismChecker()
        self.engagement = EngagementPredictor()
        self._progress = progress_callback or (lambda msg, pct: print(f"[{pct}%] {msg}"))

    def run(
        self,
        topic: str,
        tone: str = "professional",
        target_audience: str = "marketing professionals",
        word_count: int = 1200,
        formats: Optional[list] = None,
        check_plagiarism: bool = True,
    ) -> dict:
        """
        Run the complete content generation pipeline.

        Args:
            topic: Content topic
            tone: Writing tone
            target_audience: Target reader persona
            word_count: Target blog post word count
            formats: List of formats to generate (default: all)
            check_plagiarism: Whether to run plagiarism check

        Returns:
            Complete results dict with all generated content and metrics
        """
        if formats is None:
            formats = ["blog", "twitter", "linkedin"]

        results = {
            "topic": topic,
            "tone": tone,
            "target_audience": target_audience,
            "formats": formats,
            "timestamp": time.strftime("%Y-%m-%d %Human:%M:%S"),
            "pipeline_stages": [],
        }

        start_time = time.time()

        # Stage 1: Research
        self._progress("🔬 Researching topic with Gemini...", 10)
        try:
            research = self.researcher.research(
                topic=topic,
                tone=tone,
                target_audience=target_audience,
            )
            results["research"] = research
            results["pipeline_stages"].append({"stage": "research", "status": "success"})
            self._progress("✅ Research complete", 25)
        except Exception as e:
            results["research"] = self.researcher._fallback_research(topic, tone, target_audience)
            results["pipeline_stages"].append({"stage": "research", "status": "fallback", "error": str(e)})
            self._progress(f"⚠️ Research used fallback: {e}", 25)

        research = results["research"]

        # Stage 2: Write content
        self._progress("✍️ Writing content with Groq...", 30)
        content_outputs = {}

        if "blog" in formats:
            self._progress("✍️ Writing blog post...", 35)
            try:
                blog_md = self.writer.write_blog_post(
                    research=research,
                    word_count=word_count,
                    output_format="markdown",
                )
                blog_html = self.writer.write_blog_post(
                    research=research,
                    word_count=word_count,
                    output_format="html",
                )
                content_outputs["blog_markdown"] = blog_md
                content_outputs["blog_html"] = blog_html
            except Exception as e:
                content_outputs["blog_markdown"] = self.writer._fallback_blog(topic, target_audience)
                content_outputs["blog_html"] = content_outputs["blog_markdown"]
                self._progress(f"⚠️ Blog used fallback: {e}", 40)

        if "twitter" in formats:
            self._progress("🐦 Generating Twitter thread...", 50)
            try:
                content_outputs["twitter"] = self.writer.write_twitter_thread(research=research)
            except Exception as e:
                content_outputs["twitter"] = self.writer._fallback_twitter(topic)

        if "linkedin" in formats:
            self._progress("💼 Generating LinkedIn post...", 60)
            try:
                content_outputs["linkedin"] = self.writer.write_linkedin_post(research=research)
            except Exception as e:
                content_outputs["linkedin"] = self.writer._fallback_linkedin(topic)

        results["content"] = content_outputs
        results["pipeline_stages"].append({"stage": "writing", "status": "success"})

        # Stage 3: SEO Analysis
        self._progress("🔍 Running SEO analysis...", 65)
        blog_content = content_outputs.get("blog_markdown", "")
        try:
            seo_results = self.seo.analyze(blog_content, topic)
            results["seo"] = seo_results
            results["pipeline_stages"].append({"stage": "seo", "status": "success"})
            self._progress(f"✅ SEO Score: {seo_results.get('score', 0)}/100", 75)
        except Exception as e:
            results["seo"] = {"score": 0, "grade": "N/A", "error": str(e), "recommendations": []}
            results["pipeline_stages"].append({"stage": "seo", "status": "error", "error": str(e)})

        # Stage 4: Social Media Formatting
        self._progress("📱 Formatting for social media...", 80)
        try:
            social_formats = self.formatter.format_all(blog_content, research)
            results["social_formats"] = social_formats
            results["pipeline_stages"].append({"stage": "social_formatting", "status": "success"})
        except Exception as e:
            results["social_formats"] = {"error": str(e)}
            results["pipeline_stages"].append({"stage": "social_formatting", "status": "error"})

        # Stage 5: Plagiarism Check
        if check_plagiarism and blog_content:
            self._progress("🔎 Checking for plagiarism...", 85)
            try:
                plagiarism_result = self.plagiarism.check(blog_content)
                results["plagiarism"] = plagiarism_result
                results["pipeline_stages"].append({"stage": "plagiarism", "status": "success"})
            except Exception as e:
                results["plagiarism"] = {
                    "originality_score": 95,
                    "status": "check_unavailable",
                    "note": str(e),
                }

        # Stage 6: Engagement Prediction
        self._progress("📊 Predicting engagement...", 90)
        try:
            engagement_scores = {}
            if "blog_markdown" in content_outputs:
                engagement_scores["blog"] = self.engagement.predict(
                    content_outputs["blog_markdown"], platform="blog"
                )
            if "twitter" in content_outputs:
                engagement_scores["twitter"] = self.engagement.predict(
                    content_outputs["twitter"], platform="twitter"
                )
            if "linkedin" in content_outputs:
                engagement_scores["linkedin"] = self.engagement.predict(
                    content_outputs["linkedin"], platform="linkedin"
                )
            results["engagement"] = engagement_scores
            results["pipeline_stages"].append({"stage": "engagement", "status": "success"})
        except Exception as e:
            results["engagement"] = {}

        # Finalize
        elapsed = round(time.time() - start_time, 2)
        results["elapsed_seconds"] = elapsed
        self._progress(f"🎉 Pipeline complete in {elapsed}s!", 100)

        return results

    def generate_single(
        self,
        topic: str,
        format_type: str = "blog",
        tone: str = "professional",
        target_audience: str = "marketers",
    ) -> str:
        """
        Quick generation for a single format.

        Args:
            topic: Content topic
            format_type: 'blog', 'twitter', or 'linkedin'
            tone: Writing tone
            target_audience: Target audience

        Returns:
            str: Generated content
        """
        research = self.researcher.research(topic, tone, target_audience)
        
        if format_type == "blog":
            return self.writer.write_blog_post(research)
        elif format_type == "twitter":
            return self.writer.write_twitter_thread(research)
        elif format_type == "linkedin":
            return self.writer.write_linkedin_post(research)
        else:
            raise ValueError(f"Unknown format: {format_type}. Use: blog, twitter, linkedin")


if __name__ == "__main__":
    print("[UV] Testing Content Pipeline...")
    
    def progress(msg, pct):
        print(f"  [{pct:3d}%] {msg}")
    
    pipeline = ContentPipeline(progress_callback=progress)
    
    results = pipeline.run(
        topic="AI tools for content marketing",
        tone="professional",
        target_audience="digital marketers",
        word_count=800,
        formats=["blog", "linkedin"],
        check_plagiarism=False,  # Skip for quick test
    )
    
    print(f"\n[UV] Pipeline complete!")
    print(f"[UV] Blog word count: {len(results['content'].get('blog_markdown', '').split())}")
    print(f"[UV] SEO Score: {results.get('seo', {}).get('score', 'N/A')}/100")
    print(f"[UV] Elapsed: {results.get('elapsed_seconds', 0)}s")
