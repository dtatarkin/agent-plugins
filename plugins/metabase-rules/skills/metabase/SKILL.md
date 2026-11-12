---
name: metabase
description: Rules for working with Metabase — query authoring (MBQL vs native SQL), where entities land in collections, and dashboards and questions kept as code with Terraform. Load whenever creating or updating anything in Metabase — questions, dashboards, models, collections — by any mechanism, and before importing, committing or applying Metabase content kept as code.
---

# Metabase rules

This skill is a **router**. It holds no rules itself — the canonical rules live
in this skill's `references/` directory. Read **only** the topic file(s) relevant
to the change, then follow them.

| You are… | Read |
|----------|------|
| Authoring or editing a question or model query (MBQL vs native SQL) | `references/query-language.md` |
| Creating any entity — choosing which collection it lands in | `references/collections.md` |
| Importing, changing, committing or applying dashboards and questions kept as code | `references/content-as-code.md` |
| Writing or changing the Terraform root that holds them — provider, importer, credentials, apply order | `references/terraform-root.md` |

If a change spans several topics, read each relevant file. Do not guess at the
rules — read the file.
