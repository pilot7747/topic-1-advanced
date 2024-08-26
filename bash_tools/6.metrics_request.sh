curl -X 'GET' \
  'http://localhost:8001/metrics/' \
  -H 'accept: application/json' \
  -H "Authorization: $(echo $ADMIN_KEY)"
