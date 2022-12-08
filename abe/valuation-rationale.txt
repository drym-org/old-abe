TL;DR: we set the valuation at the estimated cost (USD 8750) -- which we agreed was a fair lower bound on valuation -- and set the market price as zero, so that every payment to the project counts fully as an investment.

More detail:

For valuation, we came up with two numbers to inform the final estimate. The first has to do with cost, and the second, with value provided. The former is easier to estimate but the latter is more relevant.

First, we agreed to compute the cost of the value generated in terms of standard hourly wages and time invested. For hourly rates for development contractors, on the internet, we found everything from $80/hr to > $300/hr. Using the value $125/hr, we get:

C = 70 person hours × $ 125 / hour = $8750.

But this is an estimate of the industry cost of such a project rather than its value, and so this should be considered as an approximation to the value to the extent that the industry is accurate at estimating the value, that is, we could say that it is an indirect estimate of value provided.

Now regarding the second number:

In ABE, the value of a project is purely a function of its use and influence. If there are no users and the ideas introduced by the project don't appear in subsequent work, then it isn't valuable. If there are lots of users and they use it in ways that are important to them, and if many other projects reflect its ideas, then it is very valuable. If there are some users and it fulfills a useful but nonessential service, and if it inspires a few other projects, then the value is somewhere in between. To quantify this intuition, we can say that:

V = ∑ⁿ vᵢrᵢ   ___(I)

where n is the number of uses (whether material use or in terms of ideas reflected), vᵢ is the attributed proportion of value in each of those uses, and rᵢ is the revenue of the i'th use.

This number would be a direct measure of the value of the project.

Now here's the problem. As use (and also revenue generated) by end users is often private information, we won't always or even usually have these values available. Therefore, the best we can hope for is an approximate estimate. This is where the notion of "fair market price" comes in, as it is one way to achieve this. By estimating a price P that users would be willing to pay to use it, we essentially treat the value contributed to each use as having an upper bound P (it is an upper bound because such users are not mandated to pay anything, and may pay a smaller amount or nothing), and we get:

V = ∑ⁿ P   ___(II)

We could expect that users would pay in "all" cases where rᵢ >> P, which is likely to be the same as the cases where rᵢ > 0 in practice, and we can use the number of such cases as the value of n.

So if we could estimate P, the total number of uses n', and the number of solvent (i.e. revenue-generating) uses n = |{rᵢ>0}|, it would give us a crude approximation of direct valuation. Let's see if we can do that.

For the price, two contributors independently came up with numbers, resulting in $10 and $20. We could take the average to yield a price of $15. Even though this number is somewhat arbitrary, it seems plausible that users would be willing to pay this much to use Old Abe if they had any revenue. On the other hand, estimating the number of users seems much harder, entailing much more uncertainty. Over the useful lifetime of Old Abe, it could have anywhere from 0 to 1,000,000 users or more, as adoption is almost impossible to predict.

The uncertainty here causes the entire resulting estimate to be wildly uncertain, and so, we decided that we don't have enough data to produce a useful estimate of (I) at this time, even with the simplification in (II).

So instead, we reasoned that, regardless of what the actual valuation is, it must at least exceed the cost in order to be fair to material contributors in terms of how investment works, since otherwise, users could pay for less than the cost and end up with a 100% attribution share. So it would seem that the cost of production should be treated as a lower bound on valuation. Since the estimated cost C above is the least arbitrary number we are capable of producing at this time, we chose to use this lower bound as the valuation itself, in order to incentivize investment as much as possible while not obviously violating fairness.

Regarding the price, we further decided that, at this stage, any users adopting Old Abe count as "early adopters" and are therefore investing in the project. Thus, we decided to set the market price as zero, meaning that any payment by users would count as an investment.
