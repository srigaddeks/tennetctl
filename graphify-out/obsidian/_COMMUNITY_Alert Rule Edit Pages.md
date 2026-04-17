---
type: community
cohesion: 1.00
members: 3
---

# Alert Rule Edit Pages

**Cohesion:** 1.00 - tightly connected
**Members:** 3 nodes

## Members
- [[AlertRuleEditor component]] - code - frontend/src/features/monitoring/_components/alert-rule-editor.tsx
- [[Monitoring Edit Alert Rule Page]] - code - frontend/src/app/(dashboard)/monitoring/alerts/rules/[id]/page.tsx
- [[Monitoring New Alert Rule Page]] - code - frontend/src/app/(dashboard)/monitoring/alerts/rules/new/page.tsx

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Alert_Rule_Edit_Pages
SORT file.name ASC
```
