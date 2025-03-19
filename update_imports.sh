#\!/bin/bash

# Script to replace all notionlp imports with doctree_nlp

for file in $(find /Users/colinconwell/GitHub/NotioNLPToolkit/tests -name "*.py"); do
  sed -i "" "s/from notionlp\./from doctree_nlp\./g" "$file"
  sed -i "" "s/import notionlp\./import doctree_nlp\./g" "$file"
done

echo "Imports updated in all test files."
