---
paths:
  - "**/models.py"
  - "**/models/*.py"
---

# Django model relations — recommendations

Recommendations for foreign keys, one-to-one and many-to-many relations.
Prefer these defaults; deviate when a situation genuinely warrants it.

1. Always set `related_name` explicitly, and a singular `related_query_name`
   beside the plural `related_name`; for a relation that crosses apps, prefix
   both with the owning app's name. The reverse names are then chosen rather
   than derived — `customer.orders.all()`,
   `Customer.objects.filter(order__total__gt=0)` — renaming a model does not
   silently rename them, and two apps' relations to one model cannot collide.
2. Choose `on_delete` by ownership: `CASCADE` for a child the parent owns,
   `SET_NULL` (with `null=True, blank=True`) for an optional or audit
   reference that must outlive its parent. The choice follows the data's
   lifecycle, so make it per relation; one blanket default either deletes
   history or leaves orphans.
3. For multi-table inheritance, declare the parent link explicitly:
   `OneToOneField(Parent, on_delete=models.CASCADE, parent_link=True,
   primary_key=True, related_name="<model>_ptr")`. The column, its reverse
   name and its delete behavior are then visible in the model instead of
   generated.
4. Give a many-to-many relation that needs its own columns a named "through"
   model: the two foreign keys plus a `UniqueConstraint` on the pair, wired
   with `through="app.ThroughModel"` on the `ManyToManyField`, which still
   sets `related_name` and `related_query_name`. The link then has a model to
   carry extra columns and an admin, and the constraint keeps a pair from
   being linked twice.
