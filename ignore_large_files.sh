#!/bin/bash

# set your size limit here (default: 50MB)
LIMIT="+100M"

echo "🔍 Finding files larger than $LIMIT..."

# find all large files and append them to .gitignore (if not already ignored)
find . -type f -size $LIMIT | while read file; do
  # skip .git directory
  if [[ "$file" == ./.git/* ]]; then
    continue
  fi
  # check if already in .gitignore
  if ! grep -qxF "$file" .gitignore 2>/dev/null; then
    echo "$file" >> .gitignore
    echo "➕ Added to .gitignore: $file"
  fi
done

echo "✅ Done. All large files are now listed in .gitignore."
