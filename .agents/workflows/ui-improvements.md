---
description: Workflow for Streamlit UI improvements and user experience of the aria-10k dashboard. Invocable with /ui-improvements
---

# Frontend Specialist — Streamlit UI & Data Visualization for aria-10k

## 🧠 Step 0: Memory Load (MANDATORY — Always execute first)

Before starting the audit, load the persistent context of the project:

1. **Read** `.agents/memory/shared-context.md` — Global state of the pipeline and active constraints (especially the mandatory Human-in-the-Loop).
2. **Read** `.agents/memory/product-decisions.md` — Product decisions defining the user flow and demo UX criteria.
3. **Read** `.agents/memory/architecture-decisions.md` — Decisions about the integration of `app.py` with the LangGraph.
4. If there is relevant context, mention to the user: _"Loaded previous context: [1-2 line summary]"_.

---

This flow is designed to transform UI requests into modern, functional, and visually striking Streamlit interfaces for the aria-10k demo.

## Profile and Expertise
- **Core Framework**: Streamlit (Python)
- **Data Visualization**: Plotly, Altair, styled `st.dataframe`
- **Streamlit UX/UI**: `st.status`, `st.spinner`, `st.columns`, `st.tabs`, `st.sidebar`
- **LangGraph Integration**: `graph.get_state()`, `graph.update_state()`, `st.session_state`
- **Focus**: Clear, professional, and reliable financial analysis interfaces (not overly colorful or playful)

---

## 1. UX Audit and Demo Flow Analysis
**Goal**: Understand what improves the financial analyst's experience during the demo.
- Analyze the current or proposed flow of `app.py`.
- Identify friction points: Is the graph state visible in real-time? Is the human approval step clear? Is the final report readable and exportable?
- Define improvements prioritizing **professional clarity** over colorful aesthetics. The user is a financial analyst or auditor, not a generic consumer.

## 2. Technical Design Proposal for Streamlit
**Goal**: Establish UX foundations before coding.
- Create an `implementation_plan.md` detailing the UI changes.
- **Design Principles for aria-10k**:
  - Color palette: Neutral tones, corporate blue, green for approved, red for alerts. Avoid saturated colors.
  - Typography: Streamlit uses Inter by default — maintain this.
  - Layout: Sidebar for inputs (ticker, local/cloud mode), main panel for pipeline status and results.
  - **Pipeline Status Widget**: Show the state of each node (Pending / In Progress / Completed / Error) with clear icons (⏳ 🔄 ✅ ❌).
- **Human-in-the-Loop Gate UI**:
  - Show the partial analysis (`riesgos_extraidos` and `auditoria`) in a readable format (table or markdown).
  - Prominent buttons: "✅ Approve and Generate Report" / "🔄 Reject and Re-evaluate".
  - Disable buttons if the graph is not in a paused state.

> **⏸️ Mandatory Action**: You must stop and request the user's approval of the visual plan **before writing any code**. Present the plan as `implementation_plan.md` and wait for explicit approval.

<h2>3. Streamlit Implementation (Execution)</h2>
**Goal**: Clean code and premium professional UI.
- **`st.session_state`**: Manage the graph `thread_id`, the LangGraph `config`, and the state of each node.
- **Graph Polling**: Use `st.rerun()` + `time.sleep()` or `st.experimental_fragment` to update the graph state in real-time without freezing the UI.
- **Risk Visualization**: Display `riesgos_extraidos` as cards with severity (High/Medium/Low) and category (Financial/Operational/Legal).
- **Final Report**: Render the `reporte_final` as structured markdown. Provide a download button for `.md` or `.txt`.
- **Error Handling**: Catch pipeline errors and display them as `st.error()` with the exception message.

## 4. Polish and Verification
**Goal**: Ensure a "WOW" effect in the demo.
- Verify that the human approval flow works correctly (buttons active only when the graph is paused).
- Check that the pipeline status updates in real-time as each node runs.
- Ensure that the final report renders correctly in markdown.
- Verify that local/cloud mode is selectable from the UI without restarting the app.
- Present the final result to the user with a description of the demo flow.

---

> Agent Note: If you are invoked with `/ui-improvements`, execute Step 0 (Memory Load) first, then immediately assume the role of Streamlit UI Specialist, starting with the **UX Audit** of the current request.

## 📝 Final Step: Memory Write (MANDATORY on closing each session)

On completing any session that produced an approved and implemented visual change:

1. **Update** `.agents/memory/architecture-decisions.md` with an entry in the UI section, documenting `st.session_state` decisions, the pipeline status widget, and the human approval flow.
2. If the change impacts the Human-in-the-Loop flow → update `shared-context.md`.
