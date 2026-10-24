# PALIMPSEST: VEX-Morph Dataset Engine

## Project Goal
PALIMPSEST is a high-performance dataset engine designed for Mixed Boolean-Arithmetic (MBA) deobfuscation and term-rewriting analysis, transforming obfuscated abstract syntax trees into canonical, simplified representations using zero-trust verification and theorem proving (Z3).

## Development Conventions
- Strict single-line comments: Use only `#` single-line comments for explanations. Never use multiline docstrings (`\"\"\"` or `'''`) or block comments.
- Minimal-diffs: Keep modifications minimal, surgical, and strictly scoped to required changes. Avoid extraneous whitespace or formatting alterations.
- Zero-trust security: Enforce strict whitelist validation for AST nodes before any evaluation, slicing, or compilation.

## Phase Tracker
- Phase Status: Dataset Phase 3: Opaque Zeros & Sandboxed QF_BV Miter Verifier - Complete
