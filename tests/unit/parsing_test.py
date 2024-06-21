import pytest
from decimal import Decimal
from oldabe.parsing import (
    parse_percentage,
    serialize_proportion,
)


class TestParsePercentage:
    def test_an_integer(self):
        assert parse_percentage('75') == Decimal('0.75')

    def test_non_integer_greater_than_1(self):
        assert parse_percentage('75.334455') == Decimal('0.75334455')

    def test_non_integer_less_than_1(self):
        assert parse_percentage('0.334455') == Decimal('0.00334455')

    def test_decimal_places_at_precision_context(self):
        assert parse_percentage('5.1234567891') == Decimal('0.051234567891')

    def test_very_small_number(self):
        assert parse_percentage('0.000001') == Decimal('0.00000001')

    def test_0(self):
        assert parse_percentage('0') == Decimal('0')

    def test_0_point_0(self):
        assert parse_percentage('0.0') == Decimal('0')

    def test_100(self):
        assert parse_percentage('100') == Decimal('1')

    def test_100_point_0(self):
        assert parse_percentage('100.0') == Decimal('1')


class TestSerializeProportion:
    def test_0(self):
        assert serialize_proportion(Decimal('0')) == '0'

    def test_0_point_0(self):
        assert serialize_proportion(Decimal('0.0')) == '0'

    def test_1(self):
        assert serialize_proportion(Decimal('1')) == '100'

    def test_1_point_0(self):
        assert serialize_proportion(Decimal('1.0')) == '100'

    def test_almost_1(self):
        assert serialize_proportion(Decimal('0.9523452')) == '95.23452'

    def test_low_precision_number(self):
        assert serialize_proportion(Decimal('0.2')) == '20'

    def test_very_small_number(self):
        assert serialize_proportion(Decimal('0.0000002')) == '0.00002'

    def test_decimal_places_at_precision_context(self):
        assert serialize_proportion(Decimal('0.1234567891')) == '12.34567891'
