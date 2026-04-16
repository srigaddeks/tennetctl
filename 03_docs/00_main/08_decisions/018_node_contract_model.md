# ADR-018: Node Contract Model

**Status:** Accepted  
**Date:** 2026-04-10

---

## Context

ADR-016 establishes that nodes are backend-defined building blocks, usually
implemented as Python functions. That still leaves an important gap: the exact
contract shape for a public node.

Without a standard contract, nodes would become ad hoc callables and the visual
system would not be trustworthy.

## Decision

Every public node is defined by a stable contract with five parts:

1. identity
2. schemas
3. runtime metadata
4. editor metadata
5. backend handler

The handler may be a Python function, but the function alone is not the node.

## Required Node Contract

Every public node must define:

- `key`
- `label`
- `category`
- `kind`
- `config_schema`
- `input_schema`
- `output_schema`
- `handler_ref`
- `retryable`
- `terminal_behavior`

## Node Kinds

Allowed `kind` values are:

- `request`
- `effect`
- `control`

These kinds are stable across the whole product.

## Schemas

Every public node exposes three typed schemas:

- **config schema**: static per-node configuration
- **input schema**: payload expected at execution time
- **output schema**: payload emitted at completion

Schemas are required even if the implementation is very small.

If a node needs no config or no input payload, it still declares an explicit
empty schema.

## Runtime Metadata

Every public node must declare:

- whether it is retryable
- whether it may terminate the current path
- whether it is allowed in `http`, `event`, `manual`, or multiple trigger types
- whether it may emit artifacts

## Editor Metadata

Every public node must expose enough metadata for the frontend to render it
without inventing behavior:

- display label
- category
- short description
- input ports
- output ports
- config fields derived from the config schema

The frontend may not define unofficial node fields outside the backend contract.

## Handler Contract

In most cases the backend handler is a Python function.

The handler receives:

- execution context
- validated config
- validated input payload
- artifact references

The handler returns:

- typed output payload
- artifact references, if any
- structured execution metadata, if any

## Public vs Private Nodes

Only public reusable nodes must follow this contract fully.

Feature-internal helpers may remain plain Python functions as long as they are
not exposed as reusable nodes in flows.

## Consequences

- node behavior is stable and inspectable
- frontend and backend share one contract model
- “node = Python function” stays true in implementation while remaining safe as
  a public architecture
