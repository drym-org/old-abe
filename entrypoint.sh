#!/bin/sh -l

echo "Running ls..."
echo $(ls)
echo "... done."

echo "Running money-in script..."
python money-in.py
echo "... done."

echo "Running money-out script..."
python money-out.py
echo "... done."

