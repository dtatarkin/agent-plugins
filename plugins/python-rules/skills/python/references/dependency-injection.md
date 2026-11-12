---
paths:
  - "**/*.py"
---

# Dependency injection — recommendations

Recommendations for wiring dependencies. Prefer these defaults; deviate when a
situation genuinely warrants it.

1. Inject dependencies with the `injector` library: `@inject` on constructors,
   `get_injector().get(Type)` for dynamic lookup. Declare each package's bindings
   in a `Module` subclass (`injector.py`), composed into one top-level injector.
   A class then declares what it needs instead of constructing it, so a test
   or another deployment swaps an implementation by changing a binding, not
   the class.
2. Build the injector once at startup so bindings are wired in a single place.
   A singleton belongs to the injector that made it, so a second injector
   would quietly create a second instance.
