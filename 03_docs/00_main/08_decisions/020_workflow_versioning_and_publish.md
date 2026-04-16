# ADR-020: Workflow Versioning and Publish Model

**Status:** Accepted  
**Date:** 2026-04-10

---

## Context

Flows are edited visually and may eventually drive live routes, policies, and
side effects. That means the system needs a strict versioning model.

If published workflows can change in place, the platform becomes difficult to
debug and impossible to reason about historically.

## Decision

Workflows use a draft-and-publish model with immutable published versions.

## Workflow States

Each workflow definition may have:

- one editable `draft`
- zero or more immutable published versions
- one optional current `active` published version

## Publish Rule

Publishing a workflow:

1. validates the draft
2. freezes the graph and metadata into a new immutable version
3. marks that version as the active version for new runs

Existing runs keep pointing to the exact version they started with.

## Mutation Rule

Published workflow versions are immutable.

Any change to:

- nodes
- edges
- config
- trigger binding
- route binding

creates a new published version through the draft.

## Run Binding

Every run records:

- workflow id
- workflow version
- trigger type
- execution timestamps
- node run references

Run inspection must always show the exact graph version that executed.

## Node Compatibility

Workflow versions point to node keys and contract versions valid at publish time.

If a node contract changes incompatibly, existing published workflows must not
silently adopt the new behavior. They must either:

- keep using the old compatible node contract, or
- require explicit republish after migration

Silent in-place contract mutation is forbidden.

## Draft Simplicity

v1 supports only one draft per workflow definition.

Concurrent draft branching is out of scope.

## Consequences

- runs are reproducible and explainable
- publishing becomes the stability boundary
- frontend editing stays simple
- node and workflow evolution can happen without hidden behavioral drift
