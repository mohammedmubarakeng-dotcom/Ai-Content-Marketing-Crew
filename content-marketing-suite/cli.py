#!/usr/bin/env python3
# Cursor-compatible + UV-ready
# Run: uv run content-suite --topic "AI trends 2025" --format blog
"""
Content Marketing Suite - CLI Entry Point
Usage: uv run content-suite [options]
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def create_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="content-suite",
        description="🚀 Automated Content Marketing Suite — powered by Groq + Gemini",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate a blog post
  uv run content-suite --topic "AI marketing trends 2025" --format blog

  # Generate all formats
  uv run content-suite --topic "Content repurposing tips" --format all

  # Twitter thread only, casual tone
  uv run content-suite --topic "SEO tips" --format twitter --tone casual

  # Full pipeline with output directory
  uv run content-suite --topic "Email marketing" --format all --output-dir ./my_content

  # Quick LinkedIn post
  uv run content-suite --topic "B2B marketing" --format linkedin --audience "B2B sales teams"

  # SEO analysis of a file
  uv run content-suite --analyze-seo ./my_blog_post.md --keyword "content marketing"

  # Generate content calendar
  uv run content-suite --calendar "AI tools,SEO tips,LinkedIn growth" --frequency weekly
        """,
    )

    # Main action
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument(
        "--topic",
        type=str,
        help="Topic to generate content about",
    )
    action_group.add_argument(
        "--analyze-seo",
        type=str,
        metavar="FILE_OR_TEXT",
        help="Analyze SEO for a file or text string",
    )
    action_group.add_argument(
        "--calendar",
        type=str,
        metavar="TOPICS",
        help="Comma-separated topics for content calendar generation",
    )

    # Content options
    parser.add_argument(
        "--format",
        choices=["blog", "twitter", "linkedin", "all"],
        default="all",
        help="Output format (default: all)",
    )
    parser.add_argument(
        "--tone",
        choices=["professional", "casual", "educational", "inspirational", "conversational", "authoritative"],
        default="professional",
        help="Writing tone (default: professional)",
    )
    parser.add_argument(
        "--audience",
        type=str,
        default="marketing professionals",
        help="Target audience description (default: marketing professionals)",
    )
    parser.add_argument(
        "--word-count",
        type=int,
        default=1200,
        metavar="N",
        help="Target blog post word count (default: 1200)",
    )

    # Output options
    parser.add_argument(
        "--output",
        type=str,
        metavar="FILE",
        help="Output file path (auto-named if not specified)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./outputs",
        metavar="DIR",
        help="Output directory for generated files (default: ./outputs)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output results as JSON",
    )

    # Analysis options
    parser.add_argument(
        "--keyword",
        type=str,
        help="Target keyword for SEO analysis",
    )

    # Calendar options
    parser.add_argument(
        "--frequency",
        choices=["daily", "3x_week", "weekly", "biweekly", "monthly"],
        default="weekly",
        help="Calendar posting frequency (default: weekly)",
    )

    # Pipeline options
    parser.add_argument(
        "--no-plagiarism",
        action="store_true",
        help="Skip plagiarism check (faster)",
    )
    parser.add_argument(
        "--no-seo",
        action="store_true",
        help="Skip SEO analysis",
    )

    # Misc
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed pipeline progress",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="content-suite 1.0.0 (UV-powered)",
    )

    return parser


def check_api_keys() -> bool:
    """Verify required API keys are available."""
    missing = []
    if not os.getenv("GROQ_API_KEY"):
        missing.append("GROQ_API_KEY")
    if not os.getenv("GEMINI_API_KEY"):
        missing.append("GEMINI_API_KEY")

    if missing:
        print(f"[UV] ERROR: Missing API keys: {', '.join(missing)}")
        print("[UV] Add them to your .env file:")
        for key in missing:
            print(f"  {key}=your_{key.lower()}_here")
        print("[UV] Get free keys:")
        print("  Groq: https://console.groq.com")
        print("  Gemini: https://aistudio.google.com")
        return False
    return True


def save_outputs(results: dict, output_dir: str, topic: str, formats: list):
    """Save generated content to files."""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # Safe filename from topic
    safe_topic = "".join(c if c.isalnum() or c in "-_ " else "" for c in topic)
    safe_topic = safe_topic.replace(" ", "_")[:40]

    saved_files = []
    content = results.get("content", {})

    if "blog" in formats and "blog_markdown" in content:
        filepath = out_path / f"{safe_topic}_blog.md"
        filepath.write_text(content["blog_markdown"], encoding="utf-8")
        saved_files.append(str(filepath))
        print(f"[UV] 📄 Blog post saved: {filepath}")

    if "blog" in formats and "blog_html" in content:
        filepath = out_path / f"{safe_topic}_blog.html"
        filepath.write_text(content["blog_html"], encoding="utf-8")
        saved_files.append(str(filepath))
        print(f"[UV] 🌐 Blog HTML saved: {filepath}")

    if "twitter" in formats and "twitter" in content:
        filepath = out_path / f"{safe_topic}_twitter.txt"
        filepath.write_text(content["twitter"], encoding="utf-8")
        saved_files.append(str(filepath))
        print(f"[UV] 🐦 Twitter thread saved: {filepath}")

    if "linkedin" in formats and "linkedin" in content:
        filepath = out_path / f"{safe_topic}_linkedin.txt"
        filepath.write_text(content["linkedin"], encoding="utf-8")
        saved_files.append(str(filepath))
        print(f"[UV] 💼 LinkedIn post saved: {filepath}")

    # Save full JSON report
    report_path = out_path / f"{safe_topic}_report.json"
    report_data = {
        "topic": results.get("topic"),
        "elapsed_seconds": results.get("elapsed_seconds"),
        "seo": results.get("seo", {}),
        "engagement": results.get("engagement", {}),
        "plagiarism": results.get("plagiarism", {}),
        "pipeline_stages": results.get("pipeline_stages", []),
    }
    report_path.write_text(json.dumps(report_data, indent=2), encoding="utf-8")
    saved_files.append(str(report_path))
    print(f"[UV] 📊 Report saved: {report_path}")

    return saved_files


def cmd_generate(args: argparse.Namespace):
    """Handle content generation command."""
    if not check_api_keys():
        sys.exit(1)

    topic = args.topic
    formats_map = {
        "blog": ["blog"],
        "twitter": ["twitter"],
        "linkedin": ["linkedin"],
        "all": ["blog", "twitter", "linkedin"],
    }
    formats = formats_map.get(args.format, ["blog", "twitter", "linkedin"])

    print(f"\n[UV] 🚀 Content Marketing Suite v1.0.0")
    print(f"[UV] Topic: {topic}")
    print(f"[UV] Formats: {', '.join(formats)}")
    print(f"[UV] Tone: {args.tone} | Audience: {args.audience}")
    print("[UV] " + "─" * 50)

    def progress(msg: str, pct: int):
        if args.verbose:
            print(f"[UV] [{pct:3d}%] {msg}")
        else:
            bar_width = 30
            filled = int(bar_width * pct / 100)
            bar = "█" * filled + "░" * (bar_width - filled)
            print(f"\r[UV] [{bar}] {pct:3d}% {msg[:40]:<40}", end="", flush=True)

    try:
        from agents.tasks import ContentPipeline
        pipeline = ContentPipeline(progress_callback=progress)

        results = pipeline.run(
            topic=topic,
            tone=args.tone,
            target_audience=args.audience,
            word_count=args.word_count,
            formats=formats,
            check_plagiarism=not args.no_plagiarism,
        )

        print(f"\n[UV] " + "─" * 50)
        print(f"[UV] ✅ Pipeline complete in {results.get('elapsed_seconds', 0)}s")

        # Print summary
        seo = results.get("seo", {})
        if seo.get("score"):
            print(f"[UV] 📊 SEO Score: {seo['score']}/100 ({seo.get('grade', '')})")

        engagement = results.get("engagement", {})
        blog_eng = engagement.get("blog", {})
        if blog_eng.get("overall_score"):
            print(f"[UV] 💡 Blog Engagement: {blog_eng['overall_score']}/100 ({blog_eng.get('predicted_performance', '')})")

        plagiarism = results.get("plagiarism", {})
        if plagiarism.get("originality_score"):
            print(f"[UV] 🔎 Originality: {plagiarism['originality_score']}%")

        # Output
        if args.json_output:
            print(json.dumps(results, indent=2, default=str))
        else:
            saved = save_outputs(results, args.output_dir, topic, formats)
            print(f"\n[UV] 📁 Files saved to: {args.output_dir}/")

        return results

    except KeyboardInterrupt:
        print("\n[UV] Generation cancelled.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[UV] ERROR: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def cmd_analyze_seo(args: argparse.Namespace):
    """Handle SEO analysis command."""
    input_path = Path(args.analyze_seo)

    if input_path.exists():
        content = input_path.read_text(encoding="utf-8")
        print(f"[UV] Analyzing: {input_path}")
    else:
        content = args.analyze_seo
        print("[UV] Analyzing provided text")

    if len(content) < 50:
        print("[UV] ERROR: Content too short for SEO analysis (need 50+ characters)")
        sys.exit(1)

    keyword = args.keyword or args.topic or "content marketing"
    print(f"[UV] Target keyword: {keyword}")

    try:
        from agents.seo_specialist import SEOSpecialistAgent
        seo = SEOSpecialistAgent()
        result = seo.analyze(content, keyword)

        if args.json_output:
            print(json.dumps(result, indent=2, default=str))
        else:
            print(f"\n[UV] SEO Analysis Results")
            print(f"[UV] " + "─" * 40)
            print(f"[UV] Score: {result.get('score', 0)}/100 (Grade: {result.get('grade', 'N/A')})")
            print(f"[UV] Words: {result.get('word_count', 0)}")

            readability = result.get("readability", {})
            print(f"[UV] Reading Ease: {readability.get('reading_ease', 0)} ({readability.get('interpretation', '')})")

            print(f"\n[UV] Top Keywords:")
            for kw in result.get("keywords", [])[:5]:
                print(f"  • {kw}")

            print(f"\n[UV] Recommendations:")
            for rec in result.get("recommendations", []):
                print(f"  {rec}")

    except Exception as e:
        print(f"[UV] ERROR: SEO analysis failed: {e}")
        sys.exit(1)


def cmd_calendar(args: argparse.Namespace):
    """Handle calendar generation command."""
    topics = [t.strip() for t in args.calendar.split(",") if t.strip()]

    if not topics:
        print("[UV] ERROR: No topics provided for calendar")
        sys.exit(1)

    print(f"[UV] Generating content calendar for {len(topics)} topics")
    print(f"[UV] Frequency: {args.frequency}")

    try:
        from utils.calendar_export import CalendarExporter
        exporter = CalendarExporter()

        import datetime
        entries = exporter.generate_calendar(
            topics=topics,
            start_date=datetime.date.today(),
            frequency=args.frequency,
        )

        out_path = Path(args.output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        today_str = datetime.date.today().isoformat()

        # Save CSV
        csv_data = exporter.export_csv(entries)
        csv_file = out_path / f"content_calendar_{today_str}.csv"
        csv_file.write_text(csv_data, encoding="utf-8")
        print(f"[UV] 📅 CSV saved: {csv_file}")

        # Save ICS
        ics_data = exporter.export_ics(entries, "Content Marketing Calendar")
        ics_file = out_path / f"content_calendar_{today_str}.ics"
        ics_file.write_text(ics_data, encoding="utf-8")
        print(f"[UV] 📅 ICS saved: {ics_file}")

        summary = exporter.get_calendar_summary(entries)
        print(f"\n[UV] Calendar Summary:")
        print(f"  Total posts: {summary.get('total_entries', 0)}")
        print(f"  Date range: {summary.get('date_range', {}).get('start', '')} to {summary.get('date_range', {}).get('end', '')}")
        print(f"  Platforms: {', '.join(summary.get('platforms', {}).keys())}")

    except Exception as e:
        print(f"[UV] ERROR: Calendar generation failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def main():
    """Main CLI entry point — called by `uv run content-suite`."""
    parser = create_parser()
    args = parser.parse_args()

    if args.topic:
        cmd_generate(args)
    elif args.analyze_seo:
        cmd_analyze_seo(args)
    elif args.calendar:
        cmd_calendar(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
