from registries.nngla.spatial_fabric.bundle17j import collision_contract,different_scope_visible_number_contract,idempotent_address_replay,recovery_rows

def test_same_scope_collision_fails_closed(): assert collision_contract()
def test_idempotent_retry_returns_original(): assert idempotent_address_replay()
def test_same_visible_number_is_valid_in_different_governed_scopes(): assert different_scope_visible_number_contract()
def test_recovery_policy_allows_gaps_but_never_reuse():
 rows=recovery_rows(); assert rows and all(r.expected_gap_allowed and not r.identifier_reused for r in rows)
