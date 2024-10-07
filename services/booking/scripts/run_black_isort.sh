#!/bin/sh

# Run black and isort on all files in the repository
black . --check
isort . --check-only

# Prompt the user to confirm that they want to run black and isort on all files in the repository
printf "Do you want to auto-format all files with black and isort? (y/n) "
read -r response

# See https://www.tutorialspoint.com/unix/case-esac-statement.htm
case "$response" in
    [Yy]*)
        black .
        isort .
        echo "Formatting complete"
        ;;
    *)
        echo "No changes made"
        ;;
esac

echo "Push checks complete"
