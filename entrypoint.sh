#!/bin/sh -l

# ensure that any errors encountered cause immediate
# termination with a non-zero exit code
set -e

echo "Running ls..."
echo $(ls /)
echo "... done."

echo "Running ls /github/workspace..."
echo $(ls /github/workspace)
echo "... done."

echo "Running money_in script..."
python /oldabe/money_in.py
echo "... done."

# Note that running this locally would cause your global
# git config to be modified
echo "Committing updated transactions and attributions back to repo..."
git config --global user.email "abe@drym.org"
git config --global user.name "Old Abe"
git add abe/transactions.txt abe/attributions.txt

set +e

git commit -m "Updated transactions and attributions"
git fetch
git rebase origin/main
git push origin main
echo "... done."

set -e

echo "Running money_out script..."
echo balances=$(python /oldabe/money_out.py) >> $GITHUB_OUTPUT
echo "... done."
