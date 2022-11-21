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

echo "Running money-out script..."
python /money-out.py
echo "... done."

echo "Running git status..."
echo $(git status)
echo "... done."

echo "Committing updated transactions back to repo..."
# commit transactions.txt back to repo
echo "... done."

