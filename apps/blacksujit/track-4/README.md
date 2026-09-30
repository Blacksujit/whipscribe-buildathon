# CallCoach-AI x WhipScribe

**Three jobs, one pipeline: coach the call while it happens, read the pattern across calls, and answer any question about what was said - with the quotes to prove it.**

[Live App](https://callcoachai.sujit.top/) · [Demo Video](https://github.com/Blacksujit/whipscribe-buildathon/blob/track-4-coach-pipeline/apps/blacksujit/track-4/videos/demo/callcoach-demo-2026-09-28T15-11-37.webm) (330MB, right-click "Save As")

---

## Spotter, Radar, and Griot

| Pillar | What it is | Where it lives |
|--------|-----------|----------------|
| **Spotter** | Real-time coaching during the call - compliance flags, hedged numbers, and commitments captured the second they are said | `POST /api/spotter`, `src/realtime/analyzer.py` |
| **Radar** | Cross-call deal intelligence - velocity, momentum, recurring issue clusters, action-item lifecycle, speaker risk | `/trends`, `/coach`, `/speakers`, `src/core/compare.py` |
| **Griot** | The grounded companion - a floating chat that answers from your real call library with call + speaker + second citations | `POST /api/ask`, `src/core/companion.py` |

**Why this stands out in Track 4:** every other entry stops at one call. One recording in, one summary, one issue, one proposal out. CallCoach-AI is the only entry that coaches *during* the call (Spotter), reads the pattern *across* calls (Radar), and lets you interrogate the whole library (Griot).

**Grounded, not generated:** Griot answers only from stored evaluations and cites `[Call @ m:ss - Speaker]`; if the evidence does not cover the question, it says so. There is no canned Q&A - the old placeholder assistant page was deleted. Try it live: the chat bubble on every page at [callcoachai.sujit.top](https://callcoachai.sujit.top/).

**No empty dashboard:** the repo ships `seed_evaluations.db`, a real snapshot of eight scored calls (produced through the same pipeline with real WhipScribe transcripts). The app restores it when the working database is empty, so every page has real data on first load. Rebuild it any time with `python scripts/seed_db.py`.

---

## Everything inside (13 capabilities)

### 1. Spotter - Real-Time Coaching During Calls
Live coaching prompts during calls:
- Real-time sentiment analysis
- Live compliance risk detection
- Instant action item extraction
- Live coaching prompts

```python
from src.realtime.analyzer import RealtimeAnalyzer

analyzer = RealtimeAnalyzer()
result = analyzer.add_segment({
    "text": "We'll deliver by Q1",
    "speaker": "Sarah",
    "start": 0,
    "end": 5
})

print(result['coaching_prompts'])
# -> [HIGH] Consider qualifying this commitment.
# -> [LOW] Action item captured.
```

### 2. Post-Call Analysis
Four-agent LLM scoring:
- Compliance, Tension, Clarity, Action Items
- Evidence-backed quotes with timestamps
- Primary risk identification

### 3. Radar - Cross-Call Intelligence
Trend analysis across multiple meetings:
- Deal velocity metrics
- Recurring issue clustering
- Action item lifecycle tracking
- Speaker-level risk scoring

### 4. CRM Integration
Automatic sync to CRM systems:
- Salesforce: tasks, opportunities, coaching notes
- HubSpot: tasks, contacts, engagements

### 5. Follow-Up Emails
Automated email generation:
- Action item summaries
- Compliance risk reports
- Scheduled follow-ups

### 6. Team Benchmarking
Compare reps against each other:
- Team-wide score aggregation
- Rep rankings
- Top performer identification
- Coaching needs assessment

### 7. Custom Rubrics
Define your own scoring criteria:
- Custom category weights
- Multiple rubric support
- Weighted score calculation

### 8. Sentiment Analysis
Track sentiment trends:
- Sentiment by call
- Sentiment by speaker
- Pattern identification

### 9. Coaching Plans
Personalized coaching plans:
- Action items for each weakness
- Timeline with goals
- Success metrics

### 10. Multi-Language Support
Analyze calls in 12 languages:
- English, Spanish, French, German, Italian, Portuguese, Dutch, Japanese, Korean, Chinese, Hindi, Arabic

### 11. Griot - Grounded Companion (the floating chat)
Conversational coaching over your stored evaluations, served by `POST /api/ask`:
- "What did we commit to across calls?"
- "Where do we keep losing points?"
- "How did my last call score?"
- Every answer cites the call, the speaker, and the exact second; if the evidence does not cover it, Griot says so instead of inventing
- No LLM key configured? It degrades to a data-derived summary over the same stored rows (never fabricated quotes)

### 12. Export
Multiple formats:
- Markdown, JSON, Slack, Notion, CSV

### 13. MCP Integration
WhipScribe MCP server:
- List recordings
- Search transcripts
- Manage folders

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run comprehensive demo
python comprehensive_demo.py

# Run test suite
python test_complete.py

# Start real-time coaching server
python -m src.realtime.server

# Start HTTP server
python -m src.realtime.server --http
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CallCoach-AI                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Real-Time  │  │   Post-Call  │  │   Cross-Call │      │
│  │   Coaching   │  │   Analysis   │  │ Intelligence │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │              │
│         └──────────────────┼──────────────────┘              │
│                            │                                 │
│                   ┌────────┴────────┐                        │
│                   │  Coaching Engine │                        │
│                   └────────┬────────┘                        │
│                            │                                 │
│         ┌──────────────────┼──────────────────┐              │
│         │                  │                  │              │
│  ┌──────┴──────┐  ┌───────┴───────┐  ┌──────┴──────┐       │
│  │     CRM     │  │  Follow-Up    │  │   Custom    │       │
│  │ Integration │  │    Emails     │  │   Rubrics   │       │
│  └─────────────┘  └───────────────┘  └─────────────┘       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Test Results

```
52 tests passed, 0 failed

Features tested:
- Real-Time Coaching
- Post-Call Analysis
- Cross-Call Intelligence
- CRM Integration
- Follow-Up Emails
- Team Benchmarking
- Custom Rubrics
- Sentiment Analysis
- Coaching Plans
- Multi-Language Support
- AI Coaching Assistant
- Export Functionality
- MCP Integration
```

---

## API Reference

### Real-Time Coaching
```python
from src.realtime.analyzer import RealtimeAnalyzer
analyzer = RealtimeAnalyzer()
result = analyzer.add_segment(segment)
```

### CRM Integration
```python
from src.api.crm import create_crm_integration
crm = create_crm_integration("salesforce", api_key="key", instance_url="url")
```

### Follow-Up Emails
```python
from src.api.followup import FollowUpEmailGenerator
generator = FollowUpEmailGenerator()
email = generator.generate_followup_email(evaluation, transcript, "user@example.com")
```

### Team Benchmarking
```python
from src.core.benchmark import TeamBenchmark
benchmark = TeamBenchmark()
benchmark.add_rep_data("Sarah", evaluations)
```

### Custom Rubrics
```python
from src.core.rubric import RubricManager
manager = RubricManager()
rubric = manager.create_rubric("Custom", {"compliance": 0.3, "clarity": 0.3, "action_items": 0.4})
```

---

## Conclusion

CallCoach-AI is the only platform that provides **real-time coaching during calls** (not just post-call), plus comprehensive CRM integration, automated follow-up emails, team benchmarking, and custom scoring rubrics.

These features make CallCoach-AI the most comprehensive call coaching platform available.
