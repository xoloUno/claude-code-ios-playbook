---
description: Session health monitoring — context window awareness and recovery
globs: **/*
---

# Session Health Rule

## Context Window Awareness

Claude Code sessions degrade as the context window fills. Watch for these signals:
- **Repeated mistakes** on things that worked earlier in the session
- **Forgetting earlier decisions** or re-asking settled questions
- **Increasingly generic responses** that don't reference project specifics
- **Tool calls failing** on paths or names that were correct before

When you notice degradation:
1. Commit current work immediately (even if partial)
2. Push to the working branch
3. Tell the user: "This session's context is getting long. I recommend starting a fresh
   session — I've committed and pushed current progress so the next session can pick up
   cleanly."

## Proactive Checkpointing

For long sessions (multiple features or a complex debugging arc):
- Commit after each logical milestone, not just at session end
- Update WORKLOG.md incrementally if the session is producing many changes
- If the user hasn't committed in a while and changes are accumulating, suggest a checkpoint

## Recovery After Crash or Disconnect

If a session starts and finds uncommitted changes from a previous session:
1. Run `git status` and `git diff` to understand what's there
2. Show the user a summary of uncommitted changes
3. Ask whether to commit them, stash them, or discard them
4. Do NOT silently overwrite or discard — those changes may represent hours of work
