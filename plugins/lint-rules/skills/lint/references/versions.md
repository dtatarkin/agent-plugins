---
paths:
  - "**/.pre-commit-config.yaml"
---

# Versions

**No topic of this standard states a version.** The hook entries are canonical;
the `rev:` values are not. Versions are fetched from upstream at the moment the
rules are applied, which is why two repositories converged on different days
carry different pins and still run the same standard.

## The pin

Each hook repository's `rev:` is **the newest release tag at least seven days
old**, pinned **by tag**. Not by commit hash: a hash is unreadable in review and
defeats the age comparison. A release younger than the cooldown is skipped and
picked up on a later touch — the cooldown exists because a linter's first
release of the day is the one that breaks a build, and seven days is long
enough for that to surface in someone else's repository instead of yours.

A lockfile the repository tracks resolves under the same cooldown, and the
language topic gives the setting.

## The command

```text
prek update --cooldown-days 7 --repo-exclude-tag https://github.com/crate-ci/typos=v1
```

Never pass `--freeze`: it rewrites every pin to a commit hash.

The spelling checker's repository publishes a **moving major tag** beside its
real releases, and the moving tag is the reason for the exclusion flag: a pin
that lands on it silently tracks whatever was released last, cooldown and all.
Exclude it by name so the pin lands on a real release. Version ordering may
prefer the real release on its own on any given day — keep the flag regardless,
because that is a property of the tool's sort, not a promise from the
repository.

**`pre-commit autoupdate` is not this procedure.** It knows no cooldown, so it
takes today's release; and it prefers the moving tag, so it moves a good pin
backwards onto it. Use it only as a fallback when the updater is unavailable,
and then check every date by hand.

## Checking the age

The updater applies the cooldown but does not report the date it chose, so
**verifying a pin is old enough is a separate act**: read the tag's publication
date from the hook repository's releases and compare it against the day.

Some repositories publish no releases at all — only tags. There the tag object's
own date is the date, and the check says so rather than reporting nothing found.

## Staying runnable by the reference implementation

pre-commit is the reference implementation of this configuration format; prek
is a faster reimplementation that reads the same file and can also run it. A
repository may be committed to from a machine that has only one of them, and
that machine is usually not yours — so the configuration must run under **plain
pre-commit**: no key, no syntax and no hook form that only the faster tool
understands.

Check it rather than assume it. Where pre-commit is not installed,
`uvx pre-commit validate-config` is the check and costs one command; validating
with the tool that wrote the file proves only that it can read its own output.

This is a property of the artifact, not of your machine. Which runner you have
is your business; which runners the file works under is the repository's.

## Convergence, not a sweep

Versions converge **when the repository does**. A repository converged today
carries today's pins; one converged next month carries next month's. There is
no estate-wide bump, because a sweep updates repositories nobody is working
in — every one of those pins then has to be proven safe by someone who was not
there when it moved.
