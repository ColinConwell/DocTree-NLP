#\!/bin/bash

# Script to replace all notionlp references with doctree_nlp in test files

for file in $(find /Users/colinconwell/GitHub/NotioNLPToolkit/tests -name "*.py"); do
  sed -i "" "s/notionlp\./doctree_nlp\./g" "$file"
  sed -i "" "s/from notionlp/from doctree_nlp/g" "$file"
  sed -i "" "s/import notionlp/import doctree_nlp/g" "$file"
  sed -i "" "s/patch(\"notionlp/patch(\"doctree_nlp/g" "$file"
done

echo "All notionlp references updated to doctree_nlp in test files."
