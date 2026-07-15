---
name: feedback-commit-confirmation
description: Always ask user for confirmation before making any git commit
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ab6ce0eb-50c7-4146-9c7c-8dde2e6490b2
---

Always ask the user for explicit confirmation before running any `git commit` command.

**Why:** User preference — they want to review and approve each commit before it's made.

**How to apply:** Before every `git commit` (including in subagent dispatches), pause and show the user: the files to be staged, the proposed commit message, and ask "¿Confirmas este commit?" Wait for approval before proceeding. This applies to ALL commits in ALL contexts, including fix commits and doc commits.


---
**Relacionadas:** [[feedback_commits_and_graphify]] · [[feedback_no_tests_without_permission]]

Tags: #feedback #proceso
