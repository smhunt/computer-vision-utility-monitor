# 📞 Communication Plan - Multi-Meter Monitoring

**Effective Date:** November 15, 2025
**Team Size:** 4 dev teams + DevOps
**Communication Lead:** Sean Hunt

---

## 🎯 Communication Objectives

1. **Keep all teams synchronized** across dependent work
2. **Escalate blockers immediately** to prevent timeline slips
3. **Document decisions** for future reference
4. **Share learnings** across teams
5. **Maintain security** (never share credentials via channels)
6. **Track progress** against metrics

---

## 📅 Communication Schedule (Claude Agents - 24/7 Execution)

Claude agents work 24/7 and don't follow business hours. Communication is **async-first** with scheduled checkpoints for Sean:

### Daily Standup (Async - Post Anytime)
**When:** Any time, whenever work is done
**Format:** Slack message in #general
**Who posts:** Each Claude agent after completing daily work
**Sean reviews:** At his convenience (can batch review)

**Template:**
```
[Team Name] - [Date]

✅ Completed Today:
- Task 1: [Details]
- Task 2: [Details]
- Lines of code: X

🔄 In Progress:
- Task A: [% complete, est. completion]
- Task B: [% complete, est. completion]

🚧 Blockers:
- [Issue]: [Details] - Needs: [Decision/Input from Sean]

📊 Metrics:
- Test coverage: XX%
- Code review: [status]
```

**Claude Agent Advantage:**
- Work happens 24/7, not just 9-5
- No waiting for team member availability
- Multiple agents can work in parallel on independent tasks
- Faster iteration cycles

### Mid-Week Check-in (Wednesday - Optional)
**When:** Wednesday 2:00 PM (or whenever convenient)
**Format:** Slack thread or quick call if needed
**Purpose:** Integration review, dependency check
**Required if:** Any blockers exist

**Check:**
- Are Teams A/B/C ahead of schedule?
- Can Team D start prep work early?
- Any risks identified?

### Reviews (Whenever Work is Done)
**When:** Whenever you have time - async review of completed work
**Format:** Review of completed tasks + metrics
**Purpose:** Feedback, approval, decisions, course corrections

**What Sean does:**
- Review completed work asynchronously
- Provide feedback on PRs/code
- Make decisions on blockers
- Approve course changes
- Plan next phase when ready

**Outcome:** Real-time feedback, faster iteration, no artificial Friday deadline

---

## 📧 Asynchronous Communication

### Slack Channels (Primary)

**#general**
- Project announcements
- Non-urgent status updates
- General questions

**#blockers** (New - Create this)
- **Purpose:** Only for blocking issues
- **Response Time:** 30 minutes max
- **Format:** Use blocker template from below
- **Owner:** Sean Hunt monitors

**#code-review**
- Pull request discussions
- Code quality questions
- Security review requests

**#infrastructure**
- DevOps updates
- Database questions
- Docker/deployment issues

**#configuration**
- Config format discussions
- Meter definition questions
- .env/.yaml updates

**#integration**
- Integration testing updates
- Cross-team coordination
- API questions

### Email (Secondary - Formal Decisions)

**Use for:**
- Team assignments (formal)
- Budget approvals
- Security decisions
- Handoff documentation

**Example:**
```
Subject: [DECISION] Hardware Approval for Multi-Meter

Team,
Hardware budget approved for $128:
- 2x Wyze Cam V2
- 2x MicroSD 32GB
- Weatherproof housings (optional)

Procurement will order today. Est. delivery: 3-5 business days.

Sean Hunt
```

---

## 🚨 Blocking Issue Protocol

### When You're Blocked

**Immediate Actions (Same Day):**
1. Post to #blockers channel with template below
2. Tag the blocking team/person
3. Copy to daily standup as 🚨 BLOCKER

**Template:**
```
🚨 BLOCKER: [Issue Title]

Team: [Your Team Name]
Severity: [HIGH/MEDIUM/LOW]

Description:
[What is blocked? How does it impact work?]

Root Cause:
[What is preventing progress?]

Blocked By:
- Team/Person: [Who needs to unblock?]
- Task/Decision: [What specifically?]

Timeline:
- Needed by: [Date/Time]
- Impact if delayed: [What fails?]

Proposed Solutions:
1. [Option A]
2. [Option B]
3. [Fallback option]

Requesting from [Team/Person]: [Specific action needed]
```

**Who to Tag:**
- High severity: @sean-hunt (Project Owner)
- Code blocking: @team-a-lead
- Config blocking: @team-b-lead
- Infrastructure blocking: @team-c-lead
- Integration blocking: @team-d-lead

**Response Expectations:**
- HIGH: 1 hour response time
- MEDIUM: 4 hour response time
- LOW: 24 hour response time

### When You're Asked to Unblock

**Actions (Based on Severity):**

**HIGH Priority:**
1. Stop current work if needed
2. Address blocker immediately
3. Provide status update within 1 hour
4. Resolve or escalate to Sean

**MEDIUM Priority:**
1. Complete current task first (if <30 min)
2. Address blocker within 4 hours
3. Update #blockers with status
4. Escalate if unresolvable

**LOW Priority:**
1. Complete current work
2. Address blocker within 24 hours
3. Update #blockers with status

---

## 📋 Weekly Communication Cadence

### Monday (Day 1)
```
Morning:
- Send kickoff reminders to all teams
- Confirm team assignments
- Announce week priorities

Afternoon:
- All teams begin Week 1 work
- Team A: Create directory structure
- Team B: Design config format
- Team C: Update docker-compose
```

### Tuesday-Thursday
```
Daily:
- 9:00 AM: Standup in #general (async)
- Check #blockers for escalations
- Team progress on assigned tasks

Tuesday:
- Team A: Code implementation begins
- Team B: Config design review
- Team C: Database schema finalization

Wednesday 2:00 PM:
- Mid-week check-in call (15 min)
- Dependency review
- Adjust timeline if needed

Thursday:
- Teams on track for Friday deliverables?
- Any last-minute blockers?
```

### Friday (Day 5)
```
Morning:
- Final push to complete week 1 items
- Ensure documentation is up to date
- Code reviews completed

Afternoon:
- 4:00 PM: End-of-week review call (30 min)
  - Each team presents status
  - Team D previews requirements
  - Plan Week 2
- Update PROJECT_BOARD.md
- Document decisions & lessons learned
```

---

## 🎓 Documentation Protocol

### What to Document

**In Real-time (as you work):**
- Code comments for complex logic
- Docstrings for all functions
- Inline examples for configuration

**In Daily Standup:**
- What you completed
- What you're doing
- Blockers you hit

**In Weekly Review:**
- Completed deliverables
- Lessons learned
- Changes to timeline
- Risks identified

**In PRs / Code Review:**
- Why this change?
- What design patterns used?
- Any edge cases handled?

### Where to Document

| Content | Location | Format |
|---------|----------|--------|
| Code docs | Docstrings + comments | Python/YAML |
| Architecture | PROJECT_BOARD.md | Markdown + diagrams |
| Decisions | AGENT_COORDINATION.md | Markdown |
| Blockers | #blockers channel | Slack |
| Progress | Daily standup | Slack |
| Weekly summary | #general | Slack |
| Configuration | config/ YAML files | YAML |
| Credentials | .env.local (git-ignored) | ENV format |
| Procedures | CREDENTIALS.md, TEAM_KICKOFF.md | Markdown |

---

## 🔐 Security Communication Rules

### NEVER DO THIS
❌ Share .env.local via Slack, email, or GitHub
❌ Paste API keys in messages
❌ Include passwords in code or comments
❌ Share credentials in pull request descriptions
❌ Commit .env or .env.local to git

### DO THIS INSTEAD
✅ Share credentials via encrypted 1:1 message
✅ Reference credential names in code (not values)
✅ Use environment variables in all scripts
✅ Document credential names in CREDENTIALS.md
✅ Verify git check-ignore before committing

### If Credentials Are Exposed
1. **Immediately** post to #blockers with 🚨 BLOCKER tag
2. Change all exposed credentials in actual systems
3. Update .env.local with new credentials
4. Test that new credentials work
5. Document what was exposed (not the actual secret)

**Example (GOOD):**
```
🚨 BLOCKER: Grafana credentials exposed in PR #42

Root Cause: Developer committed .env.local by mistake

Actions Taken:
✓ Changed Grafana password immediately
✓ Removed .env.local from git history
✓ Updated .env.local with new password
✓ All team members changed their credentials

Prevention:
- Added pre-commit hook to check for credentials
- Updated CREDENTIALS.md with verification steps
```

---

## 👥 Individual Role Responsibilities

### Team Leads

**Daily:**
- Ensure team members post standup
- Unblock team issues immediately
- Monitor #blockers for team-specific items
- Update team progress tracking

**Weekly:**
- Present week status in end-of-week call
- Collect metrics from team members
- Identify risks and mitigations
- Plan following week with team

**As Needed:**
- Escalate blockers to Sean
- Coordinate with other team leads
- Ensure documentation stays current

### Team Members

**Daily:**
- Post standup by 9:15 AM
- Check #blockers for items affecting your work
- Update your task status in PROJECT_BOARD.md
- Commit code with clear messages

**Weekly:**
- Provide detailed status for team lead
- Document what you learned
- Review other team's work for integration
- Prepare questions for weekly call

**As Needed:**
- Report blockers to team lead
- Escalate to #blockers if urgent
- Review and comment on PRs
- Share knowledge with other teams

### Sean Hunt (Project Owner)

**Daily:**
- Monitor #blockers for escalations
- 9:00 AM standup review
- Make quick decisions on escalations

**Weekly:**
- Join end-of-week call
- Review PROJECT_BOARD.md updates
- Make final decisions on timeline/scope
- Approve hardware/budget items

**As Needed:**
- Unblock critical issues
- Approve major architecture changes
- Handle emergency procedures
- Final sign-off on deliverables

---

## 📊 Communication Metrics

### Track These Weekly

| Metric | Target | Owner |
|--------|--------|-------|
| Standup completion | 100% | Team leads |
| Blocker response time (HIGH) | <1 hour | Sean |
| Blocker response time (MEDIUM) | <4 hours | Team leads |
| Documentation updates | 100% per PR | All |
| Code review turnaround | <24 hours | All teams |
| Mid-week attendance | 100% | All leads |
| End-of-week attendance | 100% | All teams |

---

## 🎯 Communication Goals

### Goal 1: No Surprised
Every team knows what's happening in other teams
- **How:** Daily standups + weekly reviews
- **Success:** No "I didn't know" comments

### Goal 2: Blockers Surfaced Immediately
No team waits silently for help
- **How:** #blockers protocol + daily standups
- **Success:** All blockers resolved same-day

### Goal 3: Decisions Documented
Future teams can understand why we did things
- **How:** DECISION notes + meeting minutes
- **Success:** All major decisions logged

### Goal 4: Knowledge Shared
Learning from one team benefits others
- **How:** Weekly reviews + documentation
- **Success:** No duplicate work

### Goal 5: Credentials Secure
Zero credential exposures
- **How:** #security protocol + pre-commit hooks
- **Success:** Zero incidents

---

## 🚀 Launch Checklist

### Before Week 1 Starts
- [ ] All team leads assigned
- [ ] All Slack channels created
- [ ] Standup time confirmed (9:00 AM)
- [ ] Mid-week call scheduled (Wednesday 2:00 PM)
- [ ] End-of-week call scheduled (Friday 4:00 PM)
- [ ] Hardware approval and procurement initiated
- [ ] All teams read TEAM_KICKOFF.md
- [ ] All teams read COMMUNICATION_PLAN.md

### Week 1 Day 1
- [ ] Standup posted by all teams
- [ ] Each team confirms start on assigned tasks
- [ ] Any immediate blockers posted to #blockers
- [ ] Sean approves hardware (if not done)

---

## 📞 Quick Reference

### Emergency Contacts

| Role | Name | Slack | Response Time |
|------|------|-------|----------------|
| Project Owner | Sean Hunt | @sean-hunt | 1 hour |
| Team A Lead | [TBD] | @team-a-lead | 30 min |
| Team B Lead | [TBD] | @team-b-lead | 30 min |
| Team C Lead | [TBD] | @team-c-lead | 30 min |
| Team D Lead | [TBD] | @team-d-lead | 30 min |

### Channel Quick Links

- **#general** - Announcements
- **#blockers** - Blocking issues only (🚨 priority)
- **#code-review** - PR discussions
- **#infrastructure** - DevOps/database
- **#configuration** - Config/env variables
- **#integration** - Cross-team coordination

### Key Documents

- [TEAM_KICKOFF.md](TEAM_KICKOFF.md) - Launch document
- [AGENT_COORDINATION.md](AGENT_COORDINATION.md) - Coordination hub
- [PROJECT_BOARD.md](PROJECT_BOARD.md) - Task tracking
- [CREDENTIALS.md](CREDENTIALS.md) - Security/credentials

---

## 🎉 Communication Success!

When communication is working:
- ✅ Standup posts are consistent and detailed
- ✅ Blockers are surfaced and resolved quickly
- ✅ Weekly reviews show steady progress
- ✅ Teams coordinate naturally
- ✅ No surprises or last-minute issues
- ✅ Documentation keeps pace with code

---

**Communication Plan Owner:** Sean Hunt
**Last Updated:** November 15, 2025
**Review Cycle:** Weekly (every Friday)
**Next Update:** Friday EOD, Week 1
