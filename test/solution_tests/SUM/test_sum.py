from solutions.SUM import sum_solution


class TestSum():
    def test_sum(self):
        assert sum_solution.compute(17, 19) == 36
