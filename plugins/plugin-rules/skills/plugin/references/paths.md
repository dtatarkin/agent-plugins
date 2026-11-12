---
paths:
  - "**/skills/*/references/*.md"
---

# Declaring the paths a rule file governs

Binds conventions plugins only; a plugin that operates a tool is not held to it.

- **Attachment on touch is optional.** A plugin that marks no rule file keeps
  router-only delivery, and a rule file without `paths:` does not attach.
- **Declare it in the rule files alone.** Each topic file under the skill's
  `references/` that attaches on touch carries `paths:` frontmatter naming the
  path globs it governs, and that frontmatter is the whole declaration. A
  harness that attaches rules by path then attaches the file when a file
  matching those globs is read.
- **Ship no attachment logic, hook or list of your own.** The frontmatter is
  enough, so a plugin that adopts attachment later adds `paths:` and nothing
  else; no new machinery is written.
