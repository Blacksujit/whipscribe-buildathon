# CallCoach-AI — Feature Documentation

## Overview

CallCoach-AI is a comprehensive call coaching platform that transforms recordings into actionable coaching insights. It goes beyond simple transcription to provide real-time coaching, cross-call intelligence, and automated follow-up.

## Key Differentiators

### 1. Real-Time Coaching During Calls
**The #1 differentiator — nobody else is doing this.**

All competitors do post-call analysis. CallCoach-AI provides live coaching during calls:
- Real-time sentiment analysis
- Live compliance risk detection
- Instant action item extraction
- Live coaching prompts during calls
- WebSocket server for real-time communication
- Live coaching dashboard with real-time prompts

**How it works:**
```
Speech Segment → Real-Time Analyzer → Coaching Prompt → Live Dashboard
```

**Example:**
```
Segment: "We'll definitely deliver by Q1. I promise."
→ [HIGH] Consider qualifying this commitment. Avoid absolute promises.
→ [LOW] Action item captured. Confirm the owner and deadline.
```

### 2. CRM Integration
Automatically sync call analysis to CRM systems:
- **Salesforce**: Create tasks, update opportunities, coaching notes
- **HubSpot**: Create tasks, update contacts, engagements
- Automatic task creation from action items
- Coaching notes synced to contact records

### 3. Automated Follow-Up Emails
Generate and send follow-up emails based on call analysis:
- Automatic email generation from action items
- Compliance risk summaries
- Scheduled follow-up emails
- Email tracking and analytics

### 4. Team Performance Benchmarking
Compare reps against each other:
- Team-wide score aggregation
- Rep rankings and comparisons
- Top performer identification
- Coaching needs assessment
- Team trend analysis

### 5. Custom Scoring Rubrics
Let teams define their own scoring criteria:
- Custom category weights
- Multiple rubric support (Standard, Sales, Support, Compliance Heavy)
- Rubric validation and persistence
- Weighted score calculation

### 6. Cross-Call Intelligence
Analyze trends across multiple meetings:
- Deal velocity metrics
- Recurring issue clustering
- Action item lifecycle tracking
- Speaker-level risk scoring
- Momentum direction

### 7. Four-Agent LLM Scoring
The transcript is not summarized — it is graded:
- **Compliance** — were commitments checked and tracked?
- **Tension** — where did participants hedge or deflect?
- **Clarity** — was the ask clear and consistent?
- **Action Items** — what was promised, by whom, and will it land?

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

## Feature Comparison

| Feature | CallCoach-AI | ShipNotes | TwelveStrings | CallBrief | Offstage |
|---------|-------------|-----------|---------------|-----------|----------|
| Real-Time Coaching | ✅ | ❌ | ❌ | ❌ | ❌ |
| Post-Call Analysis | ✅ | ✅ | ✅ | ✅ | ✅ |
| Cross-Call Intelligence | ✅ | ❌ | ❌ | ❌ | ❌ |
| CRM Integration | ✅ | ❌ | ❌ | ❌ | ❌ |
| Follow-Up Emails | ✅ | ❌ | ❌ | ❌ | ❌ |
| Team Benchmarking | ✅ | ❌ | ❌ | ❌ | ❌ |
| Custom Rubrics | ✅ | ❌ | ❌ | ❌ | ❌ |
| GitHub Integration | ❌ | ✅ | ❌ | ❌ | ❌ |
| Slack Integration | ✅ | ✅ | ❌ | ❌ | ❌ |
| App Store App | ❌ | ❌ | ❌ | ❌ | ✅ |

## Demo

Run the comprehensive demo to see all features working together:

```bash
python comprehensive_demo.py
```

## Test Suite

Run the comprehensive test suite to verify all features:

```bash
python test_all_features.py
```

## API Reference

### Real-Time Coaching

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
print(result['live_stats'])
```

### CRM Integration

```python
from src.api.crm import create_crm_integration, sync_call_to_crm

crm = create_crm_integration("salesforce", api_key="key", instance_url="url")
results = sync_call_to_crm(evaluation, transcript, crm)
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
summary = benchmark.get_team_summary()
```

### Custom Rubrics

```python
from src.core.rubric import RubricManager

manager = RubricManager()
rubric = manager.create_rubric("Custom", {"compliance": 0.3, "clarity": 0.3, "action_items": 0.4})
score = manager.apply_rubric("Custom", category_scores)
```

## Conclusion

CallCoach-AI is the only platform that provides:
1. **Real-time coaching during calls** (not just post-call)
2. **Comprehensive CRM integration** (Salesforce, HubSpot)
3. **Automated follow-up emails** (ensuring follow-through)
4. **Team performance benchmarking** (compare reps)
5. **Custom scoring rubrics** (flexible scoring)

These features make CallCoach-AI the most comprehensive call coaching platform available.
