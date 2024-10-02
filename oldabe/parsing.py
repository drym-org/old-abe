from decimal import Decimal
import re


def parse_percentage(value):
    """
    Translates values expressed in percentage format (75.234) into
    their decimal equivalents (0.75234). This effectively divides
    the value by 100 without losing precision.
    """
    value = re.sub("[^0-9.]", "", value)
    value = "00" + value
    if "." not in value:
        value = value + ".0"
    value = re.sub(
        r"(?P<pre>\d{2})\.(?P<post>\d+)", r".\g<pre>\g<post>", value
    )
    value = Decimal(value)
    return value


def serialize_proportion(value):
    """
    Translates values expressed in decimal format (0.75234) into
    their percentage equivalents (75.234). This effectively multiplies
    the value by 100 without losing precision.
    """
    # otherwise, decimal gets translated '2E-7.0'
    value = format(value, "f")
    if "." in value:
        value = value + "00"
    else:
        value = value + ".00"
    value = re.sub(
        r"(?P<pre>\d)\.(?P<post>\d{2})(?P<rest>\d*)",
        # match a number followed by a decimal point
        # followed by at least two digits
        r"\g<pre>\g<post>.\g<rest>",
        # move the decimal point two places to the right
        value,
    )
    # strip leading insignificant zeroes
    value = value.lstrip("0")
    # ensure there's a single leading zero if it is
    # a decimal value less than 1
    value = re.sub(r"^\.", r"0.", value)
    if "." in value:
        # strip trailing insignificant zeroes
        value = value.rstrip("0")
        # remove decimal point if whole number
        value = re.sub(r"\.$", r"", value)
    return value
