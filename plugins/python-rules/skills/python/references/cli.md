# CLI — recommendations

Recommendations for building command-line interfaces. Prefer these defaults;
deviate when a situation genuinely warrants it.

1. Build CLIs with `typer`, not the standard-library `argparse`. Declare each
   command as a type-annotated function: Typer derives the arguments, options,
   help text, and validation from the signature and type hints, so there is no
   parser object to wire up and keep in sync with the function it feeds. The same
   annotations that document the function define the interface, and subcommands,
   shell completion, and coloured help come for free. Reach for `argparse` only
   when a strict zero-dependency constraint forbids the extra package.
