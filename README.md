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

3. Attributions should be expressed on separate lines containing email (or hashed identifier), and percentage amount, in csv format:

```
john@doe.com,24%
jane@doe.com,73%
abe@doe.com,2%
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

# Non-Ownership

This work is not owned by anyone. Please see the [Declaration of Non-Ownership](https://github.com/drym-org/foundation/blob/main/DECLARATION-OF-NON-OWNERSHIP.md).
