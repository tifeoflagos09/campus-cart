"""Integration tests for checkout, receipts, stock, and audit outcomes."""

import unittest
from datetime import date, timedelta
from unittest.mock import patch

from models.item import Item, PerishableItem, DigitalVoucher
from models.payment import (
    CashPayment,
    CardPayment,
    MobileMoneyPayment,
)
from models.shopping_cart import ShoppingCart
from utils.receipt import stream_receipt_lines


class CheckoutTests(unittest.TestCase):

    def setUp(self):
        self.cart = ShoppingCart()
        self.logs = []
        self.shirt = Item(
            "103", "Campus T-shirt", 5000, 10
        )
        self.cart.add_item(self.shirt, 1)

    def test_successful_cash_checkout(self):
        result = self.cart.checkout(
            CashPayment(5000), audit_log=self.logs
        )

        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(result["order"]["total"], 4500)
        self.assertEqual(
            result["order"]["payment"]["change"], 500
        )
        self.assertEqual(self.shirt.stock, 9)
        self.assertTrue(self.cart.is_empty)
        self.assertEqual(self.logs[-1]["status"], "SUCCESS")
        self.assertGreaterEqual(
            self.logs[-1]["duration_ms"], 0
        )

    def test_declined_payments_preserve_cart_and_stock(self):
        payments = (
            CashPayment(100),
            CardPayment(False),
            MobileMoneyPayment(False),
        )

        for payment in payments:
            with self.subTest(method=type(payment).__name__):
                result = self.cart.checkout(
                    payment, audit_log=self.logs
                )

                self.assertEqual(
                    result["status"], "DECLINED"
                )
                self.assertEqual(self.shirt.stock, 10)
                self.assertEqual(
                    self.cart.items[0]["quantity"], 1
                )
                self.assertEqual(
                    self.logs[-1]["status"], "DECLINED"
                )

    def test_empty_checkout_is_logged_as_failed(self):
        self.cart.clear()

        with self.assertRaises(ValueError):
            self.cart.checkout(
                CardPayment(), audit_log=self.logs
            )

        self.assertEqual(self.logs[-1]["status"], "FAILED")
        self.assertEqual(self.shirt.stock, 10)

    def test_changed_stock_blocks_checkout(self):
        self.shirt.reduce_stock(10)

        with self.assertRaises(ValueError):
            self.cart.checkout(
                CardPayment(), audit_log=self.logs
            )

        self.assertEqual(self.shirt.stock, 0)
        self.assertFalse(self.cart.is_empty)
        self.assertEqual(self.logs[-1]["status"], "FAILED")

    def test_stock_update_failure_rolls_back_other_items(self):
        bag = Item("104", "Tote bag", 2500, 5)
        self.cart.add_item(bag, 1)

        with patch.object(
            bag,
            "reduce_stock",
            side_effect=ValueError("Stock error"),
        ):
            with self.assertRaises(ValueError):
                self.cart.checkout(
                    CardPayment(), audit_log=self.logs
                )

        self.assertEqual(self.shirt.stock, 10)
        self.assertEqual(bag.stock, 5)
        self.assertEqual(len(self.cart.items), 2)
        self.assertEqual(self.logs[-1]["status"], "FAILED")

    def test_payment_exception_restores_stock(self):
        payment = CardPayment()

        with patch.object(
            payment,
            "process_payment",
            side_effect=ValueError("Payment error"),
        ):
            with self.assertRaises(ValueError):
                self.cart.checkout(
                    payment, audit_log=self.logs
                )

        self.assertEqual(self.shirt.stock, 10)
        self.assertFalse(self.cart.is_empty)
        self.assertEqual(self.logs[-1]["status"], "FAILED")

    def test_invalid_payment_result_restores_stock(self):
        payment = CardPayment()

        invalid_results = (
            None,
            {"status": "SUCCESS", "amount": -1},
        )

        for invalid in invalid_results:
            with patch.object(
                payment,
                "process_payment",
                return_value=invalid,
            ):
                with self.assertRaises(ValueError):
                    self.cart.checkout(
                        payment, audit_log=self.logs
                    )

            self.assertEqual(self.shirt.stock, 10)
            self.assertFalse(self.cart.is_empty)

    def test_receipt_survives_cart_clear_and_price_change(self):
        result = self.cart.checkout(
            CardPayment(), audit_log=self.logs
        )

        self.shirt.price = 6000

        self.assertTrue(self.cart.is_empty)
        self.assertIn("Campus T-shirt", result["receipt"])
        self.assertIn("₦4,500.00", result["receipt"])
        self.assertEqual(
            result["order"]["items"][0]["unit_price"],
            5000,
        )
        self.assertEqual(
            result["receipt"],
            "\n".join(stream_receipt_lines(result["order"])),
        )

    def test_digital_voucher_checkout(self):
        voucher = DigitalVoucher(
            "109", "Printing voucher", 1000
        )
        self.cart.add_item(voucher, 2)

        result = self.cart.checkout(
            MobileMoneyPayment(), audit_log=self.logs
        )

        self.assertEqual(result["order"]["total"], 6300)
        self.assertIsNone(voucher.stock)
        self.assertEqual(self.shirt.stock, 9)

    def test_expiry_is_rechecked_at_checkout(self):
        tomorrow = date.today() + timedelta(days=1)

        sandwich = PerishableItem(
            "108", "Sandwich", 1500, 5, tomorrow
        )
        self.cart.add_item(sandwich, 1)

        with patch("models.item.date") as mock_date:
            mock_date.today.return_value = tomorrow

            with self.assertRaises(ValueError):
                self.cart.checkout(
                    CardPayment(), audit_log=self.logs
                )

        self.assertEqual(sandwich.stock, 5)
        self.assertEqual(self.shirt.stock, 10)

    def test_missing_audit_log_blocks_checkout(self):
        with self.assertRaises(ValueError):
            self.cart.checkout(CardPayment())

        self.assertEqual(self.shirt.stock, 10)
        self.assertFalse(self.cart.is_empty)


if __name__ == "__main__":
    unittest.main()