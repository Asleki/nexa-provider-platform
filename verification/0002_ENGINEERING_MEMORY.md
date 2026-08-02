# Engineering Memory

## Confirmed Database
- Database: npp_dev
- Runtime: simulation
- Schema: reference
- Table: canonical_name

## Confirmed Columns
name_id
canonical_value
search_value
name_kind
status
runtime_mode
schema_version
created_at
source_reference
language_refs
country_refs
region_refs
culture_refs
script_code
attributes

## Rules
- Never assume schemas.
- Verify before modifying.
- Count before import.
- Count after import.
- Read back stored records.
- Re-run import to prove idempotency.
