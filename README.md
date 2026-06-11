# Growth

Growth is a personalized life-improvement system that helps people turn
meaningful ambitions into consistent action, measurable progress, and better
decisions.

Most goal-setting products stop after helping users create goals and tasks.
Growth should understand where a person is today, where they want to go, why it
matters, what constraints they face, and which actions are actually producing
results. It should then build a personalized operating system for that person
and continuously improve it using their real-world evidence.

Examples:

- A person who wants to become fit receives a plan adapted to their current
  health, schedule, preferences, equipment, recovery, and target outcome.
- A person who wants a better job receives a plan based on their current role,
  target role, current and target compensation, skill gaps, timeline, location,
  and interview pipeline.
- A person building a product receives a system connecting product bets,
  customer learning, shipping, distribution, and business outcomes.
- A person learning a new skill receives a plan focused on demonstrated ability,
  feedback, and useful projects instead of passive content consumption.

## Product Vision

**Help every person build an adaptive operating system for becoming who they
want to become.**

Growth should behave like a thoughtful combination of strategist, coach,
planner, and evidence analyst. It should:

1. Understand the user's whole situation before recommending a plan.
2. Convert broad ambitions into clear outcomes, milestones, and weekly actions.
3. Adapt recommendations to available time, energy, money, and constraints.
4. Measure evidence and outcomes rather than rewarding busywork.
5. Detect distraction, overload, stalled strategies, and misleading progress.
6. Learn from the user's behavior and improve the plan over time.
7. Help the user make tradeoffs across competing areas of life.
8. Keep the user in control of important decisions and personal data.

The first version is being designed around one demanding personal use case:
improving career, health, product-building, quant knowledge, and professional
networking at the same time. Once this works well, the underlying system can be
customized for other people and transformations.

## Product Principles

- **Personalized, not generic:** recommendations must reflect the user's starting
  point, desired outcome, preferences, and constraints.
- **Outcomes over activity:** completing useful work matters more than checking
  boxes.
- **Adaptive, not rigid:** plans should change when evidence or circumstances
  change.
- **Focused, not overwhelming:** the product should protect users from trying to
  improve everything at once.
- **Honest, not flattering:** Growth should respectfully identify weak plans,
  avoidance, and false progress.
- **Sustainable, not extreme:** plans must account for health, recovery, and the
  realities of the user's life.
- **Private by design:** users should control what is stored, shared, or connected.

## Personalization Onboarding

Before creating a plan, Growth conducts a friendly but thorough discovery
conversation. It starts with the user's desired transformation, then asks only
the relevant follow-up questions for selected areas such as career, fitness,
learning, product-building, finances, or relationships.

- [Product onboarding questionnaire](docs/ONBOARDING_QUESTIONNAIRE.md)
- [How answers become a personalized system](docs/PERSONALIZATION_MODEL.md)

## Operating Model

The system has four layers:

- **Direction:** durable outcomes and decision filters in `config/goals.json`.
- **Weekly bets:** a deliberately small set of commitments created with the CLI.
- **Evidence:** completed work, metrics, artifacts, lessons, and outcomes.
- **Review loop:** a weekly report that decides what to continue, change, or stop.

Recommended weekly capacity:

| Area | Share | What counts |
|---|---:|---|
| Job Preparation | 45% | Interview readiness, resume defense, applications |
| Lens | 25% | Shipped product increments and user learning |
| Health | 15% | Training, nutrition, recovery, smoke-free days |
| Quant Research | 10% | Reproducible research and validated insights |
| Brand & Network | 5% | Useful public work and meaningful conversations |

Health is a constraint, not a reward. A bad health week should reduce planned
workload, not eliminate health work.

## Quick Start

Requires Python 3.9+ and no external packages.

```bash
python3 growth.py init
python3 growth.py dashboard
python3 growth.py add --area job --title "Defend Lens architecture end-to-end" --target 1 --unit artifact
python3 growth.py add --area health --title "Complete strength sessions" --target 4 --unit sessions
python3 growth.py list
python3 growth.py done 1 --value 1 --note "Recorded a 12-minute architecture walkthrough"
python3 growth.py evidence --area job --kind application --value 1 --note "Applied to Company X"
python3 growth.py review
```

The database lives at `.growth/growth.db`. Back it up or commit an encrypted
backup if you need portability. Generated weekly reviews live in `reviews/`.

## Weekly Rhythm

### Sunday: Review and Plan

1. Run `python3 growth.py review`.
2. Inspect outcomes, misses, and lessons.
3. Pick 5-8 weekly commitments across all areas.
4. Make at least half of Job Preparation commitments interview-output oriented.
5. Make Lens commitments vertically shippable.

### Daily: Execute and Record

1. Select the highest-value unfinished commitment.
2. Work in a focused block.
3. Record evidence when an output exists.
4. Capture new ideas using the decision filter before allowing them into a week.

### Friday: Career Pipeline Check

Track:

- High-quality applications sent.
- Recruiter and hiring-manager conversations.
- Interview stages and conversion.
- Repeated gaps found in interviews or job descriptions.

Use those gaps to change the following week's preparation.

## Rules That Keep It Useful

- Limit weekly commitments. A backlog may be infinite; a week may not.
- Every commitment needs a measurable target and a definition of done.
- Prefer outputs over inputs: build, explain, write, benchmark, apply, interview.
- Do not add a new project unless it passes the decision filter.
- Change the system during weekly review, not during a difficult Tuesday.
- Track leading indicators weekly and lagging outcomes monthly.

## Useful Commands

```bash
python3 growth.py add --help
python3 growth.py list --all
python3 growth.py dashboard --weeks 4
python3 growth.py idea "Build another unrelated side project"
python3 growth.py review --week 2026-06-08
```

See [SYSTEM.md](SYSTEM.md) for the measurement strategy and improvement loop.

## Current Status

This repository currently contains the first evidence-tracking CLI and the
product discovery documents. The next major milestone is designing the product
experience and architecture from the onboarding requirements before building the
full application.

## Working Across Systems

This directory is not yet initialized as a Git repository. It can be pushed to a
private GitHub repository to work from multiple computers.

Git should sync:

- Product code and configuration.
- Product requirements and design documents.
- Templates and non-sensitive reviews.

The local `.growth/growth.db` file is intentionally ignored. Committing a live
SQLite database can create merge conflicts across computers and may expose
sensitive personal data. Until Growth has secure user accounts and data sync,
each computer will have a separate local database.

Before publishing, review documents and generated reviews for personal or
confidential information. Use a private repository while the product contains
personal planning data.

Example initial setup:

```bash
git init
git add .
git commit -m "Initialize Growth product"
git branch -M main
git remote add origin <private-github-repository-url>
git push -u origin main
```
