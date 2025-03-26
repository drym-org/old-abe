from . import compile_outstanding_balances
from decimal import getcontext


def main():
    # set decimal precision at 10 to ensure
    # that it is the same everywhere
    # and large enough to represent a sufficiently
    # large number of contributors
    getcontext().prec = 10
    print(compile_outstanding_balances())


if __name__ == "__main__":
    main()
