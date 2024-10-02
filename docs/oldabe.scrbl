#lang scribble/manual

@require[racket/runtime-path]

@title{Old Abe: The Accountant for All of your ABE Needs}

@(define-runtime-path logo-path "assets/img/logo.png")
@(if (file-exists? logo-path)
     (image logo-path #:scale 1.0)
     (printf "[WARNING] No ~a file found!~%" logo-path))

@table-of-contents[]

@section{Intro}

Attribution-Based Economics is a new model of economics designed to recognize and empower value creation in the world and structure the necessary incentives in a scalable way without the need for destructive and wasteful dynamics such as the adversarial competition characterizing capitalist economics.

Although ABE is a new model, it does not start from scratch. Rather, it builds on the existing millennia-old body of work in economics and finance, translating existing, time-tested concepts and intuitions into the new paradigm in a manner that preserves their essence while also shedding the incidental details of their implementation in a capitalist economic system. This results in economic and financial patterns of great simplicity in ABE when compared with capitalism.

Nevertheless, the composition of simple atoms can lead to great complexity of the whole, and that is precisely the case with ABE as well. Economic systems are incredibly rich, dynamic, and complex. Implementing the ABE financial model for every project would take a lot of effort and care, and would be hard to get right even though the financial components are simpler than their traditional analogues. After all, traditional corporations hire entire teams of accountants to do it! Which open source project can afford such luxury?

That's where Old Abe comes in.

One of the defining properties of ABE is that all accounting is publicly conducted, even if anonymized. This allows us to write software -- aka your friendly accountant, Old Abe -- to automate significant portions of the accounting process, and to avoid any duplication of effort in ensuring that accounting is in line with ABE guidelines. Old Abe itself is owned by no one, developed and scrutinized by all to ensure accuracy, and it takes care of the accounting for projects in the agreed-upon way.

@section{Inputs}

Old Abe considers precisely three inputs in doing all of its accounting, and it will be useful to keep these in mind as we learn more:

@itemlist[
#:style 'ordered

@item{Attributions -- an association of contributor to percentage of value allocated from the value represented by the project as a whole.}

@item{Instruments -- an association of an instrument to percentage of value allocated from the value represented by the project as a whole.}

@item{Price -- a generic "fair market value" provided by the project to its users (Like many concepts, this concept named price has a distinct role in ABE from its traditional role in capitalism).}

@item{Valuation -- the assessed present value of the project as a whole.}
]

All of these are determined through the process of Dialectical Inheritance Attribution (DIA), which may initially assign values by fiat (following the DIA process for appraisal). Subsequently, these values change by incorporating every new accountable action (in a manner agreed-upon in DIA), as we'll see next.

@section{Accounting Flows}

Current accounting flows are a mix of manual and automated actions. Old Abe is not directly connected to any financial systems, so its primary role is to run the accounting logic, keep track of any project investors, and tell the maintainer how much to pay project contributors. It is up to the maintainer to record incoming payments (@code{abe/payments/}) and outgoing payouts (@code{abe/payouts/}).

@itemlist[
#:style 'ordered

@item{Recording a Payment - triggers a GitHub Action that runs the accounting logic (details below) and produces a report of all Outstanding Balances as a GitHub Issue. The maintainer can refer to the Issue to find out how much to pay.}

@item{Recording a Payout - triggers a GitHub Action that simply updates the Outstanding Balances issue to reflect the updated amounts owed.}

]

@subsection{Payment}

When someone makes a payment to a project, Old Abe allocates portions of that payment to project contributors and creates a report that tells maintainers how much money the project owes to each individual contributor. We'll get deep into the weeds of how it does that in a moment. If the incoming payment represents an investment (that is, it brings the payer's total amount paid above the project price), the payer is considered a project contributor. The system adds them to the attributions file with a share equal to their investment (or increases their pre-existing attributive share). The project valuation is increased by the investment amount and all existing attributive shares are diluted so that percentage shares still add up 100%.

Now, let's talk about how Old Abe allocates an incoming payment.

First, we pay off any processing fees (found in @code{instruments.txt}). These fees have fixed percentages that apply to every incoming payment and do not get diluted by investments. They are somewhat analogous to credit card fees. They go towards the Old Abe system itself and to those who have contributed to the DIA process for this project.

Next, we divide the remainder among the contributors in the attributions file. Ideally, this is as simple as dividing the amount according to each contributor's attributive share. However, sometimes certain contributors are temporarily unpayable (e.g. they might not have provided their payment information yet, etc.). In that case, we record the amount owed to that contributor as a "debt" so that the project can pay them later. To avoid having money sitting around in maintainers' accounts, we divide any amount left over among payable contributors, according to attributive share. Any amount we pay someone in excess of what we owed them originally, we record as an "advance." The idea here is that when someone eventually becomes payable, we can prioritize paying off the debt we owe them by allocating money to them first whenever a new payment comes in. Anyone who has been accumulating advances will receive a little less than their attributive share until their total advance amount has been "drawn down" and the scales have been balanced between debts and advances.

