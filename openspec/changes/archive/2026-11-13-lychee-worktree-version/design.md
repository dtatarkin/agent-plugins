# Design

## Context

See proposal.md for why. The checker compares a house hook's arguments
against `HOOK_CANON`, which names flags that must be present anywhere in the
command line. The version override is different in two ways: upstream reads
it only as the first argument, and its value is derived from the
repository's `rev:`, which `_check_args` does not see.

## Decisions

1. **A separate rule, not a `Canon` flag.** The override's position and its
   value depend on the pin, so it is checked in its own function that is
   handed the hook's `rev:`. The existing flag check keeps passing, because
   `_has_flag` finds `--offline` and `--no-progress` wherever they sit.
2. **Only the hosted script hook is checked.** The rule applies to a hook
   with id `lychee` from the lycheeverse repository. A local entry with that
   id is the project's own command, which the standard does not reach.
3. **The expected version is the `rev:` without `lychee-v`.** When the pin is
   not a `lychee-v*` tag, no version can be derived. The checker then asks
   only that some override comes first, and leaves the tag itself to the
   pinning procedure.
4. **The override's value is reported verbatim** in the finding, with the
   expected one, so a stale override is fixed by reading the message.

## Risks / Trade-offs

- If upstream drops the `LYCHEE_VERSION=` argument, every converged
  configuration breaks together. The override is upstream's documented fix,
  and the version-bump procedure already reads the release before moving.

## House rules

- lint-rules: `references/markup.md` and `references/versions.md` change; the
  entry stays the hosted script hook. `.pre-commit-config.yaml` follows the
  amended entry.
- python-rules: the new rule follows the existing `_check_*` generator shape
  and its tests the existing parametrised edits of the fixture tree.
- plugin-rules prose.md: the reason is stated inline beside the entry, and no
  consuming project is named.
- None broken.
