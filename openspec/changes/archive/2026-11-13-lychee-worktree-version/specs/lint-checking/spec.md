# Spec Delta

## ADDED Requirements

### Requirement: The link checker's version override follows its pin

The checker SHALL report the hosted link-checker hook when its first argument
is not `LYCHEE_VERSION=<version>`, and when `<version>` differs from its
repository's `rev:` with the `lychee-v` prefix removed. Where the `rev:` is
not a `lychee-v` tag, the checker SHALL ask only that an override comes first.
A local hook carrying the link checker's id SHALL not be reached.

#### Scenario: The override is absent

- **WHEN** the hosted link-checker hook's arguments are `--offline` and
  `--no-progress` alone
- **THEN** the checker reports the hook, naming the override it owes

#### Scenario: The override is not first

- **WHEN** the override follows `--offline` among the hook's arguments
- **THEN** the checker reports the hook, naming the override it owes

#### Scenario: The override is stale

- **WHEN** the pin is `lychee-v0.24.2` and the override names `0.23.0`
- **THEN** the checker reports the hook, naming both versions

#### Scenario: The override matches its pin

- **WHEN** the pin is `lychee-v0.24.2` and the arguments are
  `LYCHEE_VERSION=0.24.2`, `--offline` and `--no-progress`
- **THEN** the checker reports nothing on the hook
