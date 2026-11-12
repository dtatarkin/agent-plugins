---
paths:
  - "**/justfile"
  - "**/.just"
---

# Reuse before you author

The strongest convention: **don't re-implement what a shared module already
does.** Where a shared module set is vendored, `mod` its modules instead of
writing local git / submodule / lint / format recipes:

```just
mod just          '../justfiles/just.just'
mod git           '../justfiles/git.just'
mod git-submodule '../justfiles/git-submodule.just'
mod pre-commit    '../justfiles/pre-commit.just'
```

A project's own `justfile` then shrinks to those `mod` lines plus the handful of
recipes genuinely specific to the project. Catching yourself writing a generic
`git push`, `submodule update` or `pre-commit run` recipe means the shared one
exists already — stop and load the module instead.
