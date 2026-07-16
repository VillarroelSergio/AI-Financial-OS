---
name: feedback_ux_snapshots
description: Run ux:snapshots:headed after UI changes to have visual context before reporting work done
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 525ffafe-0a87-4946-a6f4-99f5c1ed176f
---

Run `npm run ux:snapshots:headed` (from `apps/desktop/`) after any UI change before reporting work as complete. This gives visual context of the full application state.

**Why:** User wants snapshots available as visual context whenever the UI changes, so changes can be reviewed against the actual rendered output.

**How to apply:** After finishing any task that touches UI/frontend files, run the snapshot tool and review the output before marking the task done. Do not claim UI work is complete without having seen the rendered screens.


---
**Relacionadas:** [[feedback_commit_confirmation]] · [[feedback_commits_and_graphify]] · [[feedback_no_tests_without_permission]]

Tags: #feedback #proceso
