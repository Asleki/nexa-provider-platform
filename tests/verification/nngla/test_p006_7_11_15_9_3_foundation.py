from verification.nngla.p006_7_11_15_9_3.matrix import matrix_row
def test_matrix_is_exact_count_fail_closed(): assert not matrix_row(0)["qualified"] and not matrix_row(119)["qualified"] and matrix_row(120)["qualified"] and not matrix_row(121)["qualified"]
