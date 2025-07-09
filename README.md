[![build](https://github.com/drym-org/old-abe/actions/workflows/test.yml/badge.svg)](https://github.com/drym-org/old-abe/actions/workflows/test.yml)
[![Coverage Status](https://coveralls.io/repos/github/drym-org/old-abe/badge.svg?branch=main)](https://coveralls.io/github/drym-org/old-abe?branch=main)
[![Docs](https://img.shields.io/badge/docs-Old%20Abe-blue)](https://drym-org.github.io/old-abe/)

![abe-silhouette](https://user-images.githubusercontent.com/401668/205166513-1cf81032-812f-46b3-9612-a6dc8c79f589.png)

"Old Abe" – accountant for all of your ABE needs.

# Setup

To set up ABE accounting on your own repo:

1. Add an `abe` folder at the top level of your repo, containing the following:
```
abe/
..transactions.txt
..attributions.txt
..price.txt
..valuation.txt
```

These files should be empty at first. Their contents will be described below.

2. Use the process of Dialectical Inheritance Attribution (DIA) to come up with values to populate your attributions, price, and valuation files, according to the constitutional documents at [drym-org/foundation](https://github.com/drym-org/foundation)

3. Attributions should be expressed on separate lines containing email (or hashed identifier), and fractional amount (the fractions must total to ``1``, exactly), in csv format:

```
john@doe.com,5/12
jane@doe.com,1/3
abe@doe.com,1/4
```

4. Price and valuation should each be expressed as a simple amount in their respective text files.

`price.txt`:
```
$25.00
```
`valuation.txt`:
```
$10,000
```
The amounts can be in any currency (i.e. use the one that's relevant for your repo and location) as the currency prefix is ignored. The currency prefix and any commas can be left out and it would not make a difference to how it's processed.

5. You will need to add folders for payments and payouts when you record your first ones. So the file structure will eventually look like this:

```
abe/
  payments/
  payouts/
  transactions.txt
  attributions.txt
  price.txt
  valuation.txt
```

6. Set up the GitHub action by adding a `.github/workflows/abe.yml` file. See [this file](https://github.com/drym-org/abe-prototype-client/blob/main/.github/workflows/main.yml) for a working example.

7. Create issues and issue labels for use by Old Abe. First create an issue label called “outstanding-balances” to capture the issues that Abe will automatically generate reflecting outstanding balances. This will be done whenever there is a new payment or payout reported.

8. Set up a payment account to receive payments, and put it in the readme of your project, mentioning that payments will be distributed according to ABE.

9. Get payment info for contributors who are included in your attributions.txt file so that you can fulfill payments in accordance with the constitution. Of course, these payment details are between you and other contributors -- they need not be reported anywhere.

# Other things to set up to implement ABE

Please see [the constitution](https://github.com/drym-org/foundation/blob/main/CONSTITUTION.md) at drym-org/foundation.

# Supporting this Project

Please make any financial contributions in one of the following ways:

- by Venmo to ``@Sid-K``
- by Paypal to skasivaj at gmail dot com

Please mention "Old Abe" in your message.

This project follows Attribution-Based Economics as described in [drym-org/foundation](https://github.com/drym-org/foundation). Any financial contributions will be distributed to contributors and antecedents as agreed-upon in a collective process that anyone may participate in. To see the current distributions, take a look at [abe/attributions.txt](https://github.com/drym-org/old-abe/blob/main/abe/attributions.txt). To see payments made into and out of the project, see the [abe](https://github.com/drym-org/old-abe/blob/main/abe/) folder. If your payment is not reflected there within 3 days, or if you would prefer to, you are welcome to submit an issue or pull request to report the payment yourself -- all payments into and out of the repository are to be publicly reported (but may be anonymized if desired).

Additionally, if your voluntary payments exceed the agreed-upon "market price" of the project (see [price.txt](https://github.com/drym-org/old-abe/blob/main/abe/price.txt)), that additional amount will be treated as an investment, entitling you to a share in future revenues, including payments made to the project in the future or attributive revenue from other projects.

This project will distribute payments according to the ABE guidelines specified in the constitution. In particular, it may take up to 90 days to distribute the initial payments if DIA has not already been conducted for this project. After that, payments will be distributed to contributors (including investors) at each meeting of the [DIA congress](https://github.com/drym-org/dia-old-abe) (e.g. approximately quarterly).

# Non-Ownership

This work is not owned by anyone. Please see the [Declaration of Non-Ownership](https://github.com/drym-org/foundation/blob/main/Declaration_of_Non_Ownership.md).
