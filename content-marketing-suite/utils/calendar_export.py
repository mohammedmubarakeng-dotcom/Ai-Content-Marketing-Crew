# Cursor-compatible + UV-ready
# Run: uv run python utils/calendar_export.py
"""
Content Calendar Export - Generates CSV and ICS calendar files.
No API required — pure data formatting.
"""

import csv
import io
import uuid
from datetime import datetime, date, timedelta
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class CalendarExporter:
    """
    Exports content calendars in multiple formats:
    - CSV (for Excel/Google Sheets)
    - ICS (for Google Calendar, Outlook, Apple Calendar)
    """

    PLATFORMS = ["Blog", "Twitter/X", "LinkedIn", "Instagram", "Facebook", "Email Newsletter"]
    CONTENT_TYPES = ["Blog Post", "Twitter Thread", "LinkedIn Article", "Social Post", "Video Script", "Email"]
    STATUSES = ["Planned", "In Progress", "Review", "Scheduled", "Published"]

    def generate_calendar(
        self,
        topics: list,
        start_date: Optional[date] = None,
        frequency: str = "weekly",
        platforms: Optional[list] = None,
    ) -> list:
        """
        Generate a content calendar schedule.

        Args:
            topics: List of content topics (strings or dicts with topic/platform/type)
            start_date: Calendar start date (default: today)
            frequency: Posting frequency ('daily', 'weekly', 'biweekly')
            platforms: List of platforms to schedule (default: all)

        Returns:
            list of content calendar entries as dicts
        """
        if start_date is None:
            start_date = date.today()
        
        if platforms is None:
            platforms = self.PLATFORMS[:3]  # Blog, Twitter, LinkedIn by default
        
        # Determine interval between posts
        intervals = {
            "daily": 1,
            "3x_week": 2,
            "weekly": 7,
            "biweekly": 14,
            "monthly": 30,
        }
        interval = intervals.get(frequency, 7)
        
        calendar_entries = []
        current_date = start_date
        
        for i, topic_item in enumerate(topics):
            # Handle both string and dict topics
            if isinstance(topic_item, str):
                topic = topic_item
                platform = platforms[i % len(platforms)]
                content_type = self._infer_content_type(platform)
            elif isinstance(topic_item, dict):
                topic = topic_item.get("topic", f"Content #{i+1}")
                platform = topic_item.get("platform", platforms[i % len(platforms)])
                content_type = topic_item.get("type", self._infer_content_type(platform))
            else:
                continue
            
            entry = {
                "id": str(uuid.uuid4())[:8],
                "date": current_date.isoformat(),
                "day_of_week": current_date.strftime("%A"),
                "topic": topic,
                "platform": platform,
                "content_type": content_type,
                "status": "Planned",
                "author": "",
                "notes": "",
                "target_keywords": "",
                "cta": "",
                "published_url": "",
            }
            
            calendar_entries.append(entry)
            current_date += timedelta(days=interval)
        
        return calendar_entries

    def generate_monthly_calendar(
        self,
        topics: list,
        month: Optional[int] = None,
        year: Optional[int] = None,
        posts_per_week: int = 3,
    ) -> list:
        """
        Generate a full month content calendar.

        Args:
            topics: List of topics to distribute
            month: Month number (1-12, default: current month)
            year: Year (default: current year)
            posts_per_week: How many posts per week

        Returns:
            list of calendar entries for the full month
        """
        today = date.today()
        month = month or today.month
        year = year or today.year
        
        # Get all weekdays in the month
        first_day = date(year, month, 1)
        if month == 12:
            last_day = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = date(year, month + 1, 1) - timedelta(days=1)
        
        # Pick posting days based on frequency
        if posts_per_week >= 5:
            posting_days = [0, 1, 2, 3, 4]  # Mon-Fri
        elif posts_per_week == 3:
            posting_days = [0, 2, 4]  # Mon, Wed, Fri
        elif posts_per_week == 2:
            posting_days = [1, 4]  # Tue, Thu
        else:
            posting_days = [1]  # Tuesday only
        
        scheduled_dates = []
        current = first_day
        while current <= last_day:
            if current.weekday() in posting_days:
                scheduled_dates.append(current)
            current += timedelta(days=1)
        
        # Match topics to dates
        platforms_cycle = [
            "Blog", "Twitter/X", "LinkedIn",
            "Twitter/X", "LinkedIn", "Instagram"
        ]
        
        calendar_entries = []
        for i, publish_date in enumerate(scheduled_dates):
            topic = topics[i % len(topics)] if topics else f"Content Topic #{i+1}"
            platform = platforms_cycle[i % len(platforms_cycle)]
            
            entry = {
                "id": str(uuid.uuid4())[:8],
                "date": publish_date.isoformat(),
                "day_of_week": publish_date.strftime("%A"),
                "topic": topic if isinstance(topic, str) else topic.get("topic", ""),
                "platform": platform,
                "content_type": self._infer_content_type(platform),
                "status": "Planned",
                "week_number": publish_date.isocalendar()[1],
                "author": "",
                "notes": "",
                "target_keywords": "",
                "cta": "",
                "published_url": "",
            }
            calendar_entries.append(entry)
        
        return calendar_entries

    def export_csv(self, entries: list) -> str:
        """
        Export calendar entries as CSV string.

        Args:
            entries: List of calendar entry dicts

        Returns:
            str: CSV content (can be written to file or downloaded)
        """
        if not entries:
            return ""
        
        output = io.StringIO()
        
        fieldnames = [
            "id", "date", "day_of_week", "topic", "platform",
            "content_type", "status", "author", "notes",
            "target_keywords", "cta", "published_url"
        ]
        
        # Only include fields that exist in entries
        actual_fields = [f for f in fieldnames if f in entries[0]]
        
        writer = csv.DictWriter(
            output,
            fieldnames=actual_fields,
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(entries)
        
        return output.getvalue()

    def export_ics(self, entries: list, calendar_name: str = "Content Calendar") -> str:
        """
        Export calendar entries as ICS (iCalendar) format.
        
        Compatible with: Google Calendar, Outlook, Apple Calendar.

        Args:
            entries: List of calendar entry dicts
            calendar_name: Name for the calendar

        Returns:
            str: ICS calendar content
        """
        try:
            from ics import Calendar, Event
            
            cal = Calendar()
            cal.creator = "Content Marketing Suite"
            
            for entry in entries:
                event = Event()
                
                # Set event name
                topic = entry.get("topic", "Content")
                platform = entry.get("platform", "")
                event.name = f"[{platform}] {topic}" if platform else topic
                
                # Set date
                date_str = entry.get("date", "")
                if date_str:
                    try:
                        event_date = datetime.fromisoformat(date_str)
                        event.begin = event_date.replace(hour=9, minute=0)
                        event.make_all_day()
                    except ValueError:
                        continue
                
                # Set description
                desc_parts = [
                    f"Topic: {entry.get('topic', '')}",
                    f"Platform: {entry.get('platform', '')}",
                    f"Content Type: {entry.get('content_type', '')}",
                    f"Status: {entry.get('status', 'Planned')}",
                ]
                if entry.get("notes"):
                    desc_parts.append(f"Notes: {entry['notes']}")
                if entry.get("target_keywords"):
                    desc_parts.append(f"Keywords: {entry['target_keywords']}")
                
                event.description = "\n".join(desc_parts)
                event.uid = entry.get("id", str(uuid.uuid4()))
                
                cal.events.add(event)
            
            return str(cal)
        
        except ImportError:
            # Fallback: manual ICS generation
            return self._manual_ics(entries, calendar_name)

    def _manual_ics(self, entries: list, calendar_name: str) -> str:
        """Manual ICS generation if ics library not available."""
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Content Marketing Suite//EN",
            f"X-WR-CALNAME:{calendar_name}",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
        ]
        
        for entry in entries:
            date_str = entry.get("date", "")
            if not date_str:
                continue
            
            try:
                event_date = datetime.fromisoformat(date_str)
                date_formatted = event_date.strftime("%Y%m%d")
            except ValueError:
                continue
            
            topic = entry.get("topic", "Content")
            platform = entry.get("platform", "")
            uid = entry.get("id", str(uuid.uuid4()))
            now = datetime.now().strftime("%Y%m%dT%H%M%SZ")
            
            lines += [
                "BEGIN:VEVENT",
                f"UID:{uid}@content-marketing-suite",
                f"DTSTAMP:{now}",
                f"DTSTART;VALUE=DATE:{date_formatted}",
                f"DTEND;VALUE=DATE:{date_formatted}",
                f"SUMMARY:[{platform}] {topic}",
                f"DESCRIPTION:Platform: {platform}\\nType: {entry.get('content_type', '')}\\nStatus: {entry.get('status', 'Planned')}",
                "END:VEVENT",
            ]
        
        lines.append("END:VCALENDAR")
        return "\n".join(lines)

    def _infer_content_type(self, platform: str) -> str:
        """Infer content type from platform name."""
        mapping = {
            "Blog": "Blog Post",
            "Twitter/X": "Twitter Thread",
            "LinkedIn": "LinkedIn Article",
            "Instagram": "Social Post",
            "Facebook": "Social Post",
            "Email Newsletter": "Email",
        }
        return mapping.get(platform, "Content")

    def get_calendar_summary(self, entries: list) -> dict:
        """Get summary statistics for a content calendar."""
        if not entries:
            return {}
        
        platforms = {}
        content_types = {}
        statuses = {}
        
        for entry in entries:
            p = entry.get("platform", "Unknown")
            t = entry.get("content_type", "Unknown")
            s = entry.get("status", "Unknown")
            
            platforms[p] = platforms.get(p, 0) + 1
            content_types[t] = content_types.get(t, 0) + 1
            statuses[s] = statuses.get(s, 0) + 1
        
        dates = [entry.get("date", "") for entry in entries if entry.get("date")]
        
        return {
            "total_entries": len(entries),
            "platforms": platforms,
            "content_types": content_types,
            "statuses": statuses,
            "date_range": {
                "start": min(dates) if dates else "",
                "end": max(dates) if dates else "",
            },
        }


if __name__ == "__main__":
    exporter = CalendarExporter()
    
    topics = [
        "AI marketing trends 2025",
        "How to write viral blog posts",
        "LinkedIn content strategy guide",
        "SEO fundamentals for beginners",
        "Content repurposing tactics",
        "Email marketing automation tips",
    ]
    
    entries = exporter.generate_calendar(
        topics=topics,
        frequency="weekly",
        platforms=["Blog", "Twitter/X", "LinkedIn"],
    )
    
    print(f"[UV] Generated {len(entries)} calendar entries")
    
    csv_output = exporter.export_csv(entries)
    print(f"[UV] CSV output ({len(csv_output)} chars):")
    print(csv_output[:500])
    
    ics_output = exporter.export_ics(entries)
    print(f"\n[UV] ICS output ({len(ics_output)} chars)")
    
    summary = exporter.get_calendar_summary(entries)
    print(f"\n[UV] Summary: {summary}")
