# Architecture

The TKM-oriented architecture separates logical responsibilities into specialized contexts (`W_i`). The goal is not only to store facts, but also to preserve enough structure to reason about applicability, discriminate useful dimensions, and support descriptive inversion back toward language-oriented representations.

## High-level flow

```text
Natural language input
        |
        v
TKM orchestrator / parser
        |
        +--> symbol grounding and registry updates
        +--> context expansion when new objects or dimensions appear
        v
Unified matrix engine
        |
        +--> V_i  truth values
        +--> S_i  applicability / sense mask
        +--> O_i  observed facts mask
        +--> D_i  discriminative mask
        v
Queries, validation, composition, and routing
```

## Main architectural pieces

1. `SymbolRegistry`
   Maps external signs to internal symbols and keeps the reverse lookup needed for reconstruction and synonym handling.
   - Code reference: `src/unified_engine.py`

2. `Context`
   Defines a logical world: objects, properties, metadata, and the current set of facts.
   - Code reference: `src/unified_engine.py`

3. `Bridge`
   Connects objects across contexts so the engine can compose or route information between logical spaces.
   - Code reference: `src/unified_engine.py`

4. `UnifiedMatrixEngine`
   Builds and operates over the four structural masks per context and exposes higher-level operations such as status evaluation, bridge routing, and information energy.
   - Code reference: `src/unified_engine.py`

5. `TKMOrchestrator`
   Produces LLM-facing prompts and applies the resulting mapping decisions back into the engine.
   - Code reference: `src/tkm_orchestrator.py`

## Interpreting the four matrix layers

- `V_i` stores factual truth values, including explicit unknown and not-applicable states.
- `S_i` decides whether a proposition is meaningful for an object in a given context.
- `O_i` marks facts that were explicitly grounded or observed.
- `D_i` suppresses dimensions that fail to discriminate between objects.

## Context design pattern

In practice, the repository uses the idea of several cooperating context types:

- lexical contexts for sign-to-symbol handling
- structural or syntactic contexts for templates and constraints
- factual contexts for the truth-bearing layer
- bridge contexts for cross-context routing

These are modeling roles rather than rigid classes. The actual implementation centers on `Context`, `Bridge`, and `UnifiedMatrixEngine`.

## Routing and inversion

Descriptive inversion works by moving from a fact-bearing context toward the structures that can explain or reconstruct it:

1. Identify the target fact or proposition.
2. Follow bridge relations across contexts when needed.
3. Recover the relevant symbols, templates, or structural constraints.
4. Reconstruct a language-facing representation from those linked pieces.

The routing primitives live in `src/unified_engine.py`, especially the bridge and dimensional-collapse logic.
