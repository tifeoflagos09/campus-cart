"""Tests for discounts, coupon eligibility, delivery, and checkout."""

import unittest
from unittest.mock import patch

from models.item import Item, DigitalVoucher
from models.payment import CashPayment, CardPayment
from models.shopping_cart import ShoppingCart
from utils.pricing import calculate_quote


class PricingTests(unittest.TestCase):

    def test_automatic_discount_and_threshold(self):
        self.assertEqual(
            calculate_quote(2000)["discount"], 0
        )

        quote = calculate_quote(7500)

        self.assertEqual(quote["discount"], 750)
        self.assertEqual(quote["total"], 6750)

    def test_coupon_replaces_automatic_discount(self):
        quote = calculate_quote(7500, " campus15 ")

        self.assertEqual(quote["coupon_code"], "CAMPUS15")
        self.assertEqual(quote["discount"], 1125)
        self.assertEqual(quote["total"], 6375)

    def test_coupon_minimum_subtotal(self):
        for subtotal in (0, 1000, 4999.99):
            with self.assertRaises(ValueError):
                calculate_quote(subtotal, "CAMPUS15")

        self.assertEqual(
            calculate_quote(5000, "CAMPUS15")["total"],
            4250,
        )

    def test_redeemed_coupon_is_rejected(self):
        with self.assertRaises(ValueError):
            calculate_quote(
                7500, "CAMPUS15", coupon_used=True
            )

        self.assertEqual(
            calculate_quote(7500, coupon_used=True)["total"],
            6750,
        )

    def test_delivery_fee_is_added_after_discount(self):
        quote = calculate_quote(
            7500, delivery_method="Campus delivery"
        )

        self.assertEqual(quote["delivery_fee"], 500)
        self.assertEqual(quote["total"], 7250)

        quote = calculate_quote(
            7500, "CAMPUS15", "Campus delivery"
        )

        self.assertEqual(quote["total"], 6875)

    def test_digital_only_orders_have_no_delivery_charge(self):
        quote = calculate_quote(
            1000,
            delivery_method="Campus delivery",
            has_physical_items=False,
        )

        self.assertEqual(quote["delivery_fee"], 0)
        self.assertEqual(
            quote["delivery_method"], "No physical delivery"
        )
        self.assertEqual(quote["total"], 1000)

    def test_empty_cart_has_no_delivery_charge(self):
        quote = calculate_quote(
            0, delivery_method="Campus delivery"
        )

        self.assertEqual(quote["total"], 0)

    def test_invalid_order_options(self):
        for code in ("BADCODE", None, True):
            with self.assertRaises(ValueError):
                calculate_quote(7500, code)

        with self.assertRaises(ValueError):
            calculate_quote(
                7500, delivery_method="Unknown"
            )

        with self.assertRaises(ValueError):
            calculate_quote(
                7500, has_physical_items="False"
            )

        with self.assertRaises(ValueError):
            calculate_quote(
                7500, coupon_used="False"
            )

    def test_invalid_subtotals(self):
        invalid_subtotals = (
            -1,
            True,
            "7500",
            None,
            float("nan"),
            float("inf"),
            10 ** 1000,
        )

        for subtotal in invalid_subtotals:
            with self.subTest(subtotal=subtotal):
                with self.assertRaises(ValueError):
                    calculate_quote(subtotal)


class PricingCheckoutTests(unittest.TestCase):

    def setUp(self):
        self.cart = ShoppingCart()
        self.shirt = Item(
            "104", "Campus T-shirt", 5000, 12
        )
        self.bag = Item(
            "105", "Canvas Tote Bag", 2500, 10
        )
        self.cart.add_item(self.shirt, 1)
        self.cart.add_item(self.bag, 1)
        self.logs = []

    def test_coupon_and_delivery_match_payment_and_receipt(self):
        quote = self.cart.calculate_quote(
            "CAMPUS15", "Campus delivery"
        )

        self.assertEqual(quote["total"], 6875)

        result = self.cart.checkout(
            CardPayment(),
            coupon_code="CAMPUS15",
            delivery_method="Campus delivery",
            audit_log=self.logs,
        )

        self.assertEqual(
            result["order"]["total"], quote["total"]
        )
        self.assertEqual(
            result["order"]["payment"]["amount"], 6875
        )
        self.assertIn("CAMPUS15", result["receipt"])
        self.assertIn("Campus delivery", result["receipt"])
        self.assertIn("₦6,875.00", result["receipt"])
        self.assertEqual(self.shirt.stock, 11)
        self.assertEqual(self.bag.stock, 9)
        self.assertEqual(self.logs[-1]["status"], "SUCCESS")

    def test_invalid_coupon_never_calls_payment_or_changes_stock(self):
        payment = CardPayment()

        with patch.object(
            payment, "process_payment"
        ) as process:
            with self.assertRaises(ValueError):
                self.cart.checkout(
                    payment,
                    coupon_code="WRONG",
                    audit_log=self.logs,
                )

            process.assert_not_called()

        self.assertEqual(self.shirt.stock, 12)
        self.assertEqual(self.bag.stock, 10)
        self.assertFalse(self.cart.is_empty)
        self.assertEqual(self.logs[-1]["status"], "FAILED")

    def test_insufficient_cash_restores_stock_with_delivery(self):
        result = self.cart.checkout(
            CashPayment(6750),
            delivery_method="Campus delivery",
            audit_log=self.logs,
        )

        self.assertEqual(result["status"], "DECLINED")
        self.assertEqual(self.shirt.stock, 12)
        self.assertEqual(self.bag.stock, 10)
        self.assertFalse(self.cart.is_empty)

    def test_digital_checkout_has_no_delivery_fee(self):
        self.cart.clear()

        voucher = DigitalVoucher(
            "109", "Printing Voucher", 1000
        )
        self.cart.add_item(voucher, 5)

        result = self.cart.checkout(
            CardPayment(),
            coupon_code="CAMPUS15",
            delivery_method="Campus delivery",
            audit_log=self.logs,
        )

        self.assertEqual(result["order"]["total"], 4250)
        self.assertEqual(result["order"]["delivery_fee"], 0)
        self.assertIn(
            "No physical delivery", result["receipt"]
        )

    def test_coupon_is_consumed_only_once(self):
        self.cart.checkout(
            CardPayment(),
            coupon_code="CAMPUS15",
            audit_log=self.logs,
        )

        self.assertTrue(self.cart.coupon_used)
        self.cart.add_item(self.shirt, 1)

        with self.assertRaises(ValueError):
            self.cart.checkout(
                CardPayment(),
                coupon_code="CAMPUS15",
                audit_log=self.logs,
            )

        self.assertEqual(self.shirt.stock, 11)
        self.assertFalse(self.cart.is_empty)

        result = self.cart.checkout(
            CardPayment(), audit_log=self.logs
        )

        self.assertEqual(result["order"]["total"], 4500)

    def test_declined_payment_does_not_consume_coupon(self):
        result = self.cart.checkout(
            CashPayment(100),
            coupon_code="CAMPUS15",
            audit_log=self.logs,
        )

        self.assertEqual(result["status"], "DECLINED")
        self.assertFalse(self.cart.coupon_used)
        self.assertEqual(self.shirt.stock, 12)
        self.assertEqual(self.bag.stock, 10)

        result = self.cart.checkout(
            CardPayment(),
            coupon_code="CAMPUS15",
            audit_log=self.logs,
        )

        self.assertEqual(result["status"], "SUCCESS")
        self.assertTrue(self.cart.coupon_used)

    def test_clear_cart_does_not_reset_coupon_usage(self):
        self.cart.checkout(
            CardPayment(),
            coupon_code="CAMPUS15",
            audit_log=self.logs,
        )

        self.cart.add_item(self.shirt, 1)
        self.cart.clear()

        self.assertTrue(self.cart.coupon_used)

    def test_new_session_has_separate_coupon_eligibility(self):
        self.cart.checkout(
            CardPayment(),
            coupon_code="CAMPUS15",
            audit_log=self.logs,
        )

        other = ShoppingCart()
        other.add_item(self.shirt, 1)

        self.assertFalse(other.coupon_used)
        self.assertEqual(
            other.calculate_quote("CAMPUS15")["total"],
            4250,
        )

    def test_minimum_excludes_delivery_fee(self):
        self.cart.clear()
        self.cart.add_item(
            Item("200", "Demo item", 4500, 2), 1
        )
        payment = CardPayment()

        with patch.object(
            payment, "process_payment"
        ) as process:
            with self.assertRaises(ValueError):
                self.cart.checkout(
                    payment,
                    coupon_code="CAMPUS15",
                    delivery_method="Campus delivery",
                    audit_log=self.logs,
                )

            process.assert_not_called()

    def test_failed_stock_update_preserves_coupon(self):
        with patch.object(
            self.bag,
            "reduce_stock",
            side_effect=ValueError("Stock error"),
        ):
            with self.assertRaises(ValueError):
                self.cart.checkout(
                    CardPayment(),
                    coupon_code="CAMPUS15",
                    audit_log=self.logs,
                )

        self.assertFalse(self.cart.coupon_used)
        self.assertEqual(self.shirt.stock, 12)
        self.assertEqual(self.bag.stock, 10)

    def test_receipt_failure_preserves_coupon_and_stock(self):
        with patch(
            "models.shopping_cart.stream_receipt_lines",
            side_effect=ValueError("Receipt error"),
        ):
            with self.assertRaises(ValueError):
                self.cart.checkout(
                    CardPayment(),
                    coupon_code="CAMPUS15",
                    audit_log=self.logs,
                )

        self.assertFalse(self.cart.coupon_used)
        self.assertEqual(self.shirt.stock, 12)
        self.assertEqual(self.bag.stock, 10)

    def test_removing_physical_items_removes_delivery_charge(self):
        voucher = DigitalVoucher(
            "109", "Printing Voucher", 1000
        )
        self.cart.add_item(voucher, 1)
        self.cart.remove_item("104", 1)
        self.cart.remove_item("105", 1)

        quote = self.cart.calculate_quote(
            delivery_method="Campus delivery"
        )

        self.assertEqual(quote["delivery_fee"], 0)
        self.assertEqual(quote["total"], 1000)


if __name__ == "__main__":
    unittest.main()