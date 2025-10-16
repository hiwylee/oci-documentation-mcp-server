curl -X 'POST' \
  'http://localhost:8090/search_documentation' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer top-secret' \
  -H 'Content-Type: application/json' \
  -d '{
  "search_phrase": "OCI Object Storage download object SDK",
  "limit": 3
}'

