# Cursor-compatible + UV-ready
# Run: uv run streamlit run app.py
"""
Content Marketing Suite - Streamlit Dashboard
4 tabs: Generate | SEO Analysis | Content Calendar | Settings
"""

import os
import json
import time
import datetime
from dotenv import load_dotenv

load_dotenv()

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# ─── Page Configuration ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="Content Marketing Suite",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Main theme */
    :root {
        --primary: #6366f1;
        --primary-dark: #4f46e5;
        --success: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;
        --surface: #1e1e2e;
        --text: #e2e8f0;
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
        border: 1px solid #3d3d5c;
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    /* Score badge */
    .score-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.9rem;
    }
    .score-a { background: #065f46; color: #6ee7b7; }
    .score-b { background: #1e3a5f; color: #93c5fd; }
    .score-c { background: #713f12; color: #fde68a; }
    .score-f { background: #7f1d1d; color: #fca5a5; }
    
    /* Content output area */
    .content-preview {
        background: #0f0f1a;
        border: 1px solid #2d2d44;
        border-radius: 8px;
        padding: 1.5rem;
        font-family: 'Georgia', serif;
        line-height: 1.8;
    }
    
    /* Platform tag */
    .platform-tag {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        margin: 2px;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: #0f0f1a;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab"] {
        font-size: 1rem;
        padding: 0.75rem 1.5rem;
    }
    
    /* Pipeline stage indicator */
    .stage-indicator {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px 0;
        font-size: 0.9rem;
    }
    
    .rec-item {
        background: #1a1a2e;
        border-left: 3px solid #6366f1;
        padding: 8px 12px;
        margin: 6px 0;
        border-radius: 0 6px 6px 0;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)


# ─── Session State Init ───────────────────────────────────────────────────────
def init_session_state():
    defaults = {
        "pipeline_results": None,
        "calendar_entries": [],
        "generated_topic": "",
        "active_tab": 0,
        "generation_log": [],
        "settings": {
            "groq_api_key": os.getenv("GROQ_API_KEY", ""),
            "gemini_api_key": os.getenv("GEMINI_API_KEY", ""),
            "default_tone": "professional",
            "default_audience": "marketing professionals",
            "default_word_count": 1200,
            "enable_plagiarism": True,
            "wordpress_url": os.getenv("WORDPRESS_URL", ""),
            "wordpress_user": os.getenv("WORDPRESS_USERNAME", ""),
            "wordpress_pass": os.getenv("WORDPRESS_APP_PASSWORD", ""),
            "buffer_token": os.getenv("BUFFER_ACCESS_TOKEN", ""),
        },
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()


# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🚀 Content Suite")
    st.markdown("---")

    # API Status
    groq_ok = bool(st.session_state.settings.get("groq_api_key"))
    gemini_ok = bool(st.session_state.settings.get("gemini_api_key"))

    st.markdown("**API Status**")
    st.markdown(
        f"{'🟢' if groq_ok else '🔴'} Groq {'Connected' if groq_ok else 'Not configured'}"
    )
    st.markdown(
        f"{'🟢' if gemini_ok else '🔴'} Gemini {'Connected' if gemini_ok else 'Not configured'}"
    )

    if not (groq_ok and gemini_ok):
        st.warning("⚙️ Add API keys in the Settings tab")
        st.markdown("[Get Groq key →](https://console.groq.com)")
        st.markdown("[Get Gemini key →](https://aistudio.google.com)")

    st.markdown("---")

    if st.session_state.pipeline_results:
        results = st.session_state.pipeline_results
        seo = results.get("seo", {})
        engagement = results.get("engagement", {})

        st.markdown("**Last Run Stats**")
        if seo.get("score"):
            st.metric("SEO Score", f"{seo['score']}/100", f"{seo.get('grade', '')}")
        blog_eng = engagement.get("blog", {})
        if blog_eng.get("overall_score"):
            st.metric("Blog Engagement", f"{blog_eng['overall_score']}/100")
        elapsed = results.get("elapsed_seconds", 0)
        st.metric("Generation Time", f"{elapsed}s")

    st.markdown("---")
    st.markdown("**Quick Actions**")
    if st.button("🗑️ Clear Results", use_container_width=True):
        st.session_state.pipeline_results = None
        st.rerun()
    if st.button("📅 View Calendar", use_container_width=True):
        st.session_state.active_tab = 2
        st.rerun()


# ─── Main Content Area ────────────────────────────────────────────────────────
st.title("🚀 Automated Content Marketing Suite")
st.caption("Powered by Groq + Gemini | Free AI APIs | CrewAI-style Pipeline")

tab1, tab2, tab3, tab4 = st.tabs(
    ["✍️ Generate", "🔍 SEO Analysis", "📅 Content Calendar", "⚙️ Settings"]
)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1: GENERATE
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.markdown("### 📝 Content Configuration")

        topic = st.text_input(
            "Content Topic",
            placeholder="e.g., Top 5 AI marketing trends 2025",
            value=st.session_state.generated_topic,
            help="The main topic you want to create content about",
        )

        tone = st.selectbox(
            "Writing Tone",
            ["professional", "casual", "educational", "inspirational", "conversational", "authoritative"],
            index=["professional", "casual", "educational", "inspirational", "conversational", "authoritative"].index(
                st.session_state.settings.get("default_tone", "professional")
            ),
        )

        target_audience = st.text_input(
            "Target Audience",
            value=st.session_state.settings.get("default_audience", "marketing professionals"),
            placeholder="e.g., small business owners, SaaS founders",
        )

        word_count = st.slider(
            "Blog Post Word Count",
            min_value=500,
            max_value=3000,
            value=st.session_state.settings.get("default_word_count", 1200),
            step=100,
        )

        st.markdown("**Output Formats**")
        col_f1, col_f2, col_f3 = st.columns(3)
        gen_blog = col_f1.checkbox("Blog Post", value=True)
        gen_twitter = col_f2.checkbox("Twitter Thread", value=True)
        gen_linkedin = col_f3.checkbox("LinkedIn Post", value=True)

        check_plagiarism = st.checkbox(
            "Run Plagiarism Check",
            value=st.session_state.settings.get("enable_plagiarism", True),
            help="Uses sentence-transformers (requires download on first run)",
        )

        st.markdown("---")

        formats = []
        if gen_blog:
            formats.append("blog")
        if gen_twitter:
            formats.append("twitter")
        if gen_linkedin:
            formats.append("linkedin")

        api_ready = groq_ok and gemini_ok
        generate_btn = st.button(
            "🚀 Generate Content",
            type="primary",
            use_container_width=True,
            disabled=not (topic and api_ready),
        )
        if not api_ready:
            st.error("⚠️ Configure API keys in Settings tab first")
        elif not topic:
            st.info("Enter a topic above to get started")

    with col_right:
        if generate_btn and topic:
            st.session_state.generated_topic = topic

            # Set API keys from settings
            os.environ["GROQ_API_KEY"] = st.session_state.settings.get("groq_api_key", "")
            os.environ["GEMINI_API_KEY"] = st.session_state.settings.get("gemini_api_key", "")

            progress_bar = st.progress(0)
            status_text = st.empty()
            log_container = st.empty()
            log_lines = []

            def update_progress(msg: str, pct: int):
                progress_bar.progress(pct / 100)
                status_text.markdown(f"**{msg}**")
                log_lines.append(f"[{pct:3d}%] {msg}")
                log_container.code("\n".join(log_lines[-8:]), language=None)

            try:
                from agents.tasks import ContentPipeline
                pipeline = ContentPipeline(progress_callback=update_progress)

                results = pipeline.run(
                    topic=topic,
                    tone=tone,
                    target_audience=target_audience,
                    word_count=word_count,
                    formats=formats,
                    check_plagiarism=check_plagiarism,
                )

                st.session_state.pipeline_results = results
                progress_bar.progress(1.0)
                status_text.markdown("✅ **Generation complete!**")
                log_container.empty()
                st.success(f"✅ Content generated in {results.get('elapsed_seconds', 0)}s!")
                st.rerun()

            except Exception as e:
                st.error(f"[ERROR] Pipeline failed: {e}")
                st.exception(e)

        # Display results
        if st.session_state.pipeline_results:
            results = st.session_state.pipeline_results
            content = results.get("content", {})
            seo = results.get("seo", {})
            engagement = results.get("engagement", {})
            plagiarism = results.get("plagiarism", {})

            # Quick metrics row
            m1, m2, m3, m4 = st.columns(4)
            m1.metric(
                "SEO Score",
                f"{seo.get('score', 0)}/100",
                seo.get("grade", ""),
            )
            blog_engagement = engagement.get("blog", {})
            m2.metric(
                "Engagement",
                f"{blog_engagement.get('overall_score', 0)}/100",
                blog_engagement.get("grade", ""),
            )
            m3.metric(
                "Word Count",
                seo.get("word_count", len(content.get("blog_markdown", "").split())),
            )
            m4.metric(
                "Originality",
                f"{plagiarism.get('originality_score', 95)}%",
                plagiarism.get("status", ""),
            )

            st.markdown("---")

            # Content tabs
            content_tabs = []
            content_tab_labels = []
            if "blog_markdown" in content:
                content_tab_labels.append("📄 Blog Post")
            if "twitter" in content:
                content_tab_labels.append("🐦 Twitter Thread")
            if "linkedin" in content:
                content_tab_labels.append("💼 LinkedIn Post")
            if content_tab_labels:
                content_tabs = st.tabs(content_tab_labels)

            tab_idx = 0

            if "blog_markdown" in content and tab_idx < len(content_tabs):
                with content_tabs[tab_idx]:
                    tab_idx += 1
                    blog_md = content["blog_markdown"]
                    st.markdown(blog_md)
                    st.download_button(
                        "⬇️ Download Markdown",
                        data=blog_md,
                        file_name=f"blog_{topic[:30].replace(' ', '_')}.md",
                        mime="text/markdown",
                        use_container_width=True,
                    )
                    if "blog_html" in content:
                        st.download_button(
                            "⬇️ Download HTML",
                            data=content["blog_html"],
                            file_name=f"blog_{topic[:30].replace(' ', '_')}.html",
                            mime="text/html",
                            use_container_width=True,
                        )

            if "twitter" in content and tab_idx < len(content_tabs):
                with content_tabs[tab_idx]:
                    tab_idx += 1
                    twitter_content = content["twitter"]
                    st.text_area(
                        "Twitter Thread",
                        value=twitter_content,
                        height=400,
                        label_visibility="collapsed",
                    )
                    tw_engagement = engagement.get("twitter", {})
                    if tw_engagement:
                        st.info(
                            f"Engagement Prediction: **{tw_engagement.get('overall_score', 0)}/100** "
                            f"({tw_engagement.get('predicted_performance', '')})"
                        )
                    st.download_button(
                        "⬇️ Download Thread",
                        data=twitter_content,
                        file_name=f"twitter_{topic[:30].replace(' ', '_')}.txt",
                        mime="text/plain",
                        use_container_width=True,
                    )

            if "linkedin" in content and tab_idx < len(content_tabs):
                with content_tabs[tab_idx]:
                    tab_idx += 1
                    linkedin_content = content["linkedin"]
                    st.text_area(
                        "LinkedIn Post",
                        value=linkedin_content,
                        height=350,
                        label_visibility="collapsed",
                    )
                    li_engagement = engagement.get("linkedin", {})
                    if li_engagement:
                        st.info(
                            f"Engagement Prediction: **{li_engagement.get('overall_score', 0)}/100** "
                            f"({li_engagement.get('predicted_performance', '')})"
                        )
                    st.download_button(
                        "⬇️ Download Post",
                        data=linkedin_content,
                        file_name=f"linkedin_{topic[:30].replace(' ', '_')}.txt",
                        mime="text/plain",
                        use_container_width=True,
                    )

            # SEO Recommendations
            if seo.get("recommendations"):
                with st.expander("🔍 SEO Recommendations", expanded=False):
                    for rec in seo["recommendations"]:
                        st.markdown(
                            f'<div class="rec-item">{rec}</div>',
                            unsafe_allow_html=True,
                        )

            # Plagiarism details
            if plagiarism.get("common_phrases"):
                with st.expander(f"⚠️ Cliché Phrases Detected ({len(plagiarism['common_phrases'])})", expanded=False):
                    for phrase in plagiarism["common_phrases"]:
                        st.markdown(f"- `{phrase}`")
                    st.caption("Consider replacing these overused phrases with more original language.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2: SEO ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### 🔍 SEO Analysis")
    st.caption("Paste any content for a detailed SEO audit (no API required)")

    col_seo1, col_seo2 = st.columns([1, 1])

    with col_seo1:
        seo_topic = st.text_input(
            "Target Keyword / Topic",
            placeholder="e.g., content marketing strategy",
            key="seo_topic_input",
        )

        # Pre-fill from generated content if available
        default_seo_text = ""
        if st.session_state.pipeline_results:
            default_seo_text = st.session_state.pipeline_results.get(
                "content", {}
            ).get("blog_markdown", "")[:3000]

        seo_content = st.text_area(
            "Content to Analyze",
            value=default_seo_text,
            height=300,
            placeholder="Paste your blog post, article, or any content here...",
            key="seo_content_input",
        )

        analyze_btn = st.button(
            "🔍 Analyze SEO",
            type="primary",
            use_container_width=True,
            disabled=not (seo_content and seo_topic),
        )

    with col_seo2:
        if analyze_btn and seo_content and seo_topic:
            with st.spinner("Analyzing SEO..."):
                try:
                    from agents.seo_specialist import SEOSpecialistAgent
                    seo_agent = SEOSpecialistAgent()
                    seo_result = seo_agent.analyze(seo_content, seo_topic)

                    # Score gauge chart
                    score = seo_result.get("score", 0)
                    grade = seo_result.get("grade", "N/A")

                    fig = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=score,
                        domain={"x": [0, 1], "y": [0, 1]},
                        title={"text": f"SEO Score — Grade {grade}", "font": {"size": 16}},
                        gauge={
                            "axis": {"range": [0, 100]},
                            "bar": {"color": "#6366f1"},
                            "steps": [
                                {"range": [0, 50], "color": "#7f1d1d"},
                                {"range": [50, 70], "color": "#713f12"},
                                {"range": [70, 90], "color": "#1e3a5f"},
                                {"range": [90, 100], "color": "#065f46"},
                            ],
                            "threshold": {
                                "line": {"color": "white", "width": 3},
                                "thickness": 0.75,
                                "value": score,
                            },
                        },
                    ))
                    fig.update_layout(
                        height=250,
                        margin=dict(l=20, r=20, t=40, b=20),
                        paper_bgcolor="rgba(0,0,0,0)",
                        font_color="white",
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # Metrics
                    c1, c2, c3 = st.columns(3)
                    readability = seo_result.get("readability", {})
                    c1.metric("Reading Ease", readability.get("reading_ease", "N/A"))
                    c2.metric("Grade Level", readability.get("grade_level", "N/A"))
                    c3.metric("Word Count", seo_result.get("word_count", 0))

                    c4, c5, c6 = st.columns(3)
                    density = seo_result.get("keyword_density", {})
                    c4.metric("Keyword Density", f"{density.get('density', 0)}%")
                    c5.metric("H2 Headings", seo_result.get("structure", {}).get("h2_count", 0))
                    c6.metric("Bullet Points", seo_result.get("structure", {}).get("bullet_points", 0))

                    # Keywords extracted
                    kws = seo_result.get("keywords", [])
                    if kws:
                        st.markdown("**🔑 Extracted Keywords**")
                        kw_str = " • ".join([f"`{k}`" for k in kws[:12]])
                        st.markdown(kw_str)

                    # Meta description
                    meta = seo_result.get("meta_description", "")
                    if meta:
                        st.markdown("**📝 Meta Description**")
                        char_count = len(meta)
                        color = "🟢" if 120 <= char_count <= 160 else "🟡"
                        st.info(f"{color} ({char_count} chars): {meta}")

                    # Recommendations
                    recs = seo_result.get("recommendations", [])
                    if recs:
                        st.markdown("**📋 Recommendations**")
                        for rec in recs:
                            st.markdown(
                                f'<div class="rec-item">{rec}</div>',
                                unsafe_allow_html=True,
                            )

                    # Suggested title
                    suggested_title = seo_result.get("optimized_title", "")
                    if suggested_title:
                        st.markdown("**✨ Suggested SEO Title**")
                        st.code(suggested_title)

                except Exception as e:
                    st.error(f"[ERROR] SEO analysis failed: {e}")

        elif not (seo_content and seo_topic):
            st.info("👈 Enter a topic and paste content to begin analysis")

            # Show sample SEO metrics if we have pipeline results
            if st.session_state.pipeline_results:
                seo_data = st.session_state.pipeline_results.get("seo", {})
                if seo_data and seo_data.get("score"):
                    st.markdown("**Last Generated Content SEO Summary:**")
                    score = seo_data.get("score", 0)
                    st.metric("Overall SEO Score", f"{score}/100 ({seo_data.get('grade', '')})")
                    for rec in seo_data.get("recommendations", [])[:3]:
                        st.markdown(f"- {rec}")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3: CONTENT CALENDAR
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### 📅 Content Calendar")

    col_cal1, col_cal2 = st.columns([1, 2])

    with col_cal1:
        st.markdown("**Generate Calendar**")

        topics_raw = st.text_area(
            "Topics (one per line)",
            height=200,
            placeholder="AI marketing trends 2025\nContent repurposing tips\nSEO basics for beginners\nLinkedIn growth strategy\nEmail marketing automation",
            help="Enter one topic per line",
        )

        cal_frequency = st.selectbox(
            "Posting Frequency",
            ["weekly", "daily", "3x_week", "biweekly", "monthly"],
            index=0,
        )

        start_date = st.date_input(
            "Start Date",
            value=datetime.date.today(),
        )

        cal_platforms = st.multiselect(
            "Platforms",
            ["Blog", "Twitter/X", "LinkedIn", "Instagram", "Facebook", "Email Newsletter"],
            default=["Blog", "Twitter/X", "LinkedIn"],
        )

        gen_cal_btn = st.button(
            "📅 Generate Calendar",
            type="primary",
            use_container_width=True,
            disabled=not topics_raw,
        )

    with col_cal2:
        if gen_cal_btn and topics_raw:
            with st.spinner("Building content calendar..."):
                try:
                    from utils.calendar_export import CalendarExporter
                    exporter = CalendarExporter()

                    topics_list = [t.strip() for t in topics_raw.strip().split("\n") if t.strip()]

                    entries = exporter.generate_calendar(
                        topics=topics_list,
                        start_date=start_date,
                        frequency=cal_frequency,
                        platforms=cal_platforms if cal_platforms else None,
                    )

                    st.session_state.calendar_entries = entries
                    st.success(f"✅ Generated {len(entries)} calendar entries!")

                except Exception as e:
                    st.error(f"[ERROR] Calendar generation failed: {e}")

        if st.session_state.calendar_entries:
            entries = st.session_state.calendar_entries

            # Calendar summary
            from utils.calendar_export import CalendarExporter
            exporter = CalendarExporter()
            summary = exporter.get_calendar_summary(entries)

            s1, s2, s3 = st.columns(3)
            s1.metric("Total Posts", summary.get("total_entries", 0))
            date_range = summary.get("date_range", {})
            s2.metric("Start Date", date_range.get("start", "")[:10])
            s3.metric("End Date", date_range.get("end", "")[:10])

            # Platform distribution chart
            platform_data = summary.get("platforms", {})
            if platform_data:
                fig = px.pie(
                    values=list(platform_data.values()),
                    names=list(platform_data.keys()),
                    title="Content by Platform",
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Set3,
                )
                fig.update_layout(
                    height=250,
                    margin=dict(l=0, r=0, t=30, b=0),
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="white",
                    showlegend=True,
                )
                st.plotly_chart(fig, use_container_width=True)

            # Calendar table
            df = pd.DataFrame(entries)
            display_cols = ["date", "day_of_week", "topic", "platform", "content_type", "status"]
            display_cols = [c for c in display_cols if c in df.columns]

            st.dataframe(
                df[display_cols],
                use_container_width=True,
                height=300,
                column_config={
                    "date": st.column_config.DateColumn("Date"),
                    "day_of_week": "Day",
                    "topic": "Topic",
                    "platform": "Platform",
                    "content_type": "Type",
                    "status": st.column_config.SelectboxColumn(
                        "Status",
                        options=["Planned", "In Progress", "Review", "Scheduled", "Published"],
                    ),
                },
            )

            # Export buttons
            col_dl1, col_dl2 = st.columns(2)

            csv_data = exporter.export_csv(entries)
            col_dl1.download_button(
                "⬇️ Download CSV",
                data=csv_data,
                file_name=f"content_calendar_{datetime.date.today()}.csv",
                mime="text/csv",
                use_container_width=True,
            )

            ics_data = exporter.export_ics(entries, "Content Marketing Calendar")
            col_dl2.download_button(
                "⬇️ Download ICS (Calendar)",
                data=ics_data,
                file_name=f"content_calendar_{datetime.date.today()}.ics",
                mime="text/calendar",
                use_container_width=True,
            )

        elif not topics_raw:
            st.info("👈 Enter topics and click Generate Calendar")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4: SETTINGS
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("### ⚙️ Settings & API Configuration")

    col_s1, col_s2 = st.columns(2)

    with col_s1:
        st.markdown("#### 🔑 API Keys (Free Tier)")

        st.markdown(
            "**Groq** ([Get free key →](https://console.groq.com))"
        )
        groq_key = st.text_input(
            "Groq API Key",
            value=st.session_state.settings.get("groq_api_key", ""),
            type="password",
            label_visibility="collapsed",
            placeholder="gsk_...",
        )

        st.markdown(
            "**Google Gemini** ([Get free key →](https://aistudio.google.com))"
        )
        gemini_key = st.text_input(
            "Gemini API Key",
            value=st.session_state.settings.get("gemini_api_key", ""),
            type="password",
            label_visibility="collapsed",
            placeholder="AIza...",
        )

        st.markdown("---")
        st.markdown("#### 🌐 WordPress Integration (Optional)")
        wp_url = st.text_input(
            "WordPress Site URL",
            value=st.session_state.settings.get("wordpress_url", ""),
            placeholder="https://yourblog.com",
        )
        wp_user = st.text_input(
            "WordPress Username",
            value=st.session_state.settings.get("wordpress_user", ""),
        )
        wp_pass = st.text_input(
            "WordPress App Password",
            value=st.session_state.settings.get("wordpress_pass", ""),
            type="password",
            help="Create in WordPress > Users > Application Passwords",
        )

    with col_s2:
        st.markdown("#### 📝 Content Defaults")

        default_tone = st.selectbox(
            "Default Tone",
            ["professional", "casual", "educational", "inspirational", "conversational", "authoritative"],
            index=["professional", "casual", "educational", "inspirational", "conversational", "authoritative"].index(
                st.session_state.settings.get("default_tone", "professional")
            ),
        )

        default_audience = st.text_input(
            "Default Target Audience",
            value=st.session_state.settings.get("default_audience", "marketing professionals"),
        )

        default_word_count = st.slider(
            "Default Blog Word Count",
            min_value=500,
            max_value=3000,
            value=st.session_state.settings.get("default_word_count", 1200),
            step=100,
        )

        enable_plagiarism = st.toggle(
            "Enable Plagiarism Check by Default",
            value=st.session_state.settings.get("enable_plagiarism", True),
            help="First run downloads ~90MB sentence-transformers model",
        )

        st.markdown("---")
        st.markdown("#### 📱 Buffer Integration (Optional)")
        buffer_token = st.text_input(
            "Buffer Access Token",
            value=st.session_state.settings.get("buffer_token", ""),
            type="password",
            help="From buffer.com/developers",
        )

    save_btn = st.button("💾 Save Settings", type="primary", use_container_width=True)

    if save_btn:
        st.session_state.settings.update({
            "groq_api_key": groq_key,
            "gemini_api_key": gemini_key,
            "default_tone": default_tone,
            "default_audience": default_audience,
            "default_word_count": default_word_count,
            "enable_plagiarism": enable_plagiarism,
            "wordpress_url": wp_url,
            "wordpress_user": wp_user,
            "wordpress_pass": wp_pass,
            "buffer_token": buffer_token,
        })

        # Update env vars for current session
        if groq_key:
            os.environ["GROQ_API_KEY"] = groq_key
        if gemini_key:
            os.environ["GEMINI_API_KEY"] = gemini_key

        st.success("✅ Settings saved for this session! (Add to .env for persistence)")
        st.rerun()

    # WordPress Test
    if st.session_state.settings.get("wordpress_url") and st.session_state.settings.get("wordpress_user"):
        st.markdown("---")
        if st.button("🔌 Test WordPress Connection"):
            with st.spinner("Testing WordPress connection..."):
                try:
                    import requests
                    import base64
                    wp_url_test = st.session_state.settings["wordpress_url"].rstrip("/")
                    credentials = base64.b64encode(
                        f"{st.session_state.settings['wordpress_user']}:{st.session_state.settings.get('wordpress_pass', '')}".encode()
                    ).decode()
                    resp = requests.get(
                        f"{wp_url_test}/wp-json/wp/v2/posts?per_page=1",
                        headers={"Authorization": f"Basic {credentials}"},
                        timeout=10,
                    )
                    if resp.status_code == 200:
                        st.success("✅ WordPress connected successfully!")
                    else:
                        st.error(f"❌ WordPress connection failed: {resp.status_code}")
                except Exception as e:
                    st.error(f"❌ Connection error: {e}")

    # System info
    with st.expander("🖥️ System Information"):
        import sys
        st.code(f"""Python: {sys.version.split()[0]}
Streamlit: {st.__version__}
UV-managed: Yes
Working directory: {os.getcwd()}
""")


# ─── Footer ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<center>🚀 Content Marketing Suite | Powered by Groq + Gemini | "
    "Built with UV + Streamlit | Run: <code>uv run streamlit run app.py</code></center>",
    unsafe_allow_html=True,
)
