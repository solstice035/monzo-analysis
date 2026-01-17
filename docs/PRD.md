---
type: prd
status: in-progress
priority: medium
created: 2026-01-14
project-path: ~/Dev/monzo-analysis
tags:
  - ideas
---

# PRD: Monzo Webhook Financial Tracker

## Document Info

| Field | Value |
|-------|-------|
| **Project Name** | Monzo Webhook Financial Tracker |
| **Author** | Nick |
| **Status** | Draft |
| **Created** | January 2025 |
| **Last Updated** | January 2025 |
| **Gate Status** | Gate 1 - Business Requirements |

---

## 1. Problem Definition

### 1.1 Problem Statement

Personal finance tracking currently requires manual effort—exporting transactions, categorising them, and comparing against budgets in spreadsheets. This leads to delayed insights, missed spending patterns, and budgets that are only reviewed retrospectively rather than managed proactively.

### 1.2 Impact Quantification

- **Delayed awareness:** Spending reviewed weekly/monthly rather than real-time
- **Manual effort:** 1-2 hours/month on transaction export and categorisation
- **Missed patterns:** Recurring subscriptions and spending creep go unnoticed
- **Budget overruns:** Overspending discovered after the fact, not prevented
- **Estimated savings potential:** £100+/month from identified cost reductions

### 1.3 Current Workarounds

- Manual spreadsheet tracking (high friction, often abandoned)
- Monzo app categories (limited customisation, no budget comparison)
- Monthly bank statement review (retrospective, not actionable)
- Mental tracking (unreliable, leads to overspending)

---

## 2. User Persona

### 2.1 Primary User: Budget-Conscious Household Manager

| Attribute | Description |
|-----------|-------------|
| **Demographics** | Working professional, manages household finances, 30-50 |
| **Goals** | Stay within budget; identify savings opportunities; reduce financial stress; build savings |
| **Frustrations** | Surprise overspending; forgotten subscriptions; tedious manual tracking; lack of real-time visibility |
| **Tech Comfort** | Uses banking apps daily; comfortable with notifications; prefers automated solutions |

### 2.2 Secondary Considerations

- Partner may need visibility into shared budget status
- Joint accounts and personal accounts may need different handling
- Savings goals require tracking beyond just spending

---

## 3. User Stories

### 3.1 Core User Stories

| ID | As a... | I want to... | So that... | Acceptance Criteria |
|----|---------|--------------|------------|---------------------|
| US-01 | User | Receive instant notifications of transactions | I'm aware of all spending in real-time | Notification within seconds of transaction |
| US-02 | User | See transactions auto-categorised | I don't have to manually tag every purchase | 90%+ transactions categorised automatically |
| US-03 | User | View budget vs actuals for current month | I know if I'm on track | Dashboard shows spend vs budget per category |
| US-04 | User | Get alerts when approaching category budget limits | I can adjust behaviour before overspending | Alert at 80% and 100% thresholds |
| US-05 | User | Import my existing budget spreadsheet | My planned budget is the baseline | Budget categories and amounts imported |
| US-06 | User | See historical trends by category | I understand my spending patterns | Month-over-month comparison available |
| US-07 | User | Identify recurring subscriptions | I can review and cancel unused services | Recurring transactions flagged and summarised |

### 3.2 Stretch User Stories

| ID | As a... | I want to... | So that... |
|----|---------|--------------|------------|
| US-08 | User | Get weekly/monthly summary reports | I have digestible financial insights |
| US-09 | User | Compare month-over-month spending | I can track improvement over time |
| US-10 | User | Share budget status with my partner | We can manage household finances together |
| US-11 | User | Set savings goals and track progress | I stay motivated toward targets |

---

## 4. Feature Requirements

### 4.1 Transaction Capture

| ID | Feature | Priority | Value |
|----|---------|----------|-------|
| FR-01 | Receive real-time transaction notifications from bank | Must Have | Enables instant awareness |
| FR-02 | Capture all transaction details (amount, merchant, time) | Must Have | Foundation for all analysis |
| FR-03 | Handle refunds and adjustments correctly | Should Have | Accurate spend tracking |
| FR-04 | Store transaction history for analysis | Must Have | Enables trends and reporting |

### 4.2 Categorisation

| ID | Feature | Priority | Value |
|----|---------|----------|-------|
| FR-05 | Auto-categorise transactions by merchant | Must Have | Reduces manual effort |
| FR-06 | Allow manual category override | Must Have | User control and accuracy |
| FR-07 | Learn from manual overrides to improve accuracy | Could Have | Continuous improvement |
| FR-08 | Identify and flag recurring transactions | Should Have | Subscription visibility |

### 4.3 Budget Management

| ID | Feature | Priority | Value |
|----|---------|----------|-------|
| FR-09 | Import budget from existing spreadsheet | Must Have | Preserves existing planning |
| FR-10 | Define budget categories with monthly limits | Must Have | Enables tracking |
| FR-11 | Map transaction categories to budget categories | Must Have | Links spending to budget |
| FR-12 | Calculate real-time spend vs budget per category | Must Have | Core value proposition |
| FR-13 | Calculate overall monthly spend vs total budget | Must Have | High-level visibility |
| FR-14 | Support budget rollover (optional per category) | Could Have | Flexibility for variable spending |

### 4.4 Alerts & Notifications

| ID | Feature | Priority | Value |
|----|---------|----------|-------|
| FR-15 | Alert when category reaches 80% of budget | Should Have | Early warning |
| FR-16 | Alert when category exceeds budget | Must Have | Prevent further overspending |
| FR-17 | Daily or weekly spending summary | Should Have | Regular awareness |
| FR-18 | Configurable notification preferences | Should Have | User control |

### 4.5 Reporting & Insights

| ID | Feature | Priority | Value |
|----|---------|----------|-------|
| FR-19 | Dashboard showing current month budget vs actuals | Must Have | At-a-glance status |
| FR-20 | Category breakdown with visual progress | Must Have | Clear communication |
| FR-21 | Transaction list with search and filter | Must Have | Drill-down capability |
| FR-22 | Monthly trend charts | Should Have | Pattern identification |
| FR-23 | Subscription/recurring payment summary | Should Have | Cost reduction opportunities |
| FR-24 | AI-powered cost reduction recommendations | Could Have | Proactive savings advice |

---

## 5. Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Transaction processing latency | < 5 seconds | Time from bank event to notification |
| Budget vs actual visibility | Real-time, always current | System uptime and data freshness |
| Manual categorisation required | < 10% of transactions | Count of manual overrides |
| Cost reduction opportunities identified | £100+/month potential | Flagged subscriptions and recommendations |
| Time spent on manual finance tracking | 80% reduction | User survey (before/after) |
| Budget adherence improvement | 20% fewer overspend events | Month-over-month comparison |

---

## 6. Scope

### 6.1 In Scope

- Real-time transaction monitoring from Monzo accounts
- Automatic and manual transaction categorisation
- Budget import and tracking against actuals
- Threshold-based alerts and notifications
- Dashboard for budget status and transaction history
- Basic subscription/recurring payment identification
- Mobile-responsive interface

### 6.2 Out of Scope (for MVP)

- Multi-bank aggregation (other banks beyond Monzo)
- Credit card tracking
- Investment tracking
- Tax categorisation or reporting
- Receipt scanning and storage
- Bill payment reminders
- Shared/family budgets with multiple users

### 6.3 Assumptions

- User has Monzo account and consents to data access
- Existing budget spreadsheet follows importable format
- User prefers automated tracking over manual entry
- Monzo merchant categories are reasonably accurate baseline

### 6.4 Dependencies

- Monzo provides transaction data access (via user authorisation)
- Notification delivery mechanism available
- Budget spreadsheet exists and can be exported

---

## 7. Security & Privacy Requirements

| Requirement | Description |
|-------------|-------------|
| User data ownership | Only authenticated user can access their financial data |
| Data encryption | All financial data encrypted at rest |
| Minimal data retention | Only store data necessary for functionality |
| No sensitive storage | Do not store full account numbers or authentication credentials |
| Audit trail | Track who performed actions for accountability |
| User consent | Explicit consent required for data access |

---

## 8. Business Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Bank data access limitations | Medium | High | Design for available data; plan for API changes |
| Categorisation accuracy insufficient | Medium | Medium | Easy manual override; learning from corrections |
| User doesn't maintain budget spreadsheet | Medium | Low | Provide in-app budget editing as alternative |
| Notification fatigue | Medium | Medium | Configurable thresholds; summary digests option |
| Scope creep to full accounting | Medium | Medium | Stay focused on budget tracking, not bookkeeping |
| Privacy concerns about financial data | Low | High | Clear data policies; local-first option |

---

## 9. Budget Spreadsheet Integration

### 9.1 Expected Input Format

The system should accept budget data in common spreadsheet formats with:
- Category name
- Monthly budget amount
- Optional notes/description

### 9.2 Import Process (User Experience)

1. User exports existing spreadsheet
2. User uploads to system
3. System displays mapping preview
4. User confirms or adjusts category mappings
5. Budget created and tracking begins

---

## 10. Go-to-Market Considerations

- **Target launch:** Personal use; potential expansion if validated
- **Acquisition:** Direct personal need; potential sharing with similar users
- **Retention:** Daily transaction notifications; weekly summaries; monthly reviews
- **Value demonstration:** First month savings identified vs effort

---

## 11. Open Questions

- [ ] Should partner/spouse have separate view or shared dashboard?
- [ ] How to handle joint account vs personal account transactions?
- [ ] Should Pot transfers be tracked as transactions or excluded?
- [ ] Integration with other accounts (savings, credit cards) in future?
- [ ] Preferred notification frequency: per-transaction vs digest?
- [ ] What budget categories are most common/useful?

---

## 12. Gate 1 Validation Checklist

| Category | Requirement | Status |
|----------|-------------|--------|
| **Problem Definition** | Problem articulated | ✅ |
| | Impact quantified | ✅ |
| | Users identified | ✅ |
| | Workarounds documented | ✅ |
| **Solution Value** | Features address core problem | ✅ |
| | Success metrics measurable | ✅ |
| | User value clear per feature | ✅ |
| **Scope Clarity** | In-scope explicit | ✅ |
| | Out-of-scope with rationale | ✅ |
| | Assumptions documented | ✅ |
| | Dependencies identified | ✅ |
| **Business Fit** | Security requirements identified | ✅ |
| | Risks identified | ✅ |

**Gate 1 Result:** ✅ PASS → Proceed to Feature Map

---

## Appendix

### A. Related Documents

- [Fashion Assistant PRD](PRD-fashion-assistant.md)
- [Voice Ideation PRD](PRD-voice-ideation.md)
- [Project Roadmap](2026-01-14%20-%20null.md)

### B. Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1 | Jan 2025 | Nick | Initial draft |
| 0.2 | Jan 2025 | Nick | Removed technical content; aligned to PRD spec |
