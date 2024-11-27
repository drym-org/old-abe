from decimal import Decimal
from ..tally import Tally
from ..repos import AdvancesRepo
from ..models import Advance
from ..constants import ACCOUNTING_ZERO


def draw_down_advances(available_amount, distribution, unpayable_contributors, payment):
    advance_totals = Tally((a.email, a.amount) for a in AdvancesRepo())

    negative_advances = [
        Advance(
            email=email,
            amount=-min(
                payable_amount, advance_totals[email]
            ),  # Note the negative sign
            payment_file=payment.file,
        )
        for email, payable_amount in distribution.without(
            unpayable_contributors
        )
        .distribute(available_amount)
        .items()
        if advance_totals[email] > ACCOUNTING_ZERO
    ]
    return negative_advances


def advance_payments(fresh_debts, negative_advances, distribution, unpayable_contributors, payment):
    redistribution_pot = Decimal(
        # amount we will not pay because we created debts instead
        sum(d.amount for d in fresh_debts)
        # amount we will not pay because we drew down advances instead
        # these are negative amounts, hence the abs
        + sum(abs(a.amount) for a in negative_advances)
    )

    fresh_advances = (
        [
            Advance(
                email=email,
                amount=amount,
                payment_file=payment.file,
            )
            for email, amount in distribution.without(unpayable_contributors)
            .distribute(redistribution_pot)
            .items()
        ]
        if redistribution_pot > ACCOUNTING_ZERO
        else []
    )
    return fresh_advances
