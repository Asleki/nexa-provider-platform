from verification.nngla.p006_7_11_15_9_2.matrix import matrix_row
def test_matrix_is_exact_count_fail_closed(): assert not matrix_row(0)["qualified"] and not matrix_row(63)["qualified"] and matrix_row(64)["qualified"] and not matrix_row(65)["qualified"]
