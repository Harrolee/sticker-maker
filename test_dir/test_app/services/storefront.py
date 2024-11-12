from random import randint
import requests
from dataclasses import dataclass

@dataclass
class StorefrontProduct:
    title: str
    description: str
    redirect_url: str
    image_url: str
    price: int  # 1999 is $19.99 on sell.app

class StickerPublisher:
    def __init__(self, config):
        self.config = config

    def _delivery_text(self, product_name, support_email):
        delivery_text_flair = [
            f"Thanks for purchasing {product_name}! They were very lonely here.",
            f"I figured you'd like {product_name}.",
            f"Come back to buy some of {product_name}'s friends."
        ]
        chosen_flair = randint(0, len(delivery_text_flair) - 1)
        return f"{delivery_text_flair[chosen_flair]}\nWe'll send your order to the shipping address you supplied in this purchase form.\nIf you have any concerns, email {support_email} and reference the serial number on your order"

    def _publish_draft_sticker(self, product: StorefrontProduct):
        headers = {
            "Authorization": f"Bearer {self.config.sell_app_token}"
        }
        data = {
            "title": product.title,
            "description": product.description,
            "visibility": "PUBLIC",
            "delivery_text": self._delivery_text(product.title, self.config.support_email),
            "additional_information[0][type]": "text",
            "additional_information[0][required]": "1",
            "additional_information[0][label]": "Shipping address:",
            "other_settings[redirect_url]": product.redirect_url,
            "other_settings[product_title]": product.title,
            "other_settings[product_description]": product.description,
        }
        files = {
            "images[]": ("sticker.png", open(product.image_url, "rb"), "image/png")
        }

        response = requests.post("https://sell.app/api/v2/products", headers=headers, data=data, files=files)
        if response.status_code == 201:
            return response.json()["data"]["id"]
        raise Exception(f"failed to post product to storefront. Response info follows:\n{response.json()}")

    def _sticker_go_live(self, product: StorefrontProduct, storefront_product_id):
        payload = {
            "title": product.title,
            "description": product.description,
            "deliverable": {
                "data": {
                    "serials": ["order tracking number here"],
                    "comment": self._delivery_text(product.title, self.config.support_email),
                    "removeDuplicate": False
                },
                "types": ["TEXT", "MANUAL"]
            },
            "pricing": {
                "humble": True,
                "price": {
                    "price": product.price,
                    "currency": "USD"
                }
            },
            "minimum_purchase_quantity": 1,
            "maximum_purchase_quantity": None,
            "bulk_discount": [
                {
                    "minimum_purchase_amount": 20,
                    "discount_percentage": 10
                }
            ],
            "payment_methods": ["PAYPAL"],
            "other_settings": {"quantity_increments": 5}
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.sell_app_token}"
        }

        response = requests.request("POST", f"https://sell.app/api/v2/products/{storefront_product_id}/variants", json=payload, headers=headers)
        if response.status_code != 201:
            raise Exception(f"failed to post product to storefront. Response info follows:\n{response.json()}")

    def publish_sticker(self, product: StorefrontProduct):
        try:
            storefront_product_id = self._publish_draft_sticker(product)
            self._sticker_go_live(product, storefront_product_id)
            product_url = f"https://{self.config.sell_app_storefront_name}.sell.app/product/{product.title.replace(' ', '-')}?store={self.config.sell_app_storefront_name}"
            return storefront_product_id, product_url
        except RuntimeError as error:
            raise RuntimeError(f"could not publish sticker. error: {error}")

if __name__ == "__main__":
    from make_sticker.config import StickerConfig
    # Initialize the config object
    config = StickerConfig()

    # Create an instance of StickerPublisher with the config
    publisher = StickerPublisher(config=config)

    # Example usage:
    product = StorefrontProduct(
        title="Cool Sticker",
        description="A really cool sticker.",
        redirect_url="https://example.com/product/1",
        image_url="path_to_image.png",
        price=1999
    )
    
    storefront_product_id, product_url = publisher.publish_sticker(product)
    print(f"Product published with ID {storefront_product_id}. URL: {product_url}")
