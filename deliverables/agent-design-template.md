# AI Agent Design Document

> **Capstone deliverable.** Fill in every section. This document is the final,
> fully documented design for a functional, reliable, and controllable AI agent
> operating on the opcp-explorer platform. Replace the _italic prompts_ with your
> own content.

- **Author:** _your name_
- **Date:** _YYYY-MM-DD_
- **Agent name:** _e.g. opcp-deploy-agent_
- **Target platform:** opcp-explorer (AI-Powered-Store)

---

## 1. Goal and Scope

_What single goal does this agent pursue? What is explicitly out of scope?_

- **Goal:** _..._
- **Out of scope:** _..._
- **Success criteria:** _how do you know the agent succeeded?_

## 2. Autonomy Level

_Where on the autonomy spectrum does this agent sit, and why? (suggest / confirm
each step / act with checkpoints / act and report / fully autonomous)_

- **Chosen level:** _..._
- **Justification:** _why is this the least autonomy that still accomplishes the goal?_

## 3. The Seven Core Components

_Describe each component for your agent._

### 3.1 Brain (LLM)
_Which model, and what reasoning role?_

### 3.2 Short-Term Memory
_What working context does it hold during a run?_

### 3.3 Long-Term Memory
_What persists across runs, and where is it stored?_

### 3.4 Tools
_Which opcp-explorer tools (API/CLI/MCP) does it call? List them._

### 3.5 Planner
_How does it decompose the goal into steps?_

### 3.6 Execution Loop
_How does the loop drive the agent? (reference your chosen variant below)_

### 3.7 Guardrails
_Summarize; detailed in section 6._

## 4. Loop Variant

_Which loop variant do you use and why? (ReAct / Plan-and-Execute / Reflexion,
or a combination)_

- **Chosen variant:** _..._
- **Justification:** _..._

## 5. Stopping Criteria

_List the explicit, enforced stopping criteria. Pair a goal condition with at
least one hard limit._

| Criterion | Type (goal / limit / error / human) | Value |
|-----------|-------------------------------------|-------|
| _..._ | _..._ | _..._ |

- **On stop, the agent reports:** _which criterion fired + final state_

## 6. Guardrails (Five Layers)

_Fill in a concrete control for every one of the five layers. All five rows are
required._

| Layer | Control for this agent |
|-------|------------------------|
| Permissions | _scoped token, tool allow-list, environment boundary_ |
| Operational limits | _iteration / retry / budget / timeout caps_ |
| Human approval | _which actions require a human yes_ |
| Observability | _what is logged / traced / alerted_ |
| Kill switch | _how the agent is stopped immediately_ |

## 7. Multi-Agent Decision

_Is this a single agent or multiple agents? Justify using the decision checklist._

- **Decision:** single agent | multi-agent
- **If multi-agent:** which pattern (supervisor / pipeline / parallel / network)
  and how do agents communicate?
- **Justification:** _why this is the simplest architecture that meets the need_

## 8. Responsible-AI Alignment (OVHcloud AI Policy)

_How does the design uphold responsible-AI principles? Map at least transparency,
human accountability, data protection, security, and controllability to concrete
choices above._

| Principle | How this design upholds it |
|-----------|----------------------------|
| Transparency | _..._ |
| Human accountability | _..._ |
| Data protection & privacy | _..._ |
| Security | _..._ |
| Controllability | _..._ |

## 9. Threat Model Reference

_Link to the completed threat model for this agent (see
threat-model-template.md)._

- **Threat model:** _..._

## 10. Open Questions and Risks

_What is unresolved, risky, or deferred?_

- _..._
