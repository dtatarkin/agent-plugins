---
name: logging
description: Logging conventions — call-site style (event-name messages, structured context, error and level usage) and centralized configuration. Load when adding or changing log calls or logging setup, independent of framework.
---

# Logging rules

This skill is a **router**. It holds no rules itself — the canonical rules live
in this skill's `references/` directory. Read **only** the topic file(s) relevant
to the change, then follow them.

| You are editing… | Read |
|------------------|------|
| Log call sites — event names, `extra=`, `exc_info`, levels | `references/call-sites.md` |
| Logging setup — dictConfig, formatters, env config | `references/config.md` |

If a change spans both, read each file. Do not guess at the rules — read the file.
