---
name: code-fix
description: Fix issues found during code review in a local project while preserving existing behavior and following project documentation.
---

# Code Fix Skill

## Purpose

Fix problems identified during code review.

The goal is to apply precise corrections while preserving:

- existing functionality
- project architecture
- coding conventions
- documented rules

This skill modifies code only when required.

## Working Rules

All fixes must be based on:

1. Project documentation
2. Existing architecture decisions
3. Existing code patterns
4. Configuration files
5. Review report findings

Project documentation has higher priority than general best practices.

Do not introduce changes that contradict the project design.

## Restrictions

- Work only with local files.
- Do not use git.
- Do not access remote repositories.
- Do not search external documentation.
- Do not perform unrelated refactoring.
- Do not rewrite working code without a reason.
- Do not change business logic unless the review issue requires it.

## Before Fixing

Analyze:

- project structure
- affected files
- architecture layers
- existing implementations
- project documentation

Understand the reason behind each issue before modifying code.

## Fix Strategy

For every issue:

1. Locate the affected code.
2. Understand the root cause.
3. Apply the smallest correct change.
4. Preserve existing APIs where possible.
5. Keep the project style consistent.
6. Check that the fix does not create new architectural problems.

## Architecture Fixes

When fixing architecture issues:

Prefer:

- moving abstractions closer to business logic
- introducing interfaces when required
- removing incorrect dependencies
- restoring correct dependency direction

Avoid:

- moving code randomly between folders
- creating unnecessary abstractions
- adding layers without architectural purpose

Example:

Problem:

```

application
|
v
infrastructure

```

Possible fix:

```

application
|
v
interface
|
v
infrastructure

````

The application layer should depend on abstractions, not implementations.

## Import Fixes

When fixing imports:

Check existing module structure first.

Example:

Problem:

```python
from src.backend.infrastructure.models.user import UserModel
````

Possible fix:

```python
from src.backend.infrastructure.models import UserModel
```

Only apply this if the project structure supports the public import boundary.

Do not create unnecessary `__init__.py` exports only to hide bad architecture.

## Code Quality Fixes

Allowed:

* remove duplicated logic
* simplify complex code
* improve typing
* improve naming
* split oversized methods
* remove unnecessary coupling
* improve exception handling

Forbidden:

* changing requirements
* changing public API contracts without reason
* changing database structure without request
* replacing working implementations with personal preferences

## Testing

After changes:

Check:

* affected tests
* type consistency
* import consistency
* architecture rules

Do not write tests unless:

* the fix changes behavior
* the existing issue requires test coverage
* the project already expects tests for this case

## Output Format

After completing fixes, provide:

# Fix Report

## Changed Files

List modified files.

Example:

```
src/application/services/user.py
src/domain/interfaces/repository.py
```

## Fixed Issues

For each fixed issue:

* original problem
* applied solution
* reason for the change

Example:

```
Problem:
Application depended on infrastructure implementation.

Fix:
Moved dependency to repository abstraction.

Reason:
Restored dependency inversion principle.
```

## Verification

Report performed checks:

* imports checked
* tests checked
* typing checked
* architecture consistency checked

## Rules

* Fix only confirmed problems.
* Prefer minimal changes.
* Do not refactor unrelated code.
* Do not hide problems instead of solving them.
* Do not modify documentation unless the code change requires it.

