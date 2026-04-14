# Cursor-compatible + UV-ready
# Run: uv run python agents/social_media_formatter.py
"""
Social Media Formatter Agent - Repurposes content for different platforms.
Uses Groq for intelligent reformatting.
"""

import os
import re
import time
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class SocialMediaFormatterAgent:
    """
    Agent that formats and repurposes content for various social platforms.
    
    Supported platforms:
    - Twitter/X (thread format, 280 char limit per tweet)
    - LinkedIn (professional long-form post)
    - Instagram (caption + hashtags)
    - Facebook (engagement-optimized post)
    """

    GROQ_MODEL = "llama-3.3-70b-versatile"

    # Platform character limits
    LIMITS = {
        "twitter": 280,
        "linkedin": 3000,
        "instagram": 2200,
        "facebook": 63206,
    }

    def __init__(self):
        """Initialize Social Media Formatter."""
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

    def format_all(self, blog_content: str, research: dict) -> dict:
        """
        Format blog content for all supported platforms.

        Args:
            blog_content: Original blog post content
            research: Research dict with topic, tone, audience info

        Returns:
            dict with formatted content for each platform
        """
        topic = research.get("topic", "")
        
        return {
            "twitter_thread": self.format_twitter_thread(blog_content, research),
            "linkedin_post": self.format_linkedin(blog_content, research),
            "instagram_caption": self.format_instagram(blog_content, research),
            "facebook_post": self.format_facebook(blog_content, research),
            "topic": topic,
        }

    def format_twitter_thread(
        self,
        content: str,
        research: dict,
        num_tweets: int = 8,
        max_retries: int = 3,
    ) -> str:
        """
        Format content as a Twitter/X thread.

        Args:
            content: Blog post or article content
            research: Research context dict
            num_tweets: Number of tweets in thread
            max_retries: API retry attempts

        Returns:
            str: Formatted Twitter thread
        """
        topic = research.get("topic", "content marketing")
        
        # Extract key points from content
        key_points = self._extract_key_points(content, max_points=num_tweets - 2)

        prompt = f"""Convert this content into a viral Twitter/X thread about "{topic}".

CONTENT SUMMARY:
{content[:2000]}

KEY POINTS EXTRACTED:
{chr(10).join(f"- {p}" for p in key_points)}

REQUIREMENTS:
- {num_tweets} tweets total
- Each tweet: MAX 275 characters (leave room for thread numbering)
- Tweet 1: Scroll-stopping hook with a bold claim or surprising stat
- Tweets 2-{num_tweets-1}: One insight per tweet, use emojis, make each standalone
- Tweet {num_tweets}: Strong CTA + 3 relevant hashtags

FORMAT (use exactly this format):
[1/{num_tweets}] text here

[2/{num_tweets}] text here

Do NOT number with periods. Use only the bracket format above.
Write the thread now:"""

        for attempt in range(max_retries):
            try:
                client = self._get_client()
                response = client.chat.completions.create(
                    model=self.GROQ_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=2048,
                    temperature=0.8,
                )
                thread = response.choices[0].message.content
                return self._validate_twitter_thread(thread, num_tweets)

            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    return self._fallback_thread(topic, key_points, num_tweets)

    def format_linkedin(
        self,
        content: str,
        research: dict,
        max_retries: int = 3,
    ) -> str:
        """
        Format content as a LinkedIn post.

        Args:
            content: Source content
            research: Research context
            max_retries: API retry attempts

        Returns:
            str: LinkedIn-optimized post
        """
        topic = research.get("topic", "")
        audience = research.get("target_audience", "professionals")

        prompt = f"""Transform this content into a high-engagement LinkedIn post about "{topic}".

SOURCE CONTENT:
{content[:2500]}

TARGET AUDIENCE: {audience}

LINKEDIN POST REQUIREMENTS:
1. DO NOT start with "I'm excited" or similar phrases
2. Open with a provocative statement, bold insight, or counterintuitive claim
3. Use short paragraphs (1-3 sentences each)
4. Add white space — one idea per paragraph
5. Use bullet points with • symbol for lists
6. Include a story or personal angle
7. End with a thought-provoking question for comments
8. Add 4-5 relevant hashtags on a new line at the end
9. Target: 200-250 words

Write only the LinkedIn post, no preamble:"""

        for attempt in range(max_retries):
            try:
                client = self._get_client()
                response = client.chat.completions.create(
                    model=self.GROQ_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1024,
                    temperature=0.75,
                )
                return response.choices[0].message.content

            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    return self._fallback_linkedin(topic, content)

    def format_instagram(
        self,
        content: str,
        research: dict,
        max_retries: int = 3,
    ) -> str:
        """Format content as an Instagram caption with hashtags."""
        topic = research.get("topic", "")

        prompt = f"""Create an engaging Instagram caption for content about "{topic}".

CONTENT:
{content[:1500]}

INSTAGRAM CAPTION REQUIREMENTS:
1. First line: Attention-grabbing hook (this shows before "more")
2. 2-3 short paragraphs with the key insight
3. Line break then a call-to-action
4. Line break then 20-25 relevant hashtags (mix of popular and niche)
5. Use emojis naturally throughout
6. Max 300 words for caption text (before hashtags)

Write only the Instagram caption:"""

        for attempt in range(max_retries):
            try:
                client = self._get_client()
                response = client.chat.completions.create(
                    model=self.GROQ_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1024,
                    temperature=0.8,
                )
                return response.choices[0].message.content

            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    return f"✨ {topic}\n\nKey insights from our latest content...\n\n#marketing #content #digitalmarketing"

    def format_facebook(
        self,
        content: str,
        research: dict,
        max_retries: int = 3,
    ) -> str:
        """Format content as a Facebook post."""
        topic = research.get("topic", "")

        prompt = f"""Write a Facebook post about "{topic}" from this content.

CONTENT:
{content[:1500]}

FACEBOOK POST REQUIREMENTS:
1. Conversational, friendly tone
2. Start with a relatable question or statement
3. Share the main value/insight in 2-3 paragraphs
4. Include a clear call-to-action (comment, share, tag a friend)
5. 3-5 relevant hashtags at the end
6. Target: 150-200 words

Write only the Facebook post:"""

        for attempt in range(max_retries):
            try:
                client = self._get_client()
                response = client.chat.completions.create(
                    model=self.GROQ_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=768,
                    temperature=0.75,
                )
                return response.choices[0].message.content

            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    return f"Exciting insights on {topic}! Check out our latest post.\n\n#marketing #content"

    def _extract_key_points(self, content: str, max_points: int = 6) -> list:
        """Extract key points from content using simple heuristics."""
        points = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            # Extract headings
            if line.startswith('## ') or line.startswith('### '):
                clean = re.sub(r'^#+\s*', '', line)
                if clean and len(clean) > 10:
                    points.append(clean)
            # Extract bullet points
            elif line.startswith(('- ', '* ', '• ')):
                clean = re.sub(r'^[-*•]\s*', '', line)
                if clean and len(clean) > 15:
                    points.append(clean)
            
            if len(points) >= max_points:
                break
        
        # If not enough points from structure, split paragraphs
        if len(points) < 3:
            paras = [p.strip() for p in content.split('\n\n') if len(p.strip()) > 100]
            for para in paras[:max_points]:
                first_sentence = re.split(r'[.!?]', para)[0].strip()
                if first_sentence and len(first_sentence) > 20:
                    points.append(first_sentence[:120])
        
        return points[:max_points]

    def _validate_twitter_thread(self, thread: str, expected_tweets: int) -> str:
        """Ensure each tweet is within character limits."""
        tweets = re.split(r'\n\n+', thread.strip())
        validated = []
        
        for tweet in tweets:
            if not tweet.strip():
                continue
            # Remove thread numbering to check actual content length
            content_only = re.sub(r'^\[\d+/\d+\]\s*', '', tweet.strip())
            
            if len(tweet) > 280:
                # Truncate intelligently at sentence boundary
                truncated = tweet[:270].rsplit(' ', 1)[0] + '...'
                validated.append(truncated)
            else:
                validated.append(tweet)
        
        return '\n\n'.join(validated)

    def _fallback_thread(self, topic: str, key_points: list, num_tweets: int) -> str:
        """Generate a basic fallback thread if API fails."""
        tweets = [f"[1/{num_tweets}] 🧵 A thread on {topic}:"]
        
        for i, point in enumerate(key_points[:num_tweets-2], 2):
            tweets.append(f"[{i}/{num_tweets}] 💡 {point[:220]}")
        
        tweets.append(
            f"[{num_tweets}/{num_tweets}] 📌 Follow for more insights on {topic}!\n"
            f"#ContentMarketing #Marketing #DigitalMarketing"
        )
        
        return '\n\n'.join(tweets)

    def _fallback_linkedin(self, topic: str, content: str) -> str:
        """Fallback LinkedIn post."""
        first_para = content.split('\n\n')[0] if content else ""
        clean = re.sub(r'[#*_]', '', first_para)[:300]
        return f"""{clean}

What's your experience with {topic}?

#Marketing #ContentMarketing #DigitalMarketing #B2BMarketing"""


if __name__ == "__main__":
    agent = SocialMediaFormatterAgent()
    
    sample_blog = """
# Top 5 AI Marketing Trends 2025

AI is transforming content marketing dramatically. Companies using AI tools see 
3x better content output with 50% reduced production time.

## 1. Generative AI for Content at Scale
AI writing tools now produce publication-quality content in minutes.

## 2. Hyper-Personalization
Machine learning enables 1:1 content experiences at scale.

## 3. Predictive Analytics
AI predicts which content will perform before you publish it.
"""
    research = {"topic": "AI marketing trends 2025", "tone": "professional", "target_audience": "marketers"}
    
    print("[UV] Testing Social Media Formatter...")
    thread = agent.format_twitter_thread(sample_blog, research, num_tweets=5)
    print(thread[:400])
