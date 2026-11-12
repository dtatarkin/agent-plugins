# The Terraform root that holds Metabase content

What is specific to a root declaring Metabase content with the community
provider (`flovouin/metabase`) and its importer, `mbtf`. Layout, state and
modules are the same as for any other root.

1. **The root lives in the project's own repository**, beside what it
   reports on, so that a change to the data and the change to the dashboards
   reading it are reviewed together.
2. **Pin the provider to one exact version, not a range.** The provider
   compares the JSON of cards and dashboards with what Metabase returns, and
   how it does so changes between releases. A new version must arrive as a
   reviewed change with its own plan, not as whatever `init` resolved that
   day.
3. **The importer is a build of one fixed source revision, declared in the
   project's pinned environment.** It is published as source only, so every
   use is a build, and the revision is what makes two imports comparable.
   Never install it machine-wide, and never run a build whose revision the
   project does not declare. Outside the project's environment the importer
   is absent, and that is the intended outcome.
4. **Credentials reach the tooling through the environment of the process
   that needs them, and nowhere else** — not committed configuration, not a
   variable file, not a plan, not state.
   - The importer takes its API key from an environment variable; its
     configuration file names none.
   - Terraform takes the API key through a variable that is both `sensitive`
     and `ephemeral`, set from the environment.
   - A database password goes through the provider's write-only attribute,
     fed by an ephemeral variable, with its version counter raised to send a
     rotated value. A plain attribute would write the password into state.
     Write-only attributes need Terraform 1.11 or later.
5. **Apply the database before what reads its schema.** A table is declared
   by looking it up, and Metabase only knows a table once it has finished
   reading the database's schema, which a single apply does not wait for.
   On an instance that does not hold the database yet: apply the database
   alone, wait for the schema read, then apply tables, cards and dashboards.
6. **The recipe for that two-phase apply belongs to the project that needs
   it.** It moves to shared tooling only when a second project needs the
   same, because one use does not show what is generic.
