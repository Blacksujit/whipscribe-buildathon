# CallCoach-AI × WhipScribe

**The only call coaching platform with real-time coaching during calls.**

[Live App](https://callcoachai.sujit.top/) · [Demo Video](https://videotourl.com/videos/1790703784383-893d45c0-0e34-4ade-84b1-0c732fbc65c0.webm)

---

## What Makes CallCoach-AI Different

| Feature | CallCoach-AI | Others |
|---------|-------------|--------|
| **Real-Time Coaching During Calls** | ✅ | ❌ |
| Post-Call Analysis | ✅ | ✅ |
| Cross-Call Intelligence | ✅ | ❌ |
| CRM Integration | ✅ | ❌ |
| Follow-Up Emails | ✅ | ❌ |
| Team Benchmarking | ✅ | ❌ |
| Custom Rubrics | ✅ | ❌ |
| Sentiment Analysis | ✅ | ❌ |
| Coaching Plans | ✅ | ❌ |
| Multi-Language | ✅ | ❌ |
| AI Assistant | ✅ | ❌ |
| Export | ✅ | ❌ |
| MCP Integration | ✅ | ❌ |

**The #1 differentiator: Real-Time Coaching During Calls.** All competitors do post-call analysis. CallCoach-AI provides live coaching during calls.

---

## Features

### 1. Real-Time Coaching During Calls
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

### 3. Cross-Call Intelligence
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

### 11. AI Coaching Assistant
Conversational coaching:
- "How did I do on my last call?"
- "What should I improve?"
- "What are my weaknesses?"

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
