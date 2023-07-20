import unittest.mock

import pytest

from solutions.CHK import checkout_solution
from solutions.CHK.checkout_service import CheckoutService


class TestCheckout():

    @classmethod
    def setup_class(cls):
        # This would likely be done by mocking a file name or DB responses.
        cls.bak_prices = CheckoutService.prices
        cls.bak_offers = CheckoutService.offers
        CheckoutService.prices = {"x": 17, "y": 19, "z": 23}
        CheckoutService.offers = {"x": {5: 63}, "y": {11: 191}}

    @classmethod
    def teardown_class(cls):
        CheckoutService.prices = cls.bak_prices
        CheckoutService.offers = cls.bak_offers

    def test_checkout_item_price_simple(self):
        service = CheckoutService()
        assert service.get_item_price("x", 1) == 17

    def test_checkout_item_price_multi(self):
        service = CheckoutService()
        assert service.get_item_price("x", 3) == 3 * 17

    def test_checkout_item_price_offer(self):
        service = CheckoutService()
        assert service.get_item_price("x", 5) == 63

    def test_checkout_item_price_beyond_offer(self):
        service = CheckoutService()
        assert service.get_item_price("x", 7) == 63 + 2 * 17

    def test_checkout_item_price_beyond_multiple_offers(self):
        service = CheckoutService()
        assert service.get_item_price("x", 3 * 5 + 2) == 3 * 63 + 2 * 17

    def test_checkout_item_price_no_offers(self):
        service = CheckoutService()
        assert service.get_item_price("z", 1719) == 1719 * 23

    def test_checkout_item_price_invalid_sku(self):
        service = CheckoutService()
        with pytest.raises(ValueError):
            service.get_item_price("WRONG", 1719)

    def test_checkout_basket_price_simple(self):
        service = CheckoutService()
        assert service.get_basket_price("x") == 17

    def test_checkout_basket_price_multi(self):
        service = CheckoutService()
        assert service.get_basket_price(3 * "x") == 3 * 17

    def test_checkout_basket_price_offer(self):
        service = CheckoutService()
        assert service.get_basket_price(5 * "x") == 63

    def test_checkout_basket_price_beyond_offer(self):
        service = CheckoutService()
        assert service.get_basket_price(7 * "x") == 63 + 2 * 17

    def test_checkout_basket_price_beyond_multiple_offers(self):
        service = CheckoutService()
        assert service.get_basket_price((3 * 5 + 2) * "x") == 3 * 63 + 2 * 17

    def test_checkout_basket_price_no_offers(self):
        service = CheckoutService()
        assert service.get_basket_price(1719 * "z") == 1719 * 23

    def test_checkout_basket_price_invalid_sku(self):
        service = CheckoutService()
        assert service.get_basket_price("xEx") == -1

    def test_checkout_basket_price_empty(self):
        service = CheckoutService()
        assert service.get_basket_price("") == 0

    def test_checkout_basket_price_mixed_skus(self):
        service = CheckoutService()

        # Basket: 7 of each
        basket_str = 7 * "xyz"
        expected = (
            1 * 63 + 2 * 17  # price for x
            + 7 * 19  # price for y (offer requirement not reached)
            + 7 * 23  # price for z (no offers)
        )
        assert service.get_basket_price(basket_str) == expected

        # Basket: 13 x, 17 y, 3 z
        basket_str = "yyyxxyzyxyxyyyxyyyxxzxxyyyxxyyzxx"
        expected = (
            2 * 63 + 3 * 17  # price for x (2 offers of 5 items + 3 remaining)
            + 1 * 191 + 6 * 19  # price for y (1 offer of 11 items + 6 remain.)
            + 3 * 23  # price for z (no offers)
        )
        assert service.get_basket_price(basket_str) == expected

    def test_checkout(self):
        with unittest.mock.patch.object(
            CheckoutService, "get_basket_price",
        ) as mock:
            checkout_solution.checkout("xyz")
        mock.assert_called_with("xyz")


class TestCheckout2():

    @classmethod
    def setup_class(cls):
        # Let's use values from the example in CheckoutService._get_best_price
        # to catch some cases that the original data misses.
        # This whole class would normally be a rework of the above, but that
        # would include crafting test data for all cases, and it's easier to
        # just have a completely new one without the need to "fix" the expected
        # results above.
        cls.bak_prices = CheckoutService.prices
        cls.bak_offers = CheckoutService.offers
        cls.bak_free_items = CheckoutService.free_items
        CheckoutService.prices = {"A": 50, "B": 30, "C": 20, "D": 15, "E": 40}
        CheckoutService.offers = {"A": {5: 200, 7: 270}, "B": {2: 45}}
        CheckoutService.free_items = {"E": (2, "B")}

    @classmethod
    def teardown_class(cls):
        CheckoutService.prices = cls.bak_prices
        CheckoutService.offers = cls.bak_offers
        CheckoutService.free_items = cls.bak_free_items

    def test_checkout_basket_with_competing_offers(self):
        # Test two offers from docstring examples in
        service = CheckoutService()

        assert service.get_basket_price(7 * "A") == 270
        assert service.get_basket_price(10 * "A") == 400

    def test_checkout_basket_with_free_stuff(self):
        # Test two offers from docstring examples in
        service = CheckoutService()

        # Nothing is free (because B is not in the basket).
        assert service.get_basket_price("EE") == 2 * 40

        # Nothing is free (because we don't have enough of E in the basket).
        assert service.get_basket_price("BE") == 1 * 30 + 1 * 40

        # B is free, E is charged at full price.
        assert service.get_basket_price("BEE") == 0 * 30 + 2 * 40

        # B is free, E is charged at full price.
        assert service.get_basket_price("BEEE") == 0 * 30 + 3 * 40

        # B is free, but only once (could be twice, but we don't have two of
        # B), E is charged at full price.
        assert service.get_basket_price("BEEEE") == 0 * 30 + 4 * 40

        # One B is free, but the other one isn't (we only have two of E), E is
        # charged at full price.
        assert service.get_basket_price("BBEE") == 1 * 30 + 2 * 40

        # One B is free, and the remaining two go at a discounted price, while
        # E is charged at full price.
        assert service.get_basket_price("BBBEE") == 1 * 45 + 2 * 40

        # One B is free, two of the remaining ones go at a discounted price,
        # while the fourth one and E go at full price.
        assert service.get_basket_price("BBBBEE") == 1 * 45 + 1 * 30 + 2 * 40

