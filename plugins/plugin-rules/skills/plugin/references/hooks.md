---
paths:
  - "**/hooks/hooks.json"
---

# Plugin hooks

Binds every plugin that ships hooks, conventions or not.

- **Declare a plugin's hooks in `hooks/hooks.json` at its root**, and nowhere
  else. Hooks declared there run only in projects where the plugin is enabled,
  their subagents included, and in no other project.
- **Resolve each hook command to a script inside the plugin, or to a console
  script the plugin's own repository installs.** Anything else may be missing
  on the machine that runs it.
- **Declare each hook in exec form**: the command and its arguments given
  separately. No shell then stands between the harness and the command, and no
  shell prefix a project sets wraps it or mixes its output into the stream the
  harness reads. A command given as one string with no separate arguments is
  shell form.
- **Check form and resolution before commit**; hold them with a test where the
  repository has one, failing with the event and the command.
- **Prove a hook by observing its effect in a running session**, never by
  inferring it from the file's presence. A hook that fails does so silently: a
  command that is not installed shows only as a missing effect.
