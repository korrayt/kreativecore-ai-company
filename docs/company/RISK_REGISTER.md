# Risk Register

Do not put secrets or confidential incident details in a public repository.

| ID | Risk | Area | Likelihood | Impact | Status | Owner | Mitigation | Review |
|---|---|---|---|---|---|---|---|---|
| R-001 | Product claims exceed verified capability | Product/Marketing | Medium | High | ACTIVE | @korrayt | Require evidence before publishing claims | Monthly |
| R-002 | Secrets or private data enter Git history | Security | Medium | Critical | ACTIVE | @korrayt | Ignore rules, CI scan, immediate revocation process | Weekly |
| R-003 | Too many products dilute delivery | Portfolio | High | High | ACTIVE | @korrayt | Limit P1 work and require next proof | Weekly |
| R-004 | Local-first products become hard to install or update | Engineering | Medium | High | ACTIVE | @korrayt | Test packaging, rollback, update and offline paths | Per release |
| R-005 | Public repo exposes future internal company data | Company | Medium | High | ACTIVE | @korrayt | Use templates only or change visibility to Private | Immediate |

## Risk rule

Critical risks block release until an owner and mitigation exist.
