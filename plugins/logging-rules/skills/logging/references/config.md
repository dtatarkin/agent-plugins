# Logging — configuration

Recommendations for wiring up logging. Prefer these defaults; deviate when a
situation genuinely warrants it.

1. Configure logging once, centrally — a single structlog `ProcessorFormatter`
   dictConfig that renders stdlib records to JSON in production and a colored
   console in development. Do not hand-roll handlers or formatters per service
   or per entrypoint; share the one config across every entrypoint (web server,
   workers, tasks). Drive it from env vars validated the way the general Python
   `config` rule says (a `LOG_` prefix for level, formatter, and per-logger
   overrides). The processor chain enriches every record (timestamp,
   log level, logger name, callsite, merged contextvars), so never add those
   fields manually at call sites. The canonical implementation is
   `biased.logging.configure_logging`, applied once per entrypoint and driven
   by `LoggingConfig` (`LOG_LEVEL`, `LOG_FORMATTER`, `LOG_LEVELS__<logger>`,
   `LOG_COLORS`). A service that needs other defaults subclasses
   `LoggingConfig` and overrides the field defaults; it does not pass kwargs,
   because init kwargs beat the environment and would silence the variables.
