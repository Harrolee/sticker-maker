from dataclasses import dataclass
from typing import List


@dataclass
class StickerOrder:
    sku: str
    quantity: int

    def __str__(self):
        return f"""
            Sku: {self.sku} 
            Quantity: {self.quantity}
        """

@dataclass
class OrderInfo:
    email: str
    name: str
    order_id: str
    shipping_address: str
    order_contents: List[StickerOrder]

    def _build_order_contents(self):
        body = f"{len(self.order_contents)} Different SKUs\n\n"
        return body + "\n--------\n".join([str(sticker) for sticker in self.order_contents])

    def pretty_print(self):
        return f"""
            Order ID: {self.order_id} 
            Name: {self.name} 
            Email: {self.email} 
            Shipping Address: {self.shipping_address}
            Order Contents: {self._build_order_contents}
        """
