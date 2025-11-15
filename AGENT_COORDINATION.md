# 🤖 Agent Coordination Hub

**Purpose:** Central coordination point for all development agents working on the multi-utility meter monitoring system.

**Last Updated:** 2025-11-15
**Project Status:** Phase 1 - Foundation Setup

---

## 📊 Current Project State

### Completed ✅
- Water meter monitoring system (fully functional)
- Thingino firmware deployment (10.10.10.207)
- Claude Vision API integration
- InfluxDB + Grafana setup
- Secure credential management (.env/.env.local)
- Enterprise-grade documentation (11 files)

### In Progress 🔄
- Multi-meter architecture planning
- Hardware procurement (electric + gas cameras)
- Code refactoring for modular design

### Planned 🗓️
- Phase 1: Foundation (Week 1)
- Phase 2: Integration (Week 2)
- Phase 3: Visualization (Week 3)
- Phase 4: Finalization (Week 4)

---

## 🎯 Immediate Action Items (Week 1)

### Hardware Team
**Status:** Pending Approval
- [ ] Approve hardware list ($128 total)
- [ ] Order 2x Wyze Cam V2 cameras
- [ ] Order 2x MicroSD cards (32GB)
- [ ] Order weatherproof housings (optional)
- [ ] Estimated arrival: 3-5 business days

**Contacts:**
- Sean Hunt (Owner) - Decision maker

### Development Team A - Code Refactoring
**Status:** Ready to Start
- [ ] Create src/meters/ directory structure
- [ ] Implement base_meter.py abstract class
- [ ] Refactor water_meter.py from existing code
- [ ] Implement electric_meter.py
- [ ] Implement gas_meter.py
- [ ] Create camera_capture.py module

**Files to Create:**
```
src/
├── meters/
│   ├── __init__.py
│   ├── base_meter.py           (NEW)
│   ├── water_meter.py          (REFACTORED)
│   ├── electric_meter.py       (NEW)
│   ├── gas_meter.py            (NEW)
├── core/
│   ├── camera_capture.py       (NEW)
│   ├── llm_reader.py           (UPDATE)
│   └── influxdb_writer.py      (UPDATE)
└── utils/
    ├── config_loader.py        (NEW)
    └── logging_utils.py        (NEW)
```

**Contacts:**
- Development Lead - Start immediately
- Est. Time: 3-4 days

### Development Team B - Configuration
**Status:** Ready to Start
- [ ] Create config/meters.yaml with all meter definitions
- [ ] Update .env.example with multi-meter variables
- [ ] Implement config_loader.py for YAML parsing
- [ ] Create config examples for each meter type
- [ ] Document configuration options

**Files to Create:**
```
config/
├── meters.yaml                 (NEW)
├── prompts.yaml                (NEW)
└── examples/
    ├── meters-water.yaml
    ├── meters-electric.yaml
    └── meters-gas.yaml
```

**Contacts:**
- Configuration Specialist - Start after Team A begins
- Est. Time: 2-3 days

### DevOps Team - Infrastructure
**Status:** Ready to Start
- [ ] Update docker-compose.yml for InfluxDB token management
- [ ] Create InfluxDB migration scripts
- [ ] Update Grafana provisioning for multi-bucket setup
- [ ] Create environment variable validation scripts
- [ ] Set up CI/CD for automated testing

**Files to Update:**
```
docker-compose.yml              (UPDATE)
scripts/
├── migrate_influxdb.py         (NEW)
├── setup_influxdb.sh           (NEW)
└── validate_config.py          (NEW)
```

**Contacts:**
- DevOps Lead - Start in parallel with other teams
- Est. Time: 2-3 days

---

## 📋 Weekly Sync Schedule

### Daily Standup (5 min)
**Time:** 9:00 AM
**Format:** Slack status update
**Template:**
```
✅ Yesterday: [completed tasks]
🔄 Today: [planned tasks]
🚧 Blockers: [any blockers]
```

### Mid-Week Check-in (15 min)
**Time:** Wednesday 2:00 PM
**Format:** Video/Voice sync
**Agenda:**
- Integration points review
- Dependency management
- Risk assessment
- Adjust timeline if needed

### End-of-Week Review (30 min)
**Time:** Friday 4:00 PM
**Format:** Full team sync
**Agenda:**
- Phase completion status
- Deliverables review
- Next week planning
- Documentation updates

---

## 🔗 Key Dependencies & Integration Points

### Code Dependencies
```
multi_meter_monitor.py (Orchestrator)
    ├── meters/base_meter.py (Abstract)
    │   ├── meters/water_meter.py
    │   ├── meters/electric_meter.py
    │   └── meters/gas_meter.py
    ├── core/camera_capture.py
    ├── core/llm_reader.py
    ├── core/influxdb_writer.py
    └── utils/config_loader.py
```

### Database Dependencies
```
InfluxDB (Single instance)
├── Bucket: water_meter (existing)
├── Bucket: electric_meter (new)
├── Bucket: gas_meter (new)
└── Bucket: utility_costs (new)
```

### Configuration Dependencies
```
.env (shared across all modules)
├── Camera credentials (WATER_*, ELECTRIC_*, GAS_*)
├── API keys (ANTHROPIC_API_KEY)
└── Database config (INFLUXDB_*)

config/meters.yaml (meter-specific)
├── Water meter settings
├── Electric meter settings
└── Gas meter settings
```

---

## 🎓 Knowledge Transfer

### Essential Context for All Teams

**Water Meter System (Reference)**
- File: `WYZE_CAM_V2_SETUP.md` (800+ lines)
- File: `CREDENTIALS.md` (security practices)
- File: `PROJECT_SETUP_COMPLETE.md` (overview)

**Claude Vision API Usage**
- Model: claude-opus-4-1 (latest, most reliable)
- Input: 1920x1080 JPEG snapshots (~450KB)
- Cost: ~$0.01 per reading (3 meters = $0.03)
- Confidence scoring: high/medium/low

**InfluxDB Patterns**
- Measurement-based organization (water_meter, electric_meter, etc.)
- Tags for metadata (meter_id, camera, confidence)
- Fields for numerical data (readings, usage, flow)
- 1-year retention policy
- Flux query language (not InfluxQL)

**Grafana Best Practices**
- Pre-provisioned dashboards from `/grafana-provisioning/`
- Template variables for meter selection
- Color coding: Water=Blue, Electric=Yellow, Gas=Orange
- Real-time refresh: 30 seconds

---

## 📝 Communication Protocols

### Blocking Issues
**Action:** Escalate immediately
**Channel:** Slack #blockers or mention @sean
**Template:**
```
🚨 BLOCKER: [Issue name]
Severity: [High/Medium/Low]
Impact: [What is blocked]
Details: [Technical details]
Needed from: [Who/What to unblock]
Timeline: [When needed by]
```

### Integration Tests Required
**When:** Before merging between team work
**Who:** Both teams involved
**Documentation:** Update INTEGRATION_TESTS.md

### Code Review Process
**Reviewer:** Senior dev or team lead
**Criteria:** Security, style, performance, docs
**Approval:** Required before merge

---

## 🔐 Security Coordination

### Credential Handling
- **Rule:** NEVER commit `.env.local`, `.env`, or credentials
- **Validation:** `git check-ignore .env .env.local` before every commit
- **Sharing:** Use Slack, direct message, or secure channel (NOT GitHub)
- **Rotation:** Every 90 days

### Code Review Security Checklist
- [ ] No hardcoded credentials
- [ ] No debug logging of secrets
- [ ] No credentials in comments
- [ ] Proper .gitignore patterns
- [ ] File permissions verified (600 for .env files)

---

## 📊 Progress Tracking

### Metrics to Monitor
```
Velocity: Tasks completed per day
Quality: Tests passing (target: 100%)
Integration: Blockers (target: 0)
Documentation: Updated with code changes (target: 100%)
Security: Credential exposure incidents (target: 0)
```

### Dashboard
See: `PROJECT_SETUP_COMPLETE.md` → Success Criteria

---

## 🎯 Phase 1 Deliverables Checklist

### Code
- [ ] src/meters/ module complete
- [ ] config/ management complete
- [ ] Multi-meter monitor.py created
- [ ] All tests passing
- [ ] Code documented

### Configuration
- [ ] config/meters.yaml created
- [ ] .env.example updated
- [ ] Multi-meter .env documented
- [ ] Example configs provided

### Infrastructure
- [ ] InfluxDB buckets created
- [ ] Migration script tested
- [ ] Grafana updated
- [ ] Docker compose working

### Documentation
- [ ] Code API docs
- [ ] Configuration guide
- [ ] Setup procedures
- [ ] Troubleshooting guide

### Testing
- [ ] Unit tests (all modules)
- [ ] Integration tests (all teams)
- [ ] Hardware tests (camera + API)
- [ ] Database tests (writes + queries)

---

## 🚀 Launch Readiness Checklist

### Code Quality
- [ ] All modules implemented
- [ ] 95%+ test coverage
- [ ] Code reviewed and approved
- [ ] No security issues
- [ ] Performance verified

### Documentation
- [ ] API documentation complete
- [ ] User guides written
- [ ] Troubleshooting guide
- [ ] Architecture diagrams
- [ ] Credential rotation procedures

### Testing
- [ ] Unit tests: 100% pass
- [ ] Integration tests: 100% pass
- [ ] Load tests: OK
- [ ] Failure scenarios: Handled
- [ ] Manual validation: Complete

### Deployment
- [ ] All configs ready
- [ ] Database initialized
- [ ] Grafana dashboards loaded
- [ ] Alerts configured
- [ ] Monitoring active

### Training
- [ ] Team documentation
- [ ] Runbook created
- [ ] Handoff complete
- [ ] Support procedures

---

## 📞 Emergency Contacts

| Role | Name | Channel | Response Time |
|------|------|---------|----------------|
| Project Owner | Sean Hunt | Slack #general | 1 hour |
| Dev Lead | [TBD] | Slack | 30 min |
| DevOps Lead | [TBD] | Slack | 30 min |
| QA Lead | [TBD] | Slack | 1 hour |
| Security Lead | [TBD] | Slack | 30 min |

---

## 📚 Reference Documents

### System Architecture
- `PROJECT_SETUP_COMPLETE.md` - Complete overview
- `SECURITY_SUMMARY.md` - Security design
- `THINGINO_SETUP_STATUS.md` - Firmware details

### Implementation Plan
- `AGENT_COORDINATION.md` - This document
- Multi-meter technical plan (from agent)
- Database schema details

### Operational Guides
- `CREDENTIALS.md` - Credential management
- `GRAFANA_SETUP.md` - Dashboard guide
- `WYZE_CAM_V2_SETUP.md` - Hardware setup

### Configuration Examples
- `.env.example` - Environment variables
- `config/meters.yaml` - Meter definitions
- `docker-compose.yml` - Infrastructure

---

## 🔄 Feedback Loop

### Agent to Agent
**Every team shares their progress with others**
- Daily standup: What I did, what I'm doing, blockers
- Weekly review: Completed, in progress, next week
- Integration point: How my work connects to theirs

### Agent to Owner
**Weekly updates to Sean Hunt**
- Status: On track / At risk / Blocked
- Deliverables: What's complete
- Decisions needed: Any choices to make
- Budget impact: Any cost changes

### Documentation
**All decisions and changes logged**
- Update AGENT_COORDINATION.md with changes
- Keep timeline accurate
- Document blockers and solutions
- Update progress metrics

---

## 🎉 Success Criteria

### Week 1 (Foundation)
✅ All code modules created and integrated
✅ Configuration system working
✅ Database schema ready
✅ All unit tests passing
✅ Documentation 80% complete

### Week 2 (Integration)
✅ Multi-meter orchestrator working
✅ InfluxDB data flowing
✅ Integration tests passing
✅ Database migration complete
✅ Performance verified

### Week 3 (Visualization)
✅ Grafana dashboards complete
✅ All alerts configured
✅ Cost tracking working
✅ 48-hour continuous test passed
✅ Documentation 95% complete

### Week 4 (Finalization)
✅ All tests passing (100%)
✅ Security audit complete
✅ Deployment checklist complete
✅ Team trained and ready
✅ System production-ready

---

## 📋 Template: Daily Standup

```
# [Team Name] - [Date]

## ✅ Completed Yesterday
- Task 1: [Details]
- Task 2: [Details]

## 🔄 In Progress Today
- Task 1: [Target completion]
- Task 2: [Target completion]

## 🚧 Blockers
- Issue 1: [Details] - Needs [from whom]
- Issue 2: [Details] - Needs [from whom]

## 📊 Metrics
- Lines of code: [#]
- Tests passing: [#/total]
- Documentation complete: [%]

## 🤝 Dependencies
- Waiting for: [Team/Person] on [Task]
- Can provide: [To Team/Person] for [Task]
```

---

## 📋 Template: Weekly Review

```
# Week [#] Review - [Date]

## 🎯 Completed Deliverables
- [ ] Item 1
- [ ] Item 2
- [ ] Item 3

## 🔄 In Progress
- Item 1: [% complete, target date]
- Item 2: [% complete, target date]

## 🚧 Blockers This Week
- Issue: [Impact] - [Resolution]

## 📊 Metrics
- Velocity: [tasks/day]
- Code quality: [test coverage]
- Documentation: [% complete]

## 🎯 Next Week Plans
- Team priorities: [1, 2, 3]
- Integration points: [with whom]
- Risks identified: [Mitigation]
```

---

## 🚀 Ready to Launch

**All teams:** Use this coordination hub to stay aligned!

**Key principles:**
1. **Transparency** - Share progress openly
2. **Coordination** - Know dependencies
3. **Communication** - Use templates
4. **Documentation** - Update as you go
5. **Quality** - Test everything
6. **Security** - Never expose credentials

**Let's build something great together!** 🎉

---

**Coordination Hub Owner:** Sean Hunt
**Last Updated:** 2025-11-15
**Next Review:** Daily (standup), Weekly (Friday)
