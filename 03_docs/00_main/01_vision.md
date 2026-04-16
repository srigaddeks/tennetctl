# Vision

## The Problem

Building a serious software product is mostly the same set of decisions over and over again.

Every API or workflow eventually needs the same concerns wired in:

- authentication or not
- feature flag checks or not
- rate limiting or not
- audit events
- logs
- traces
- metrics
- notifications
- dashboards and reports for the owning feature

Teams usually solve this in one of two bad ways:

- bury the concerns inside route handlers until business logic and platform logic are mixed together
- build a visual layer that is disconnected from the backend and turns into documentation theater

Both approaches create drift. The code becomes hard to reason about, and the UI stops matching reality.

## What tennetctl Is

tennetctl is a backend-first platform for building software systems out of self-contained features, reusable nodes, and visual flows.

- A **feature** is a bounded business domain such as IAM, Audit, Feature Flags, or Monitoring.
- A **sub-feature** is the smallest independently scoped capability inside a feature.
- A **node** is a registered runtime building block, usually a Python function with typed config, typed inputs, typed outputs, and runtime metadata.
- A **flow** composes nodes visually so the backend can execute or compile them consistently.

The frontend is not the source of truth. It is the authoring and observability layer over backend-defined contracts.

## The Goal

When building a new capability, the system should make the right structure easy:

- business logic stays in feature-owned backend code
- cross-cutting concerns are added as reusable nodes
- flows show exactly how a capability behaves
- each feature owns its own reports and dashboards
- every unit of work is small enough to scope, build, test, and ship cleanly

The result should feel simple even when the product has tens of features and hundreds of sub-features.

## Who It Is For

tennetctl is built for:

- builders who want a clear backend architecture, not prompt soup
- teams that want visual composition without giving up code ownership
- products that need strong security, observability, and auditability around APIs and workflows
- maintainers who need a documentation system that scales as the product grows

## What tennetctl Will Not Become

- a frontend-only workflow toy with hidden backend behavior
- a system where nodes are untyped arbitrary scripts glued together by convention
- a product where dashboards are separate from the features that own the underlying behavior
- a giant shared abstraction layer where every feature reaches into every other feature's internals
- a platform where process overhead is so high that adding a small capability becomes a project of its own

tennetctl should stay easy because the architecture stays explicit, bounded, and small at the unit-of-work level.
