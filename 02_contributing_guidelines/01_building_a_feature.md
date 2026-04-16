# Building a Feature

Use this guide when you are defining a new top-level feature boundary.

A feature is a bounded domain, not just a folder.

## What a Feature Owns

A feature owns:

- its business purpose
- its ordered sub-feature backlog
- its architecture boundaries
- its public contracts
- its dashboards and reports

It does not own another feature's internals.

## Required Feature Pack

Create exactly these files first:

```text
03_docs/features/{nn}_{feature}/
├── 00_overview.md
├── 01_sub_features.md
├── feature.manifest.yaml
└── 04_architecture/
    └── 01_architecture.md
```

## Feature Workflow

1. Pick and name the boundary.
2. Write the overview.
3. List the sub-features in build order.
4. Write the architecture doc.
5. Create the feature manifest.
6. Start the first sub-feature.

## What Goes in `00_overview.md`

Keep it short. Answer only:

- what this feature does
- what it owns
- what it does not own
- why it exists
- which other features it depends on

### Minimal template

```markdown
# {Feature Name}

## Purpose
{2-3 sentences}

## Owns
- {owned concern}

## Does Not Own
- {neighbor concern}

## Depends On
- {public contract or feature}
```

## What Goes in `01_sub_features.md`

List the sub-features in the order they should be built.

Each line should say:

- sub-feature name
- what it does
- why it comes in that order

## What Goes in `04_architecture/01_architecture.md`

Answer only:

- the boundary of the feature
- the main internal pieces
- the public contracts exposed to other features
- the contracts consumed from other features
- any invariants that must stay true
- whether the feature owns reusable nodes or only uses them

## What Goes in `feature.manifest.yaml`

Use the smallest useful shape.

```yaml
title: "{Feature Name}"
feature: "{nn}_{feature}"
status: PLANNED
owner: "{owner}"
created_at: "YYYY-MM-DD"
description: |
  {short description}
sub_features:
  - number: 1
    name: {sub_feature_name}
    status: PLANNED
```

Feature status is one of:

- `PLANNED`
- `ACTIVE`
- `DONE`

## Done Criteria

The feature scaffold is ready when:

- the boundary is clear
- the required feature pack exists
- the ordered sub-feature backlog exists
- the architecture doc names public contracts and dependencies
- the first sub-feature can be started without making new structural decisions
