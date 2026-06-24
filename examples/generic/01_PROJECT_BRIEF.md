# 01 — Project Brief

A stable, slow-changing description of the project. Update it when the goal,
scope, or key rules change — not on every task.

## Overview

Project Name is a small service that turns inbound requests into processed
results for an internal team.

## Goals

- Process every inbound request within Feature Y's time budget.
- Keep the codebase small and easy for a new contributor to read.

## Scope

- In scope: Module A (intake), Module B (processing), Service X (storage).
- Out of scope: user-facing UI, billing.

## Important rules

- Service X is the only component that reads or writes the data store.
- Module A validates input before anything else runs.

## Key components

- **Module A** — validates and normalizes inbound requests.
- **Module B** — runs the processing pipeline for Feature Y.
- **Service X** — the single storage gateway.

## Decisions

- 2026-05-10 — Decision: Service X owns all storage access. Why: avoid scattered
  data logic and make the data store easy to swap later.

## Next steps

- Add retry handling to Module B.
- Document Service X's error codes.
