# ADR-019: Feature and Node Ownership

**Status:** Accepted  
**Date:** 2026-04-10

---

## Context

The system needs both feature-owned logic and reusable nodes. Without an
ownership rule, the codebase will drift into duplication and blurred
boundaries.

Examples of the problem:

- feature-specific versions of generic nodes
- shared nodes that should really be internal to one feature
- dashboards separated from the feature that owns the underlying behavior

## Decision

Ownership follows the narrowest valid boundary.

### Features own:

- business handlers
- feature-specific dashboards and reports
- feature-specific contracts
- feature-specific nodes and presets

### Shared node catalog owns:

- reusable nodes intentionally used across multiple features
- shared node documentation
- shared node metadata contracts

## Ownership Rule

Use this test:

- if only one feature needs the node, keep it inside that feature
- if at least three features genuinely need the same stable behavior, promote it
  to the shared node catalog

Do not promote a node to shared just because it feels platform-like.

## Dashboard Ownership

Dashboards and reports always belong to the feature that owns the underlying
behavior and data.

Examples:

- IAM auth and access dashboards belong to IAM
- Audit event reporting belongs to Audit
- API route operational views belong to API Gateway

## Cross-Feature Usage

Features may rely on another feature only through declared public contracts.

Examples of valid contracts:

- HTTP API
- event contract
- shared public node contract
- persisted artifact contract

Examples of invalid cross-feature coupling:

- direct table access into another feature's schema
- importing another feature's internal service layer
- depending on undocumented internal node behavior

## Presets

Features may publish feature-owned flow presets built from:

- feature-local nodes
- shared nodes

Presets remain owned by the feature even when they reuse shared nodes.

## Consequences

- duplication pressure is reduced
- feature boundaries stay clear
- shared nodes remain intentionally small and stable
- dashboards and reports stay attached to the domains that own them
