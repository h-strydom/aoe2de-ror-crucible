# CLAUDE.md

Guidance for Claude Code working in this repository.

## What this is
A Crucible-style roguelite campaign for AoE2 DE Return of Rome (AoE4's Crucible: survive runs, spend what you earn
in a hub on upgrades that carry over). Scenarios and the campaign are built from code with aoe-agent-editor
(`../aoe-editor`, github.com/h-strydom/aoe-agent-editor), pinned in pyproject.toml.

## Working rules
- Build bottom up: settle what the engine can do (the test map) before designing on it.
- Commit after each step, with a clear message. Ask before pushing.
- When the toolkit falls short, extend aoe-agent-editor instead of working around it here.
- The user playtests in game themselves: give a short checklist of what to look for, then read results.
- Record what a playtest proves in aoe-agent-editor's engine-facts guide; mark guesses as unverified.
- No AI cheats: no free units, free resources or full map reveal for computer players.
