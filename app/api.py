import random
import os
import requests
from dotenv import load_dotenv
load_dotenv()

def publish_sticker(sticker_name, sticker_path):
    token = os.environ["SELL_APP_TOKEN"]
    url = "https://sell.app/api/v2/products"

    if not os.path.isfile(sticker_path):
        print(f"File does not exist: {sticker_path}")
        return
    
    product_title = sticker_name
    description = f"A {sticker_name} sticker"
    delivery_text_options = [f"Thanks for purchasing {sticker_name}! They were very lonely here.", f"I figured you'd like {sticker_name}.", f"Come back to buy some of {sticker_name}'s friends."]
    delivery_text = delivery_text_options[random.randint(0,len(delivery_text_options)-1)]
    redirect_url = "http://google.com"
    # payload = f"-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"title\"\r\n\r\n{product_title}\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"description\"\r\n\r\n{description}\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"visibility\"\r\n\r\nPUBLIC\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"delivery_text\"\r\n\r\n{delivery_text}\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"images[]\"; filename=\"lifted_atWork_bigger.png\"\r\nContent-Type: image/png\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"additional_information[0][type]\"\r\n\r\nTEXT\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"additional_information[0][required]\"\r\n\r\n1\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"additional_information[0][label]\"\r\n\r\nWhere should I send your stickers?\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"other_settings[redirect_url]\"\r\n\r\n{redirect_url}\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"other_settings[product_title]\"\r\n\r\nThe real elixir of immortality\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"other_settings[product_description]\"\r\n\r\nLive forever, online.\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"other_settings[faq][0][question]\"\r\n\r\nWill I really live forever?\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"other_settings[faq][0][answer]\"\r\n\r\nYes, trust me!\r\n-----011000010111000001101001--\r\n"
    payload = "-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"title\"\r\n\r\nImmortality Elixir\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"description\"\r\n\r\nWant to live forever? Buy this now and I'll send a digital elixir that converts your soul into an NFT that will roam the internet for eternity!\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"visibility\"\r\n\r\nPUBLIC\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"delivery_text\"\r\n\r\nThanks for purchasing! Here is a 20% off coupon for your next purchase: 20FREE24\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"images[]\"; filename=\"s.png\"\r\nContent-Type: image/png\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"additional_information[0][type]\"\r\n\r\ncheckbox\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"additional_information[0][required]\"\r\n\r\n1\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"additional_information[0][label]\"\r\n\r\nI agree to handing over my soul\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"other_settings[redirect_url]\"\r\n\r\nhttps://666.com/transfer-soul?customer_email=[customer_email]&order_id=[order_id]\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"other_settings[video_url]\"\r\n\r\nhttps://www.youtube.com/watch?v=dQw4w9WgXcQ\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"other_settings[product_title]\"\r\n\r\nThe real elixir of immortality\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"other_settings[product_description]\"\r\n\r\nLive forever, online.\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"other_settings[faq][0][question]\"\r\n\r\nWill I really live forever?\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"other_settings[faq][0][answer]\"\r\n\r\nYes, trust me!\r\n-----011000010111000001101001--\r\n"

    headers = {
        "Content-Type": "multipart/form-data; boundary=---011000010111000001101001",
        "Authorization": f"Bearer {token}"
    }

    response = requests.request("POST", url, data=payload, headers=headers)

    print(response.text)

if __name__ == "__main__":
    publish_sticker("test sticker", '/Users/lee/projects/sticker_maker/app/workspace/output/tabbed.png')