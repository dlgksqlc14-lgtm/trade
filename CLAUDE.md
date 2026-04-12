# Project Rules

## Session Init

When starting a new session, always:
1. Read this file first
2. Read `doc/project/README.md` for project overview
3. Identify which feature/project context is relevant to the current task
4. Check `doc/project/<feature>/` for existing design, plan, and implementation docs

## Documentation Structure

All project documentation lives under `doc/`:

```
doc/
  project/
    README.md              # Project overview & feature index
    <feature-name>/
      design/              # Design decisions, architecture
      plan/                # Task plans, roadmaps
      implement/           # Implementation notes, specs
      result/              # Results, retrospectives, learnings
```

- Each feature gets its own directory under `doc/project/`
- Documents are accumulated over time -- do not overwrite, add new files
- File naming: `YYYY-MM-DD-<short-description>.md`

## Coding Conventions (Kent Beck Style)

- **Simple Design**: code passes all tests, reveals intention, has no duplication, fewest elements
- **Small methods**: each method does one thing, named clearly for what it does
- **No premature abstraction**: duplication is cheaper than wrong abstraction -- wait for 3 occurrences
- **Test first**: write failing test, make it pass, refactor
- **Incremental change**: small commits, each one leaving the code better than before
- **Clear naming**: names tell the reader what, not how. Avoid abbreviations
- **Flat over nested**: prefer early returns, avoid deep nesting
- **Composition over inheritance**

## Script Project Conventions

- Scripts live in `scripts/` directory
- Each script is self-contained and executable
- Include usage/help output when run without arguments
- Use clear exit codes (0 = success, 1 = error)

## General Rules

- Respond in the same language the user writes in
- Read existing docs before proposing changes
- When starting a new feature, create its doc structure first
- Keep code simple -- complexity is a last resort
