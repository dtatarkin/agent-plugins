# Django models — recommendations

Recommendations for writing Django models, fields, managers, and querysets.
Prefer these defaults; deviate when a situation genuinely warrants it.

## Structure & files

1. Prefer one model per file inside a `models/` package, re-exporting each model
   from `models/__init__.py`. The file name is the snake_case of the model, in
   full — `LedgerEntry` lives in `models/ledger_entry.py`, never a shortened
   `models/entry.py`: a class has to be findable from its name. The model names
   the file, whatever private helper classes sit beside it. The naming is
   guarded by a test; the app-structure rules state it.
2. Prefer a shared abstract timestamp mixin
   (`biased.django.models.created_at_modified_at_mixin.CreatedAtModifiedAtMixin` —
   `created_at` auto-set on add, `modified_at` auto-set on save, both
   `editable=False`) over per-model timestamp fields.
3. In `__str__`, return the identifying field values directly — **no
   `ClassName(...)` wrapper**. The default `__repr__` already renders
   `<ClassName: {str(self)}>`, so repeating the class name doubles it. List the
   pk plus the few fields that make the row recognizable at a glance
   (`f"{self.id}, {self.customer_id}, {self.auth_state}"`), or a structural glyph
   when it reads better (`f"{beholder_id}->{session_id}"`). Surface FK ids via
   `<field>_id` (never the related object, which triggers a query) and choice
   labels via `get_<field>_display()`.

## Fields & types

4. Prefer the semantic `CharField` subclasses in `biased.django.models.char_field`
   (`DefaultCharField`; `DefaultShortCharField` for status/enum columns;
   `NameField`; `DefaultUrlField`) over raw `CharField(max_length=…)`.
5. For domain-specific string columns, subclass the base char fields into named
   field types (often in a `models/fields.py`) so meaning is encoded in the type,
   even when behavior is identical.
6. Use `biased.django.models.default_money_amount_field.DefaultMoneyAmountField`
   for money rather than an ad-hoc `DecimalField`; default running totals to `0`.
7. Avoid bare `JSONField()` — use
   `biased.django.models.pydantic_model_field.PydanticModelField` for validated
   structured JSON, or `JSONField(encoder=…, default=dict|list)` for plain JSON.
8. Reach for established model libraries over hand-rolling: ordered-model for
   orderable rows, field encryption for sensitive columns, phonenumber/localflavor
   for typed fields.

## Choices & status

9. Define choices as `@unique`, string-backed `models.TextChoices` in a per-app
   `types.py` (generate values with `auto()`) — not inline in the model file.
10. Pass the choices class directly (`choices=SomeStatus`), not
    `choices=SomeStatus.choices`.
11. Make status fields a `DefaultShortCharField` with `choices=` and an explicit
    initial-state default (e.g. `.new`, `.pending`).

## Relationships

12. Always set `related_name` explicitly; add a singular `related_query_name`
    alongside the plural `related_name`. For app-spanning relations, prefix the
    name with the owning app.
13. Choose `on_delete` by ownership: `CASCADE` for owned children, `SET_NULL`
    (with `null`/`blank`) for optional/audit refs that should outlive the parent.
14. For multi-table inheritance, declare the parent link explicitly:
    `OneToOneField(parent, parent_link=True, primary_key=True, related_name="<model>_ptr")`.
15. Name explicit M2M "through" tables, give them paired FKs + `unique_together`,
    and wire via `through="app.ThroughModel"` on the `ManyToManyField` (which still
    carries `related_name`/`related_query_name`).

## Validation & constraints

16. Put cross-field invariants in `clean()`, raising
    `ValidationError(msg, code="snake_case_code")` with a stable machine-readable
    code; reserve DB constraints for true uniqueness.
17. Use `unique_together` for simple composite uniqueness; reach for
    `Meta.constraints` `UniqueConstraint` when you need a name or options
    (e.g. `nulls_distinct`).

## Managers & mixins

18. Build custom managers/querysets by composing reusable mixin managers (e.g. the
    soft-delete manager in `biased.django.models.deleted_at_mixin`), exposing query
    intent as queryset methods (e.g. `not_deleted()`).
19. Factor recurring field clusters into abstract mixins (`class Meta: abstract = True`)
    and combine several via MRO on the concrete model.

## Meta & docs

20. Set `verbose_name` only to preserve initialism casing (ACH, SSN, FINRA, KYC);
    otherwise omit `Meta` and leave default ordering to Django.
21. Set `verbose_name_plural` whenever the default plural would be wrong. Django
    derives the plural by appending a bare `"s"` to `verbose_name` — it does no
    real English pluralization — so any model whose name doesn't pluralize by
    `+s` needs an explicit plural, or the admin shows mangled labels
    (`ChannelAccountAccess` → "Channel account access").
22. Document non-obvious models with a class docstring (state grain/semantics) and
    per-field `help_text` (especially the rationale for nullability).
