ENTITY = "TOWN"
EXPECTED = 120
PUBLIC_VIEW = "geography.nngla_town_public_read_v2"


def matrix_row(count):
    count = int(count)
    qualified = count == EXPECTED
    return {
        "entity": ENTITY,
        "publicCount": count,
        "expectedCount": EXPECTED,
        "qualified": qualified,
        "status": (
            "COMPLETE"
            if qualified
            else ("PARTIAL" if count else "EMPTY")
        ),
    }
