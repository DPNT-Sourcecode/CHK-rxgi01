"""
Service for handling checkouts.
"""

import re


class CheckoutService:
    """
    Service for handling checkouts.
    """

    # We'll normally want these in a DB or some file.
    # Prices: SKU -> price
    prices = {"A": 50, "B": 30, "C": 20, "D": 15}
    # Offers: SKU -> (quantity, price_for_that_quantity)
    offers = {"A": (3, 130), "B": (2, 45)}

    def __init__(self) -> None:
        pass

    def get_item_price(self, sku: str, quantity: int) -> int:
        """
        Return the price for `quantity` number of items defined by `sku`.
        """
        result = 0
        try:
            price = self.prices[sku]
        except KeyError:
            raise ValueError(f"invalid SKU: {repr(sku)}")

        try:
            offer = self.offers[sku]
        except KeyError:
            pass
        else:
            result += (quantity // offer[0]) * offer[1]
            quantity %= offer[0]

        result += quantity * price

        return result

    def get_basket_price(self, basket: str) -> int:
        """
        Return the price of the given basket or -1 if invalid.

        :param basked: A string containing SKUs. Non-characters (like spaces
            and commas are ignored), but the letters are considered
            case-sensitive, as is common practice with SKUs.
        :return: The price of the basked with given SKUs, or -1 if some SKU is
            invalid (i.e., it does not exist in service's `prices` dictionary).
        """
        sku2quant: dict[str, int] = dict()
        for sku in re.sub(r"[^a-z]", "", basket, flags=re.I):
            sku2quant[sku] = sku2quant.get(sku, 0) + 1
        try:
            return sum(
                self.get_item_price(sku, quantity)
                for sku, quantity in sku2quant.items()
            )
        except ValueError:
            return -1

