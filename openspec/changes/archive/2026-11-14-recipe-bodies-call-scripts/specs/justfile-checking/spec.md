# Spec Delta

## MODIFIED Requirements

### Requirement: The mechanically checkable rules are enforced

The checker SHALL report: a public recipe without a `[doc("…")]` attribute; a
private recipe carrying `[doc("…")]`; a recipe named with a leading underscore
but not marked `[private]`, or marked `[private]` without the underscore; a
variadic parameter interpolated into a recipe body, except inside a quoted
command string that a nested shell re-evaluates (the rules' `git submodule
foreach` case); a recipe body that holds a script — a shebang body of any
interpreter or length, or a body of more than two lines; and a `*.just` file
loaded with `mod` that lacks `source_file := source_file()` or a `list`
recipe. It SHALL NOT report formatting: whether a file is formatted as
`just --fmt` would format it belongs to the repository's own formatter hook,
which pins its own `just`. It SHALL NOT report rules that need judgment —
reusing the shared modules, grouping recipes, preferring dependency calls to
`just …` bodies, placing `[no-cd]`, choosing `mod?` or `import?`, whether one
line chains too many commands — which reach the agent through attachment only.

#### Scenario: A recipe carries its help in a comment

- **WHEN** a public recipe has a `#` comment above it and no `[doc("…")]`
- **THEN** the checker reports it

#### Scenario: A variadic is spliced into a body

- **WHEN** a recipe interpolates `{{ args }}` from a `*args` parameter into its
  body
- **THEN** the checker reports it, unless the interpolation sits inside a quoted
  command that a nested shell re-evaluates

#### Scenario: A body has a shebang

- **WHEN** a recipe body opens with a shebang
- **THEN** the checker reports it, whatever the interpreter and however short
  the body

#### Scenario: A multi-line body has no shebang

- **WHEN** a recipe body has three or more lines and no shebang
- **THEN** the checker reports it

#### Scenario: A body is a command or two

- **WHEN** a recipe body has one or two lines and no shebang
- **THEN** the checker reports nothing about its length

#### Scenario: A file is unformatted

- **WHEN** a file is not formatted as `just --fmt` would format it and breaks
  no other checked rule
- **THEN** the checker reports nothing for it

#### Scenario: A sub-repository's justfile is loaded as a module

- **WHEN** an umbrella loads a sub-repository's `justfile` with `mod`
- **THEN** the module preamble is not required of it, since it is its own
  repository's entrypoint

#### Scenario: A judgment rule is broken

- **WHEN** a recipe re-implements what a shared module already offers
- **THEN** the checker reports nothing for it
