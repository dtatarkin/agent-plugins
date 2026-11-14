---
paths:
  - "**/models.py"
  - "**/models/*.py"
---

# Django models — recommendations

Recommendations for the shape of a model class: its file, `__str__`, mixins,
managers and `Meta`. Prefer these defaults; deviate when a situation genuinely
warrants it.

## Files

1. Lay out and name model files as the app-structure rules state.

## Representation

2. In `__str__`, return the identifying field values directly — **no
   `ClassName(...)` wrapper**. The default `__repr__` already renders
   `<ClassName: {str(self)}>`, so repeating the class name doubles it. List the
   pk plus the few fields that make the row recognizable at a glance
   (`f"{self.id}, {self.customer_id}, {self.status}"`), or a structural glyph
   when it reads better (`f"{self.source_id}->{self.target_id}"`). Surface FK
   ids via `<field>_id` (never the related object, which triggers a query) and
   choice labels via `get_<field>_display()`.

## Mixins & managers

3. Prefer one shared abstract timestamp mixin — such as
   `CreatedAtModifiedAtMixin` in
   `biased.django.models.created_at_modified_at_mixin`: `created_at` set on
   add, `modified_at` on every save, both `editable=False` — over per-model
   timestamp fields. Every table then carries the same two columns with the
   same meaning, and a query or admin filter written for one works on all.
4. Factor any other recurring field cluster into an abstract mixin
   (`class Meta: abstract = True`) and combine several by inheritance on the
   concrete model. The cluster is then declared, migrated and changed in one
   place.
5. Build custom managers and querysets by composing reusable manager mixins —
   such as the soft-delete manager in `biased.django.models.deleted_at_mixin` —
   and expose query intent as queryset methods (`not_deleted()`). A named
   method states the intent once and chains with other filters; the same
   `filter(...)` repeated at call sites drifts when the meaning changes.

## Meta & docs

6. Declare in `Meta` only what the defaults get wrong. Set `verbose_name` only
   to keep an initialism's casing: Django lowercases the class name, so
   `APIKey` shows as "Api key" until `verbose_name = "API key"`. Leave
   `ordering` unset: a default ordering adds a sort to every query, including
   those that never needed one, so order in the query that does.
7. Set `verbose_name_plural` whenever the default plural would be wrong.
   Django derives the plural by appending a bare `"s"` to `verbose_name` — it
   does no real English pluralization — so any model whose name doesn't
   pluralize by `+s` needs an explicit plural, or the admin shows mangled
   labels (`Category` → "Categorys", `Person` → "Persons").
8. Document a non-obvious model with a class docstring stating its grain and
   meaning, and its fields with `help_text`, above all the reason a field is
   nullable. The docstring is read where the model is used and `help_text` in
   the admin form, so the meaning travels with the column instead of living in
   someone's memory.
