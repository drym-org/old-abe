#!/bin/bash

# ensure that any errors encountered cause immediate
# termination with a non-zero exit code
set -eo pipefail

echo "PWD is: "
echo $(pwd)

echo "Running ls..."
echo $(ls /)
echo "... done."

export PYTHONPATH=/:$PYTHONPATH

echo "Running ls /github/workspace..."
echo $(ls /github/workspace)
echo "... done."

# TODO: note that we do not support multiple consecutive
# ABE-related commits with jobs running concurrently,
# as subsequent jobs would not have the up-to-date accounting
# data that would be produced by earlier jobs that have
# not yet finished running.
# So either:
#  (a) ensure that ABE-related jobs are always run after the previous
#      one concludes.
#  (b) employ a locking mechanism so that no two instances of Old Abe
#      can run concurrently (better).

echo "Running money_in script..."
python -m oldabe.money_in.__main__

# $? holds the exit status of the last executed command
if [ $? -neq 0 ]; then
    exit 1
fi
echo "... done."

echo "Running money_out script..."
BALANCES_OUTPUT=$(python -m oldabe.money_out.__main__)

# $? holds the exit status of the last executed command
if [ $? -eq 0 ]; then
    echo balances=$BALANCES_OUTPUT >> $GITHUB_OUTPUT
else
    exit 1
fi
echo "... done."

# Note that running this locally would cause your global
# git config to be modified
echo "Committing updated accounting records back to repo..."
git config --global user.email "abe@drym.org"
git config --global user.name "Old Abe"
git add abe/transactions.txt abe/attributions.txt abe/attributions.md abe/valuation.txt abe/itemized_payments.txt abe/advances.txt abe/debts.txt

git commit -m "Updated accounting records"
git fetch
git rebase origin/`git remote set-head origin -a | cut -d' ' -f4`
git push origin `git remote set-head origin -a | cut -d' ' -f4`
echo "... done."
