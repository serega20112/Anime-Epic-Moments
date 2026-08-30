---
name: code-review
description: Review local project code for architecture, quality, maintainability, and consistency issues based on project documentation and existing rules. Use when analyzing code quality or preparing a review report.
---

# Code Review Skill

## Purpose

Perform a comprehensive code review of the local project.

The goal is to identify:

- architectural problems
- code quality issues
- violations of project rules
- maintainability problems
- incorrect design decisions

This skill only reviews code.

It does not modify files. It does not implement fixes.

## Working Rules

The review must be based on the project itself.

Priority order:

1. Project documentation
2. Existing architecture decisions
3. Existing code patterns
4. Configuration files
5. General software engineering practices

Do not apply generic recommendations if they contradict project documentation.

## Local Project Analysis

Before reviewing:

Analyze:

- project structure
- source directories
- architecture layers
- dependency flow
- coding conventions

Read available documentation:

- README.md
- docs/
- architecture documentation
- contribution guidelines
- pyproject.toml
- configuration files

Documentation defines project expectations.

## Restrictions

- Work only with local files.
- Do not use git.
- Do not access remote repositories.
- Do not search external documentation.
- Do not modify source code.
- Do not create patches.

## Review Areas

## 1. Architecture Review

Check:

- Clean Architecture violations
- incorrect layer dependencies
- dependency inversion problems
- business logic placement
- excessive coupling
- wrong responsibilities

Examples:

Bad:

```

domain
|
v
infrastructure

```

The domain layer should not depend on infrastructure.

Possible issue:

```

application -> infrastructure

````

Application logic should depend on abstractions.

## 2. Import Review

Check:

- deep imports
- unnecessary internal dependencies
- forbidden imports between layers
- circular dependencies

Example:

Problem:

```python
from src.backend.infrastructure.models.user import UserModel
````

Possible issue:

The code depends on an internal module structure.

Prefer public module boundaries when project design requires it.

## 3. Code Quality Review

Check:

* duplicated code
* unclear naming
* oversized classes
* oversized methods
* unnecessary complexity
* bad exception handling
* incorrect typing
* dead code

## 4. Design Review

Check:

* SOLID violations
* incorrect abstractions
* poor encapsulation
* leaking implementation details
* violation of domain boundaries

## 5. Testing Review

Check:

* missing important tests
* weak test isolation
* incorrect mocking
* tests coupled to implementation details

## Severity Levels

Every issue must have severity:

CRITICAL

The problem can break architecture, security, reliability, or future development.

HIGH

The problem significantly reduces maintainability or violates project principles.

MEDIUM

The problem should be improved but does not immediately break the system.

LOW

Minor improvement or style issue.

## Output Format

Return only a structured review report.

Example:

# Code Review Report

## Summary

Short project review summary.

## Issues

### CRITICAL

1. File:

```
src/application/services/user.py
```

Problem:

Application layer imports infrastructure implementation.

Why:

Creates direct dependency on database implementation.

Recommendation:

Introduce abstraction between layers.

---

### HIGH

2. File:

```
src/backend/api/router.py
```

Problem:

Deep import detected.

Current:

```python
from src.backend.infrastructure.models.user import UserModel
```

Why:

Couples code to internal module structure.

Recommendation:

Use a public module boundary.

---

## Positive Observations

Only mention if they are directly related to architectural decisions.

Do not write generic praise.

## Review Rules

* Every issue must contain a file path.
* Every issue must explain why it matters.
* Do not suggest unrelated refactoring.
* Do not rewrite code.
* Do not fix issues automatically.
* Focus on actionable findings.
