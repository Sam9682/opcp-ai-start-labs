# AI Agent Threat Model

> **Workshop deliverable.** Fill in every section. This threat model identifies
> how an agent operating on opcp-explorer could be misused or fail, and maps each
> mitigation to one of the five guardrail layers. Replace the _italic prompts_.

- **Author:** _your name_
- **Date:** _YYYY-MM-DD_
- **Agent under analysis:** _e.g. opcp-deploy-agent_
- **Target platform:** opcp-explorer (AI-Powered-Store)

---

## 1. System Overview

_Briefly describe the agent, its goal, its tools, and its autonomy level. What
can it touch on opcp-explorer?_

## 2. Trust Boundaries

_Where does untrusted input enter? (user prompts, tool outputs, web content,
other agents) Where are the privilege boundaries?_

- _..._

## 3. Threats

_For each threat, describe the attack/failure, its impact, and its likelihood.
Cover at least the three agent-specific threats below; add others as needed._

### 3.1 Tool Misuse
_The agent calls a tool in a harmful or unintended way (e.g. deploys to
production, deletes an app, exhausts quota)._

- **Impact:** _..._
- **Likelihood:** _..._

### 3.2 Prompt Injection
_Untrusted content (tool output, user data, a repo file) smuggles instructions
that redirect the agent._

- **Impact:** _..._
- **Likelihood:** _..._

### 3.3 Runaway Loops
_The agent fails to stop: oscillation, repeated identical failures, or no
convergence — burning budget and hammering the platform._

- **Impact:** _..._
- **Likelihood:** _..._

### 3.4 Other Threats
_e.g. data exfiltration, excessive permissions, secret leakage, denial of
service. Add rows as needed._

- _..._

## 4. Mitigations Mapped to the Five Guardrail Layers

_For each threat above, specify the mitigating control and the guardrail layer it
belongs to. Every one of the five layers must appear at least once._

| Threat | Mitigation | Guardrail layer |
|--------|-----------|-----------------|
| Tool misuse | _..._ | Permissions |
| Runaway loops | _..._ | Operational limits |
| High-impact action | _..._ | Human approval |
| Undetected failure | _..._ | Observability |
| Active incident | _..._ | Kill switch |

### Guardrail Layer Coverage Checklist
_Confirm each layer is addressed by at least one mitigation._

- [ ] Permissions
- [ ] Operational limits
- [ ] Human approval
- [ ] Observability
- [ ] Kill switch

## 5. Residual Risk

_What risk remains after mitigations? Is it acceptable? Who signs off?_

- _..._

## 6. Responsible-AI Note (OVHcloud AI Policy)

_How do these mitigations align with responsible-AI principles (transparency,
human accountability, security, controllability)? Confirm against the canonical
OVHcloud AI Policy._

- _..._
