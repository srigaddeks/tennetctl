---
type: community
cohesion: 0.14
members: 21
---

# Feature Flag Evaluations Node

**Cohesion:** 0.14 - loosely connected
**Members:** 21 nodes

## Members
- [[.run()_58]] - code - backend/02_features/09_featureflags/sub_features/05_evaluations/nodes/featureflags_evaluations_resolve.py
- [[Deterministic bucketing hash(flag_key + entity_id) mod 100  percentage.]] - rationale - backend/02_features/09_featureflags/sub_features/05_evaluations/service.py
- [[EvaluationsResolve]] - code - backend/02_features/09_featureflags/sub_features/05_evaluations/nodes/featureflags_evaluations_resolve.py
- [[Fetch attr from context. Supports dotted paths like 'user.email'.]] - rationale - backend/02_features/09_featureflags/sub_features/05_evaluations/service.py
- [[Find the highest-precedence override among the given entity pairs.     Precedenc]] - rationale - backend/02_features/09_featureflags/sub_features/05_evaluations/service.py
- [[Input_55]] - code - backend/02_features/09_featureflags/sub_features/05_evaluations/nodes/featureflags_evaluations_resolve.py
- [[Output_55]] - code - backend/02_features/09_featureflags/sub_features/05_evaluations/nodes/featureflags_evaluations_resolve.py
- [[Pick the most-specific flag matching the context. application  org  global.]] - rationale - backend/02_features/09_featureflags/sub_features/05_evaluations/service.py
- [[Resolve a flag_key + environment + context into       {value, reason, flag_id,]] - rationale - backend/02_features/09_featureflags/sub_features/05_evaluations/service.py
- [[_context_get()]] - code - backend/02_features/09_featureflags/sub_features/05_evaluations/service.py
- [[_eval_condition()]] - code - backend/02_features/09_featureflags/sub_features/05_evaluations/service.py
- [[_get_env()]] - code - backend/02_features/09_featureflags/sub_features/05_evaluations/service.py
- [[_get_flag_state()]] - code - backend/02_features/09_featureflags/sub_features/05_evaluations/service.py
- [[_in_rollout()]] - code - backend/02_features/09_featureflags/sub_features/05_evaluations/service.py
- [[_load_rules()]] - code - backend/02_features/09_featureflags/sub_features/05_evaluations/service.py
- [[_lookup_overrides()]] - code - backend/02_features/09_featureflags/sub_features/05_evaluations/service.py
- [[_resolve_flag_by_scope()]] - code - backend/02_features/09_featureflags/sub_features/05_evaluations/service.py
- [[evaluate()]] - code - backend/02_features/09_featureflags/sub_features/05_evaluations/service.py
- [[featureflags.evaluations.resolve — control node (read-only).]] - rationale - backend/02_features/09_featureflags/sub_features/05_evaluations/nodes/featureflags_evaluations_resolve.py
- [[featureflags_evaluations_resolve.py]] - code - backend/02_features/09_featureflags/sub_features/05_evaluations/nodes/featureflags_evaluations_resolve.py
- [[service.py_35]] - code - backend/02_features/09_featureflags/sub_features/05_evaluations/service.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Feature_Flag_Evaluations_Node
SORT file.name ASC
```

## Connections to other communities
- 3 edges to [[_COMMUNITY_Node Catalog & Feature Implementations]]
- 3 edges to [[_COMMUNITY_Service & Repository Layer]]
- 3 edges to [[_COMMUNITY_API Routes & Response Handling]]
- 2 edges to [[_COMMUNITY_Auth & Error Handling]]

## Top bridge nodes
- [[evaluate()]] - degree 13, connects to 3 communities
- [[_eval_condition()]] - degree 5, connects to 2 communities
- [[service.py_35]] - degree 10, connects to 1 community
- [[_get_flag_state()]] - degree 5, connects to 1 community
- [[Output_55]] - degree 3, connects to 1 community