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

echo "Committing updated transactions back to repo..."
git config --global user.email "abe@drym.org"
git config --global user.name "Old Abe"
git add transactions.txt
git commit -m "Updated transactions"
git fetch
git rebase origin/main
git push origin main
echo "... done."

echo "Running money-out script..."
python /money-out.py > issue-body.txt
echo "... done."

echo "Create an issue with outstanding balances..."
gh issue create -F issue-body.txt -t "Outstanding Balances" -l outstanding-balances
echo "... done."
