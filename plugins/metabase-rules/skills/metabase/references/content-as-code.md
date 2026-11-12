---
paths:
  - "**/mbtf.yml"
  - "**/mb-gen-*.tf"
---

# Metabase content kept as code

A project that keeps Metabase content as code declares it as resources of the
community Metabase Terraform provider (`flovouin/metabase`) and generates
those declarations with the provider's importer, `mbtf`.

1. **Managed content is the database connection, the collections, the cards
   and the dashboards, and the table metadata they reference.** Anything
   else in an instance is not in the configuration, so an apply neither
   creates nor restores it.
2. **Author in a development instance, then import.** A managed dashboard or
   question is created and changed in the instance, and reaches the
   repository as a diff of files the importer regenerates. Building a
   question in the interface is what Metabase is for; writing its JSON by
   hand is not.
3. **Never edit a generated file.** The next import overwrites it, so a
   correction made there is lost without a trace. Make it in the instance, or
   in the importer's configuration.
4. **An instance that receives the configuration by apply is changed only by
   apply.** A hand edit of managed content there is reverted by the next
   apply. Asked for one, say that it will not survive and route the change
   through the development instance.
5. **Commit only portable configuration.** Every database, collection, table,
   field and card a generated file mentions must be a reference to a
   Terraform resource or data source; an integer id of the instance it was
   read from must not stand in for any of them. Read the files before
   committing, because neither the plan nor the apply shows the defect: the
   configuration applies cleanly elsewhere and the card fails, or queries the
   wrong object, when it is run. The places an id hides:
   - `database`, `collection_id`, `card_id`;
   - `source-table` and `source-card`;
   - the id of a `["field", …]` clause, before or after its options, and
     `source-field` inside those options;
   - a native query's `{{#<id>}}` and the `card-id` of its template tag.
6. **A raw id left behind is the importer's defect.** Do not commit the file
   and do not patch the id in it — the next import would put it back. Report
   which reference was not rewritten.
7. **Say what is not carried before importing or applying, and never present
   the result as a complete copy.** The provider does not carry a card's
   model type, SQL snippets, segments, alerts and subscriptions, or instance
   settings.
   - A model in the import set is created elsewhere as a plain question: say
     so and ask whether that is acceptable.
   - A native query that uses a snippet needs that snippet to exist in the
     target instance by other means: say so.
8. **Managed content lives in a collection named in the importer's mapping.**
   That mapping is the explicitly specified target, so the default of placing
   new entities in a personal collection does not apply to it; the importer
   also refuses a card whose collection it was not given.
9. **For managed content, native SQL is pushed down into a saved question,
   not a model**, since the model type would be lost on the way to another
   instance. The query-builder questions built on top of it are unaffected.
10. **Try an import or an apply on a throwaway instance.** A check of the
    importer or of generated configuration runs against an instance created
    for it and discarded after, with credentials generated for it and never
    printed. A project's real instance is not written to without the user's
    say for that run.
