#!/bin/sh -l

echo "Running ls..."
echo $(ls /)
echo "... done."

echo "Running ls /github/workspace..."
echo $(ls /github/workspace)
echo "... done."

echo "Running money-in script..."
python /money-in.py
echo "... done."

echo "Committing updated transactions and attributions back to repo..."
git config --global user.email "abe@drym.org"
git config --global user.name "Old Abe"
git add abe/transactions.txt abe/attributions.txt
git commit -m "Updated transactions and attributions"
git fetch
git rebase origin/main
git push origin main
echo "... done."

echo "Running money-out script..."
echo balances=$(python /money-out.py) >> $GITHUB_OUTPUT
echo "... done."
