"""
Service for handling checkouts.
"""


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

