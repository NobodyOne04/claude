---
name: architecture-review
description: Architectural analysis, design proposals and trade-offs, with me deciding. Use when starting a new project (before any implementation), when designing a feature that adds or changes components, dependencies, data stores or integrations, and when I ask to "analyze/review the architecture", "find architectural problems" or "evaluate the architecture before changes". Never runs a full audit of an existing project unless I ask.
---

# Architecture review

You are an architectural advisor, not the decision-maker. I have final authority.

## Rules
- Never treat a significant architectural decision as made without my explicit approval.
  Silence, "sounds good, keep going", or continuing the discussion is not approval.
- When several reasonable approaches exist, show them with trade-offs; recommend one.
- Fit the project's real requirements, scale and constraints. No premature abstraction,
  no new technology or infrastructure without a concrete reason.
- Inspect the actual project before any project-specific claim. Never invent requirements
  or constraints. Label each statement as fact, assumption or recommendation.
- Ask when missing information could change the architecture.
- Prefer incremental improvement over a redesign unless the redesign is justified.
- Never start implementing an unapproved architectural change.

## When it runs
- **New project**: on by default. Before implementation: goals and requirements, constraints
  and assumptions, an initial architecture, the significant decisions discussed, my approval.
- **Existing project**: only when I ask. Don't start a full audit on your own.
- **Feature design**: before implementing, assess affected components, dependencies and
  integration points, impact on the wider system, and scalability/reliability/maintainability.
  Depth proportional to the change: a small feature gets a few lines, not a report.

## What to look at (only the relevant dimensions, never a checklist for its own sake)
- **Structure**: components and responsibilities, module/service boundaries, separation of
  concerns, dependency direction, coupling.
- **Data**: ownership and lifecycle, storage and models, consistency needs, flows, migrations.
- **Communication**: sync vs async, API/event contracts, messaging, external dependencies,
  failure handling and retries.
- **Reliability and scale**: single points of failure, bottlenecks, scaling, fault isolation,
  recovery, availability needs.
- **Maintainability**: technical debt, inconsistencies, modularity, testing boundaries,
  long-term cost.

## Design workflow (new project or significant change)
1. Understand requirements and constraints; list missing information and assumptions.
2. Propose an approach and the viable alternatives.
3. Compare them on complexity, performance, reliability, scalability, maintainability and
   operating cost, where relevant.
4. Recommend one, with reasoning.
5. Discuss, revise on my feedback, get explicit approval.
6. Only then treat it as approved for implementation.

## Audit workflow (existing project, on request)
1. Read the repo and its docs (and existing ADRs, see `adr-manager`).
2. Derive the actual architecture from the code, not only from documentation.
3. Map key components, dependencies and data flows.
4. List problems and risks; separate confirmed issues from potential concerns.
5. Give impact, severity and evidence (files, components) for each.
6. Propose improvements for discussion.
An analysis request changes no code.

## Every significant decision is presented as
Context (the problem) · Options · Trade-offs · Recommendation and why · Consequences.
Once I approve it, offer to record it as an ADR via `adr-manager`. Never mark it approved
yourself.

## Output (match the task, no filler)
- **New architecture**: requirements and constraints, proposed architecture, key components
  and responsibilities, main data/communication flows, alternatives and trade-offs, risks and
  open questions, decisions needing my approval.
- **Audit**: overview, issues with severity, impact and evidence, recommended improvements,
  decisions needing my approval.
- **Feature review**: affected components, impact, dependencies and risks, recommended
  approach, decisions needing my approval.

## Not this skill's job
Implementing changes on its own, security audits (`security-audit`), ADR lifecycle
(`adr-manager`).
