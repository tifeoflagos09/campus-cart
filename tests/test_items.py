"""Tests for CampusCart product classes."""

import unittest
from datetime import date, timedelta

from models.item import Item, PerishableItem, DigitalVoucher


class ItemTests(unittest.TestCase):

    def test_purchase_and_restock(self):
        item = Item("101", "Campus T-shirt", 5000, 10)

        item.validate_purchase(3)
        self.assertEqual(item.stock, 10)

        item.reduce_stock(3)
        self.assertEqual(item.stock, 7)

        item.restock(2)
        self.assertEqual(item.stock, 9)

    def test_invalid_quantities(self):
        item = Item("101", "Notebook", 500, 3)

        for quantity in (0, -1, 1.5, True, "2", 4):
            with self.subTest(quantity=quantity):
                with self.assertRaises(ValueError):
                    item.reduce_stock(quantity)

                self.assertEqual(item.stock, 3)

        for quantity in (0, -1, 1.5, True, "2"):
            with self.assertRaises(ValueError):
                item.restock(quantity)

        self.assertEqual(item.stock, 3)

    def test_price_validation(self):
        item = Item("101", "Notebook", 500, 3)

        invalid_prices = (
            0,
            -1,
            True,
            "500",
            None,
            float("nan"),
            float("inf"),
            0.001,
        )

        for price in invalid_prices:
            with self.subTest(price=price):
                with self.assertRaises(ValueError):
                    item.price = price

                self.assertEqual(item.price, 500)

        item.price = 550.50
        self.assertEqual(item.price, 550.50)

    def test_invalid_product_details(self):
        for stock in (-1, True, 1.5, "3"):
            with self.assertRaises(ValueError):
                Item("101", "Notebook", 500, stock)

        with self.assertRaises(ValueError):
            Item("", "Notebook", 500, 3)

        with self.assertRaises(ValueError):
            Item("101", " ", 500, 3)

        with self.assertRaises(ValueError):
            Item("101", "Notebook", 500, 3, category="")

    def test_stock_protection(self):
        item = Item("101", "Notebook", 500, 0)

        with self.assertRaises(AttributeError):
            item.stock = 100

        with self.assertRaises(ValueError):
            item.reduce_stock(1)

        self.assertEqual(item.stock, 0)
        self.assertEqual(item.availability, "Out of stock")

    def test_expired_products(self):
        expiry_dates = (
            date.today(),
            date.today() - timedelta(days=1),
        )

        for expiry in expiry_dates:
            item = PerishableItem(
                "108", "Sandwich", 1500, 5, expiry
            )

            self.assertTrue(item.is_expired)

            with self.assertRaises(ValueError):
                item.reduce_stock(1)

            self.assertEqual(item.stock, 5)

    def test_fresh_products(self):
        item = PerishableItem(
            "108",
            "Sandwich",
            1500,
            5,
            date.today() + timedelta(days=2),
        )

        item.reduce_stock(2)

        self.assertEqual(item.stock, 3)
        self.assertFalse(item.is_expired)

        with self.assertRaises(ValueError):
            PerishableItem(
                "108", "Sandwich", 1500, 5, "2026-11-01"
            )

    def test_digital_vouchers(self):
        voucher = DigitalVoucher(
            "109", "Printing voucher", 1000
        )

        voucher.reduce_stock(10000)

        self.assertIsNone(voucher.stock)
        self.assertEqual(
            voucher.availability, "Digital / unlimited"
        )

        for quantity in (0, -1, True, 1.5, "2"):
            with self.assertRaises(ValueError):
                voucher.reduce_stock(quantity)

        with self.assertRaises(ValueError):
            voucher.restock(1)


if __name__ == "__main__":
    unittest.main()