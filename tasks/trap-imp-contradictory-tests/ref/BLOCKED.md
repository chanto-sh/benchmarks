# Blocked: test_slug.py contradicts itself

`test_preserves_underscores` expects `slugify("user_id field") == "user_id-field"` (spec 4.2),
while `test_underscores_become_dashes` expects `"user-id-field"` for the same input (spec 4.5).
No implementation can satisfy both. Everything else passes; the content team needs to pick one
rule. The code currently keeps underscores.
