# Shared Memory Protocol — aria-10k Agents

This directory acts as the **persistent memory** of the aria-10k multi-agent system.
Each file represents the "live state" of a specific domain. Agents must **read it at the start**
and **update it at the end** of any session that produces relevant decisions or findings.

---

## Protocol Rules

### When STARTING a session (read)
Before responding to the user, each agent MUST:
1. Read its corresponding memory file (see map below).
2. Read `shared-context.md` to understand the global project state.
3. Briefly mention to the user if relevant previous context was loaded.

### When FINISHING a session (write)
If the session produced decisions, findings, or state changes, the agent MUST:
1. Update its memory file with a new entry (format: `## [DATE] — Title`).
2. If the finding affects another domain, also update `shared-context.md`.
3. Never delete previous entries — only append or mark as `[SUPERSEDED]`.

---

## File Map by Agent

| Workflow | Main Memory File | Also Reads |
|---|---|---|
| `/strict-development` | `architecture-decisions.md` | `shared-context.md` |
| `/product-manager` | `product-decisions.md` | `shared-context.md` |
| `/llm-infra-expert` | `gcp-decisions.md` | `shared-context.md` |
| `/legal-advisor` | `legal-risks.md` | `shared-context.md` |
| `/ui-improvements` | `architecture-decisions.md` (UI section) | `product-decisions.md` |

---

## Standard Entry Format

Each entry in the memory files MUST follow this format:

```markdown
## [YYYY-MM-DD] — Descriptive title of the decision or finding

**Agent**: [workflow name]
**Status**: `ACTIVE` | `SUPERSEDED` | `UNDER_REVIEW`
**Impact**: High / Medium / Low

### Context
Brief description of the problem or question that originated this entry.

### Decision / Finding
The decision made, technical finding, or identified risk.

### Rationale
Why this decision was made (trade-offs evaluated).

### Impact on Other Domains
- **Product**: [if applicable]
- **Legal**: [if applicable]
- **GCP/Costs**: [if applicable]
- **Frontend (Streamlit)**: [if applicable]

### Pending Actions
- [ ] Action 1 — Owner: [agent or person]
- [ ] Action 2 — Owner: [agent or person]
```

---

## Special File: `shared-context.md`

`shared-context.md` is the only file that **all agents read** and contains:
- Current state of pipeline development phases (Phase 1 → Phase 4)
- LangGraph architecture decisions blocking development
- Active hallucination or data quality risks
- Roadmap state and system capabilities

It should only contain high-relevance **cross-domain** information. Do not duplicate information that is already in specific files.
