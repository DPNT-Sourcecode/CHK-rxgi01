"""
Service for handling checkouts.
"""

import itertools
from typing import TypeAlias


sku_pricesT: TypeAlias = dict[str, int]
sku2quantT: TypeAlias = dict[str, int]
sku_offersT: TypeAlias = dict[int, int]
offersT: TypeAlias = dict[str, sku_offersT]
free_itemsT: TypeAlias = dict[str, tuple[int, str]]


class CheckoutService:
    """
    Service for handling checkouts.
    """

    # We'll normally want these in a DB or some file.
    # Prices: SKU -> price
    prices: sku_pricesT = {"A": 50, "B": 30, "C": 20, "D": 15, "E": 40}
    # Offers: SKU -> {quantity -> price_for_that_quantity}
    offers: offersT = {"A": {3: 130, 5: 200}, "B": {2: 45}}
    free_items: free_itemsT = {"E": (2, "B")}

    def __init__(self) -> None:
        pass

    def _apply_free(self, sku2quant: sku2quantT) -> None:
        """
        Return `sku2quant` with free items' quantities reduced appropriately.

        Strictly speaking, overlapping offers could cause conflicts. For
        example, 2E could give a free C (value 20), while 3E could give a free
        B (value 30). So, what would 6E give?

        Further, these are items, and a customer would want to pick free items.
        This means that even if the prices were C=19, B=30, i.e., 2B being
        worth more than 3C, we shouldn't make this pick automatically.

        Therefore, we assume that such conflicts do not exist, as "offers are
        well balanced so that they can be safely combined".
        """
        for sku, quantity in sku2quant.items():
            try:
                free_quantity, free_sku = self.free_items[sku]
            except KeyError:
                pass
            else:
                free_item_quant = sku2quant.get(free_sku, 0)
                free_item_quant -= quantity // free_quantity
                if free_item_quant > 0:
                    sku2quant[free_sku] = free_item_quant
                else:
                    # TODO: Add extra free items to the basket?
                    sku2quant.pop(free_sku, None)

    def _get_best_price(
        self, price: int, quantity: int, sku_offers: sku_offersT,
    ) -> int:
        """
        Return the optimal price for the given quantity of items.

        Note that it is not always directly clear which discounts to apply. For
        example, let's say that we can get 5A for 200 or 7A for 270.

        * 7A can be 1 * 5A + 2 * A = 300 or 1 * 7A = 270, implying that we
          might prefer larger offers;

        * 10A can be 2 * 5A = 400 or 1 * 7A + 3 * A = 420, implying that we
          might prefer smaller offers.

        Further, in real world, offers don't always make sense ("buy 3" can be
        more expensive than buying 3 separate items).

        Since baskets are usually small and offers rarely very plentiful, we'll
        just try all possibilities and optimise later on if needed.

        :param price: Individual item's price (without any discounts).
        :param quantity: The quantity of the given item in the basket.
        :param sku_offers: A dictionary with all offers for that item.
        :return: The best price for the items.
        """
        result = quantity * price
        if not sku_offers:
            return result

        # Apply max. of each discount, in all possible orderings.
        for discount_counts in itertools.permutations(sku_offers):
            total_price = 0
            remaining_quantity = quantity
            for discount_cnt in discount_counts:
                discount_quantity = remaining_quantity // discount_cnt
                if discount_quantity:
                    total_price += discount_quantity * sku_offers[discount_cnt]
                    remaining_quantity -= discount_cnt * discount_quantity
                    if not remaining_quantity:
                        break
            total_price += remaining_quantity * price
            if total_price < result:
                result = total_price

        return result

    def get_item_price(self, sku: str, quantity: int) -> int:
        """
        Return the price for `quantity` number of items defined by `sku`.
        """
        try:
            price = self.prices[sku]
        except KeyError:
            raise ValueError(f"invalid SKU: {repr(sku)}")

        sku_offers = self.offers.get(sku, dict())
        return self._get_best_price(price, quantity, sku_offers)

    def get_basket_price(self, basket: str) -> int:
        """
        Return the price of the given basket or -1 if invalid.

        :param basked: A string containing SKUs.
        :return: The price of the basked with given SKUs, or -1 if some SKU is
            invalid (i.e., it does not exist in service's `prices` dictionary).
        """
        sku2quant: sku2quantT = dict()
        # Note: wrong specs. It said that SKUs are "individual letters of the
        # alphabet".
        for sku in basket:
            sku2quant[sku] = sku2quant.get(sku, 0) + 1
        try:
            return sum(
                self.get_item_price(sku, quantity)
                for sku, quantity in sku2quant.items()
            )
        except ValueError:
            return -1





