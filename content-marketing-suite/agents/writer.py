# Cursor-compatible + UV-ready
# Run: uv run python agents/writer.py
"""
Writer Agent - Uses Groq (llama-3.3-70b-versatile) to generate content.
Takes research notes and produces polished blog posts.
"""

import os
import time
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class WriterAgent:
    """
    AI agent that writes high-quality content using Groq's fast inference.
    
    Supports multiple content formats:
    - Blog post (markdown or HTML)
    - Twitter/X thread
    - LinkedIn post
    """

    GROQ_MODEL = "llama-3.3-70b-versatile"
    MAX_TOKENS = 4096

    def __init__(self, model: Optional[str] = None):
        """
        Initialize the Writer agent.

        Args:
            model: Groq model to use (default: llama-3.3-70b-versatile)
        """
        self.model = model or self.GROQ_MODEL
        self.api_key = os.getenv("GROQ_API_KEY", "")
        self._client = None

    def _get_client(self):
        """Lazy-load Groq client."""
        if self._client is None:
            try:
                from groq import Groq
                if not self.api_key:
                    raise ValueError("[UV] GROQ_API_KEY not set in .env file")
                self._client = Groq(api_key=self.api_key)
            except ImportError:
                raise ImportError("[UV] groq not installed. Run: uv sync")
        return self._client

    def write_blog_post(
        self,
        research: dict,
        word_count: int = 1200,
        output_format: str = "markdown",
        max_retries: int = 3,
    ) -> str:
        """
        Write a complete blog post from research notes.

        Args:
            research: Research dict from ResearcherAgent
            word_count: Target word count (default: 1200)
            output_format: 'markdown' or 'html'
            max_retries: Retry attempts on failure

        Returns:
            str: Complete blog post content
        """
        topic = research.get("topic", "")
        tone = research.get("tone", "professional")
        audience = research.get("target_audience", "readers")
        raw_research = research.get("raw_research", "")
        structure = research.get("recommended_structure", "")

        format_instruction = (
            "Format the output as clean Markdown with proper headings (##), "
            "bullet points, and bold text for emphasis."
            if output_format == "markdown"
            else "Format the output as clean semantic HTML with <h2>, <p>, <ul>, <li>, <strong> tags."
        )

        prompt = f"""You are an expert content writer. Write a comprehensive, engaging blog post.

TOPIC: {topic}
TARGET AUDIENCE: {audience}
TONE: {tone}
TARGET LENGTH: approximately {word_count} words

RESEARCH NOTES:
{raw_research[:3000]}

SUGGESTED STRUCTURE:
{structure}

WRITING REQUIREMENTS:
1. Write a compelling, SEO-friendly title (H1)
2. Open with a hook that immediately grabs attention
3. Use the research to back up all claims with specifics
4. Write in {tone} tone appropriate for {audience}
5. Include practical, actionable advice
6. End with a strong call-to-action
7. {format_instruction}
8. Include a meta description (150-160 characters) at the very top, labeled "META DESCRIPTION:"

Write the complete blog post now. Do not include any preamble or explanation — just the content.
"""

        for attempt in range(max_retries):
            try:
                client = self._get_client()
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=self.MAX_TOKENS,
                    temperature=0.7,
                )
                return response.choices[0].message.content

            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"[UV] Writer retry {attempt + 1}/{max_retries} after {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    print(f"[UV] Writer failed: {e}")
                    return self._fallback_blog(topic, audience)

    def write_twitter_thread(
        self,
        research: dict,
        num_tweets: int = 8,
        max_retries: int = 3,
    ) -> str:
        """
        Write a Twitter/X thread from research notes.

        Args:
            research: Research dict from ResearcherAgent
            num_tweets: Number of tweets in the thread (default: 8)
            max_retries: Retry attempts

        Returns:
            str: Formatted Twitter thread with numbered tweets
        """
        topic = research.get("topic", "")
        tone = research.get("tone", "professional")
        raw_research = research.get("raw_research", "")

        prompt = f"""You are a viral Twitter/X content creator. Write an engaging thread.

TOPIC: {topic}
TONE: {tone} but conversational for Twitter
NUMBER OF TWEETS: {num_tweets}

RESEARCH:
{raw_research[:2000]}

TWITTER THREAD REQUIREMENTS:
1. Tweet 1: Hook tweet that stops the scroll — bold claim or surprising stat
2. Tweets 2-{num_tweets-2}: Numbered insights, each under 280 characters
3. Second-to-last tweet: Practical takeaway or action step
4. Last tweet: Call to action (follow, retweet, reply, etc.)

FORMAT EACH TWEET AS:
[1/{num_tweets}] Tweet text here...

[2/{num_tweets}] Tweet text here...

Rules:
- Each tweet MUST be under 280 characters
- Use line breaks within tweets for readability
- Include 1-2 relevant emojis per tweet
- Add 2-3 relevant hashtags to the LAST tweet only
- Make each tweet standalone but part of a narrative arc

Write the complete thread now:
"""

        for attempt in range(max_retries):
            try:
                client = self._get_client()
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=2048,
                    temperature=0.8,
                )
                return response.choices[0].message.content

            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                else:
                    return self._fallback_twitter(topic)

    def write_linkedin_post(
        self,
        research: dict,
        max_retries: int = 3,
    ) -> str:
        """
        Write a LinkedIn post from research notes.

        Args:
            research: Research dict from ResearcherAgent
            max_retries: Retry attempts

        Returns:
            str: Formatted LinkedIn post
        """
        topic = research.get("topic", "")
        tone = research.get("tone", "professional")
        audience = research.get("target_audience", "professionals")
        raw_research = research.get("raw_research", "")
        stats = research.get("stats", "")

        prompt = f"""You are a LinkedIn thought leader. Write a high-engagement LinkedIn post.

TOPIC: {topic}
AUDIENCE: {audience}
TONE: {tone} but personal and authentic for LinkedIn

RESEARCH:
{raw_research[:2000]}

KEY STATS:
{stats}

LINKEDIN POST REQUIREMENTS:
1. Opening line: Pattern interrupt — make them stop scrolling (no "I'm excited to share...")
2. Personal angle or story hook (2-3 sentences)
3. Key insight or lesson (3-5 bullet points with •)
4. Practical takeaway
5. Engagement question at the end
6. 3-5 relevant hashtags on a new line at the end

TARGET LENGTH: 200-300 words
STYLE: Conversational, authentic, thought-leadership
AVOID: Corporate jargon, excessive buzzwords, humble-bragging

Write the complete LinkedIn post now (just the post, no preamble):
"""

        for attempt in range(max_retries):
            try:
                client = self._get_client()
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1024,
                    temperature=0.75,
                )
                return response.choices[0].message.content

            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                else:
                    return self._fallback_linkedin(topic)

    def _fallback_blog(self, topic: str, audience: str) -> str:
        return f"""# {topic}

*Content generation temporarily unavailable. Please check your GROQ_API_KEY in .env*

This blog post would cover the key aspects of {topic} for {audience}.

## Key Points
- Important aspect 1
- Important aspect 2  
- Important aspect 3

## Conclusion
[Content to be generated once API key is configured]
"""

    def _fallback_twitter(self, topic: str) -> str:
        return f"""[1/5] 🧵 A thread on {topic}

[2/5] Key insight about this topic...

[3/5] Another important point...

[4/5] What this means for you...

[5/5] Follow for more insights on {topic}! #ContentMarketing #Marketing

*(Note: Configure GROQ_API_KEY in .env for AI-generated content)*"""

    def _fallback_linkedin(self, topic: str) -> str:
        return f"""Here's what I've learned about {topic}...

• Key insight 1
• Key insight 2
• Key insight 3

What's your experience with this topic?

#Marketing #ContentMarketing

*(Note: Configure GROQ_API_KEY in .env for AI-generated content)*"""


if __name__ == "__main__":
    # Quick test with mock research
    agent = WriterAgent()
    mock_research = {
        "topic": "AI tools for content marketing",
        "tone": "professional",
        "target_audience": "marketers",
        "raw_research": "AI is transforming content marketing with tools for writing, SEO, and analytics.",
        "recommended_structure": "Intro, Top Tools, Implementation, ROI, Conclusion",
        "stats": "73% of marketers use AI tools in 2024",
    }
    print("[UV] Testing Writer Agent...")
    post = agent.write_linkedin_post(mock_research)
    print(post[:300])
