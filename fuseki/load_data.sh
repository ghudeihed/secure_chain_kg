#!/bin/bash
# Start Fuseki server in the background
/jena-fuseki/fuseki-server --config=/fuseki/config.ttl &

# Wait for Fuseki to start (adjust sleep time if needed)
sleep 10

# Load all .ttl files from /fuseki/data/ into the securechain dataset
for file in /fuseki/data/*.ttl; do
  if [ -f "$file" ]; then
    echo "Loading $file into securechain dataset"
    curl -X POST http://localhost:3030/securechain/data -H "Content-Type: text/turtle" --data-binary "@$file"
  fi
done

# Keep the container running
wait