from oldabe.tally import Tally


class TestTally:

    def test_ordinary_tally(self):
        tally = Tally([("a", 1), ("b", 1), ("c", 2), ("a", 1)])
        assert tally == {'a': 2, 'b': 1, 'c': 2}

    def test_subtract_tallies(self):
        tally1 = Tally([("a", 1), ("b", 1), ("c", 2), ("a", 1)])
        tally2 = Tally([("b", 1), ("c", 1)])
        assert tally1 - tally2 == {'a': 2, 'b': 0, 'c': 1}
