from solutions.CHK import checkout_solution
from solutions.CHK.checkout_service import CheckoutService


class TestCheckout():
    @classmethod
    def setup_class(cls):
        # This would likely be done by mocking a file name or DB responses.
        cls.bak_prices = CheckoutService.prices
        cls.bak_offers = CheckoutService.offers
        CheckoutService.prices = {"x": 17, "y": 19, "z": 23}
        CheckoutService.offers = {"x": (5, 63), "y": (11, 191)}

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

