#!/bin/bash

# Directory containing JavaScript files
JS_DIR="app/static/js"
MIN_DIR="$JS_DIR/min"

# Create the min directory if it doesn't exist
mkdir -p "$MIN_DIR"

# Loop through all .js files in the directory
for file in "$JS_DIR"/*.js; do
  # Get the base filename without the directory
  filename=$(basename "$file")
  # Create the output filename with .min.js extension
  output_file="$MIN_DIR/${filename%.js}.min.js"
  # Minify the JavaScript file using uglifyjs
  uglifyjs "$file" -o "$output_file"
  echo "Minimized: $file -> $output_file"
done

echo "All JavaScript files have been minimized and saved in $MIN_DIR."
