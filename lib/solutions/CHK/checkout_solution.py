"""
Solution for the `CHK` challenge.
"""


# noinspection PyUnusedLocal
# skus = unicode string
def checkout(skus: str) -> int:
    """
    Return the total price of a basket containing given SKUs.

    :param sku: A string containing valid SKUs.
    :return: Total price of the basket, or -1 if some of the SKUs are invalid.
    """
    service = CheckoutService()
    return service.get_basket_price(skus)

