#lang scribble/manual

@title{Old Abe: The Accountant for All of your ABE Needs}

@table-of-contents[]

@section{Intro}

Attribution-Based Economics is a new model of economics designed to recognize and empower value creation in the world and structure the necessary incentives in a scalable way without the need for destructive and wasteful constructions such as the adversarial competition characterizing capitalist economics.

Although ABE is a new model, it does not start from scratch. Rather, it builds on the existing millennia-old body of work in economics and finance, translating existing, time-tested concepts and intuitions into the new paradigm in a manner that preserves their essence while also shedding the incidental details of their implementation in a capitalist economic system. This results in economic and financial patterns of great simplicity in ABE when compared with capitalism.

Nevertheless, the composition of simple atoms can lead to great complexity of the whole, and that is precisely the case with ABE as well. Economic systems are incredibly rich, dynamic, and complex. Implementing the ABE financial model for every project would take a lot of effort and care, and would be hard to get right even though the financial components are simpler than their traditional analogues. You could hire a team of accountants to do it, but which open source project can afford such luxury?

That's where Old Abe comes in.

One of the defining properties of ABE is that all accounting is publicly conducted, even if anonymized. This allows us to write software -- aka your friendly accountant, Old Abe -- to automate significant portions of the accounting process, and to avoid any duplication of effort in ensuring that accounting is in line with ABE guidelines. Old Abe itself is owned by no one, developed and scrutinized by all to ensure accuracy, and handles the accounting for all projects in the agreed-upon way.

@section{Inputs}

Old Abe considers precisely three inputs in doing all of its accounting, and it will be useful to keep these in mind as we learn more:

@itemlist[
#:style 'ordered

@item{Attributions -- an association of contributor to percentage of value allocated from the value represented by the project as a whole.}

@item{Price -- a generic "fair market value" provided by the project to its users (Like many concepts, this concept named price has a distinct role in ABE from its traditional role in capitalism).}

@item{Valuation -- the assessed present value of the project as a whole.}
]

All of these are determined through the process of Dialectical Inheritance Attribution (DIA), which may initially assign values by fiat (following the DIA process for appraisal). Subsequently, these values change by incorporating every new accountable action (in a manner agreed-upon in DIA), as we'll see next.

@section{Accounting Flows}

There are several actions ("accountable actions") pertaining to a project that trigger accounting by Old Abe. These are:

@itemlist[
#:style 'ordered

@item{Work is done for the project.}

@item{A financial contribution is made to the project.}

@item{An appointed project representative fulfills a payout to a contributor.}

@item{A "fiat" change is made to one of the inputs, i.e. either attributions, price or valuation, which is typically a resolution by DIA.}

]

We will learn more about each of these, in turn.

@subsection{Work}

Work done could be either labor, capital, or ideas, as defined in the @hyperlink["https://github.com/drym-org/finance/blob/main/finance.md"]{ABE financial model}). Regardless of what kind of work it is, its appraisal takes the form of an "incoming attribution," which is an association of a set of contributors to percentage of value contributed, as judged in related to existing attribution allocations in the project.

Old Abe will account this by "renormalizing" the attributions to total to 100% after incorporating the fresh values.

TODO: flesh out

@subsection{Payment}

Money, money, money!!!

TODO: flesh out

@subsection{Payout}

TODO: flesh out

@subsection{Fiat Change in Inputs}

TODO: flesh out, including backpropagation

@section{Modules}

The accounting flows mentioned earlier correspond to distinct modules that handle them.

@subsection{Money In}

This module handles incoming payments.

First it finds all payments that have not already been processed, that
is, which do not appear in the transactions file.

For each of these payments, it consults the current attributions for
the project, and does three things.

First, it figures out how much each person in the attributions file is
owed from this fresh payment, generating a transaction for each
stakeholder.

Second, it determines how much of the incoming payment can be
considered an "investment" by comparing the project price with the
total amount paid by this payer up to this point -- the excess, if
any, is investment.

Third, it increases the current valuation by the investment amount
determined, and, at the same time, "dilutes" the attributions by
making the payer an attributive stakeholder with a share proportionate
to their incoming investment amount (or if the payer is already a
stakeholder, increases their existing share) in relation to the
valuation.

@subsection{Money Out}

This module determines outstanding balances owed.

First, it reads all generated transactions from payments that have come in to
determine the amount owed to each contributor.  Then, it looks at all recorded
payouts to see the total amounts that have already been paid out.  It then
reports the difference of these values, by contributor, as the balance still
owed.
