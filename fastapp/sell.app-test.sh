#!/bin/bash
curl --request POST \
  --url https://sell.app/api/v2/products \
  --header 'Authorization: Bearer {token here}' \
  --header 'Content-Type: multipart/form-data' \
  --form 'title=Immortality Elixir' \
  --form 'description=Want to live forever? Buy this now and I'\''ll send a digital elixir that converts your soul into an NFT that will roam the internet for eternity!' \
  --form visibility=PUBLIC \
  --form 'delivery_text=Thanks for purchasing! Here is a 20% off coupon for your next purchase: 20FREE24' \
  --form 'images[]=@workspace/output/tabbed.png' \
  --form 'additional_information[0][type]=checkbox' \
  --form 'additional_information[0][required]=1' \
  --form 'additional_information[0][label]=I agree to handing over my soul' \
  --form 'other_settings[redirect_url]=https://666.com/transfer-soul?customer_email=[customer_email]&order_id=[order_id]' \
  --form 'other_settings[video_url]=https://www.youtube.com/watch?v=dQw4w9WgXcQ' \
  --form 'other_settings[product_title]=The real elixir of immortality' \
  --form 'other_settings[product_description]=Live forever, online.' \
  --form 'other_settings[faq][0][question]=Will I really live forever?' \
  --form 'other_settings[faq][0][answer]=Yes, trust me!'
