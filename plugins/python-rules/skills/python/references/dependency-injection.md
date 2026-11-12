# Dependency injection — recommendations

Recommendations for wiring dependencies. Prefer these defaults; deviate when a
situation genuinely warrants it.

1. Inject dependencies with the `injector` library: `@inject` on constructors,
   `get_injector().get(Type)` for dynamic lookup. Declare each package's bindings
   in a `Module` subclass (`injector.py`), composed into one top-level injector.
2. Build the injector once at startup so bindings are wired in a single place.
