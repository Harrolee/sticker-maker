curl -X POST https://us-central1-sticker-maker-439910.cloudfunctions.net/process_sale \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d 'sale_id=123425&product_name=bananas&email=johndoe@example.com&test=true'
