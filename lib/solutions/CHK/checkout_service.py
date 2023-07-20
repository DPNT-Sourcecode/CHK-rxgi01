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
groupsT: TypeAlias = dict[str, tuple[int, int]]


class CheckoutService:
    """
    Service for handling checkouts.
    """

    # We'll normally want these in a DB or some file.
    # Prices: SKU -> price
    prices: sku_pricesT = {
        "A": 50, "B": 30, "C": 20, "D": 15, "E": 40, "F": 10, "G": 20, "H": 10,
        "I": 35, "J": 60, "K": 70, "L": 90, "M": 15, "N": 40, "O": 10, "P": 50,
        "Q": 30, "R": 50, "S": 20, "T": 20, "U": 40, "V": 50, "W": 20, "X": 17,
        "Y": 20, "Z": 21,
    }
    # Offers: SKU -> {quantity -> price_for_that_quantity}
    offers: offersT = {
        "A": {3: 130, 5: 200},
        "B": {2: 45},
        "H": {5: 45, 10: 80},
        "K": {2: 120},
        "P": {5: 200},
        "Q": {3: 80},
        "V": {2: 90, 3: 130},
    }
    free_items: free_itemsT = {
        "E": (2, "B"),
        "F": (2, "F"),
        "N": (3, "M"),
        "R": (3, "Q"),
        "U": (3, "U"),
    }
    groups: groupsT = {
        "STXYZ": (3, 45),
    }

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
        remove_skus: set[str] = set()
        for sku, quantity in sku2quant.items():
            try:
                free_quantity, free_sku = self.free_items[sku]
            except KeyError:
                pass
            else:
                if free_sku == sku:
                    free_quantity += 1
                free_item_quant = sku2quant.get(free_sku, 0)
                free_item_quant -= quantity // free_quantity
                if free_item_quant > 0:
                    sku2quant[free_sku] = free_item_quant
                else:
                    # TODO: Add extra free items to the basket?
                    remove_skus.add(free_sku)

        for remove_sku in remove_skus:
            sku2quant.pop(remove_sku, None)

    def _apply_groups(self, sku2quant: sku2quantT) -> int:
        """
        Update `sku2quant` by applying group prices and return their price.

        We assume that group offers are better than the individual ones, i.e.,
        that applying group takes priority. Not assuming so would introduce
        some serious problems:

        * It would complicate the code and require a significant refactor, as
          we could no longer compute the prices for individual items.

        * The ambiguity of which items to leave outside of the groups when the
          groups don't encompass all of them (the group discount comes at `k`
          items, but we have `m * k + r` for some `r` such that `0 < r < k`).

        * Extra mess with free items (does 2E give B if it is also applying for
          a group discount? usually not, but it's undefined here).

        The data does not require this, so we're not doing it, while also
        praying to the elder gods to strike Marketing with a lightning bolt if
        the consider adding such offers.
        """
        result = 0

        for group, (group_cnt, group_price) in self.groups.items():
            remove_skus: set[str] = set()
            total_cnt = sum(
                sku_quant
                for sku, sku_quant in sku2quant.items()
                if sku in group
            )
            remaining_cnt = total_cnt // group_cnt
            if not remaining_cnt:
                # Not enough for a discount.
                continue

            # Take away discounted items (weirdly enough, most expensive
            # first).
            for sku, _ in sorted(
                self.prices.items(), key=lambda it: it[1], reverse=True,
            ):
                if sku not in group:
                    continue
                item_cnt = sku2quant.get(sku, 0)
                discount_cnt = min(remaining_cnt, item_cnt)
                if discount_cnt:
                    remaining_cnt -= discount_cnt
                    item_cnt -= discount_cnt
                    result += discount_cnt * group_price
                    if item_cnt:
                        sku2quant[sku] = item_cnt
                    else:
                        remove_skus.add(sku)
                    if not remaining_cnt:
                        break

            for remove_sku in remove_skus:
                sku2quant.pop(remove_sku, None)

        return result

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
        self._apply_free(sku2quant)
        self._apply_groups(sku2quant)
        try:
            return sum(
                self.get_item_price(sku, quantity)
                for sku, quantity in sku2quant.items()
            )
        except ValueError:
            return -1


