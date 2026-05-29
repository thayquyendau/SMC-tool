---
name: review-scope-guard
description: Enforce GitHub review-comment driven edits with strict scope control. Use when implementing reviewer feedback while avoiding unrelated file changes.
---

# Review Scope Guard

Use this skill when coding from GitHub review comments and you want strict control over change scope.

## Core Rules

1. Only change files directly related to reviewer comments.
2. Do not refactor unrelated code while fixing review points.
3. Keep existing code style and formatting in touched files.
4. Prefer minimal diffs that are easy for reviewers to re-check.
5. If a requested change implies broader impact, stop and ask before expanding scope.
6. Preserve human-language text exactly, including Vietnamese accents and UTF-8 encoding.

## Workflow

### 1) Parse review comments into actionable items

Convert each reviewer comment into:

- `comment_id`
- `target_file`
- `target_symbol_or_block`
- `requested_change`
- `acceptance_note`

If a comment is ambiguous, ask one focused clarification question before coding.

### 2) Build a scope lock

Before editing, define:

- Allowed files: exact file list from review comments
- Allowed changes: exact behavior requested
- Forbidden changes: cleanup/refactor/renames outside requested scope

Do not edit files outside the allowed list unless:

- build/test is broken by the requested change, and
- you explicitly report and justify the extra file.

### 3) Implement minimally

- Apply the smallest correct change first.
- Preserve interfaces unless comment explicitly requests an API change.
- Add comments only when needed to explain non-obvious logic.

### 4) Self-check before finishing

Run this checklist:

- Each review comment is resolved by a concrete code change.
- No unrelated files changed in `git diff --name-only`.
- No behavior change outside requested scope.
- New/updated tests exist when risk warrants it.
- Vietnamese UI text, prompts, errors, and comments are not mojibake or stripped of accents.

### 5) Report back in review-friendly format

Summarize by comment:

- `comment_id -> files changed -> what changed -> why this satisfies review`

Also include:

- Any assumptions made
- Any intentionally deferred items

## Guardrail Commands

Use these commands frequently during implementation:

```bash
git status --short
git diff --name-only
git diff -- <file>
rg "<symbol_or_text_from_comment>" -n
rg "Ã|Â|Ä|Æ|áº|á»|â€|â„¢" -n
```

If `git diff --name-only` includes unrelated files, remove accidental changes before finalizing.

## Vietnamese Text And Encoding

When touching Vietnamese text:

- Keep files encoded as UTF-8.
- Do not convert Vietnamese text to ASCII unless the file already intentionally uses ASCII-only text.
- After moving prompts/UI copy between files, search for mojibake markers such as `Ã`, `Â`, `Ä`, `Æ`, `áº`, `á»`, `â€`, and `â„¢`.
- If text is already corrupted, restore the intended Vietnamese wording instead of copying the corrupted string forward.

For UI copy-only reviews, only edit visible text, placeholders, titles, and `aria-label` values.

## Non-Goals

- Large refactors not requested by review
- Opportunistic renaming/reformatting
- Cross-module redesign without explicit approval
