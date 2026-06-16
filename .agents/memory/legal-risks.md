# Memory: Legal Risks and Compliance

> **Written by**: `/legal-advisor`
> **Read by**: `/product-manager`, `/strict-development`

---

## Usage Guide

This file records identified legal risks, their criticality level, and the recommended mitigating actions.
The Legal Advisor must update it at the end of each consultation that produces a relevant finding.

---

## Active Risks

| ID | Risk | Severity | Proposed Mitigation | Status |
|---|---|---|---|---|
| LEG-01 | Use of public EDGAR data: the system processes public SEC financial information. It must be explicit that the system does NOT provide investment advice. | Medium | Include a visible disclaimer in the Streamlit UI: "This analysis is for informational purposes only. It does not constitute financial or legal advice." | `UNDER_MITIGATION` |
| LEG-02 | Use of third-party LLMs (OpenAI / Anthropic) in cloud mode: 10-K data could be processed on external servers. | Medium | Document in the README that cloud mode sends fragments of public documents to third-party APIs. Recommend local mode for analyzing confidential proprietary documents. | `UNDER_REVIEW` |
| LEG-03 | Accuracy of outputs: the system could generate incorrect risk analyses with consequences on investment decisions. | High | Implement mandatory Human-in-the-Loop before the final report. LangSmith Faithfulness score as a quality gate. Output liability disclaimers. | `UNDER_MITIGATION` |

---

## Mitigated Risks

_(No entries)_

---

## Findings and Consultations

## [2026-06-16] — Legal Risk Analysis of the MVP

**Agent**: `/legal-advisor`
**Status**: `ACTIVE`
**Impact**: High

### Context
At the start of aria-10k development, the need was identified to evaluate the legal risks inherent in an automated AI financial analysis system.

### Decision
- The system operates exclusively on **public data** from the SEC (10-K forms available on EDGAR). There is no risk of insider trading.
- The Human-in-the-Loop in the graph is not just a UX decision: it is a **legal liability mechanism**. The final report is only generated with explicit human approval, transferring interpretive responsibility to the user.
- The **financial non-advisory disclaimer** must be present in: (1) the Streamlit UI, (2) the repository README, and (3) exported reports.
- For cloud mode: document in the README what data is sent to external APIs (text snippets from public documents, not user data).

### Pending Actions
- [ ] Add visible disclaimer in `app.py` (Streamlit UI) — Owner: Coding Agent
- [ ] Add "Legal Disclaimer" section in `README.md` — Owner: Coding Agent
- [ ] Define trace retention policy in LangSmith (analysis data) — Owner: `/legal-advisor`
