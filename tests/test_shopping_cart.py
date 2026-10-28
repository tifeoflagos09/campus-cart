"""Tests for cart quantities, availability, and discounts."""

import unittest
from datetime import date, timedelta

from models.item import Item, PerishableItem, DigitalVoucher
from models.shopping_cart import ShoppingCart


class ShoppingCartTests(unittest.TestCase):

    def setUp(self):
        self.cart = ShoppingCart()
        self.notebook = Item("101", "Notebook", 500, 10)

    def test_repeated_additions_and_stock_limit(self):
        self.cart.add_item(self.notebook, 3)
        self.cart.add_item(self.notebook, 2)

        self.assertEqual(len(self.cart.items), 1)
        self.assertEqual(self.cart.items[0]["quantity"], 5)

        with self.assertRaises(ValueError):
            self.cart.add_item(self.notebook, 6)

        self.assertEqual(self.cart.items[0]["quantity"], 5)
        self.assertEqual(self.notebook.stock, 10)

    def test_invalid_additions(self):
        for quantity in (0, -1, True, 1.5, "2"):
            with self.assertRaises(ValueError):
                self.cart.add_item(self.notebook, quantity)

        with self.assertRaises(ValueError):
            self.cart.add_item("Notebook", 1)

        self.assertTrue(self.cart.is_empty)

    def test_partial_and_full_removal(self):
        self.cart.add_item(self.notebook, 3)
        self.cart.remove_item("101", 1)

        self.assertEqual(self.cart.items[0]["quantity"], 2)

        self.cart.remove_item("101", 2)

        self.assertTrue(self.cart.is_empty)
        self.assertEqual(self.notebook.stock, 10)

    def test_invalid_removal_preserves_cart(self):
        self.cart.add_item(self.notebook, 3)

        for quantity in (0, -1, True, 1.5, "2", 4):
            with self.assertRaises(ValueError):
                self.cart.remove_item("101", quantity)

        with self.assertRaises(ValueError):
            self.cart.remove_item("999", 1)

        self.assertEqual(self.cart.items[0]["quantity"], 3)

    def test_discount_threshold(self):
        self.cart.add_item(self.notebook, 4)

        self.assertEqual(self.cart.calculate_total(), 2000)

        self.cart.add_item(self.notebook, 1)

        self.assertEqual(
            self.cart.calculate_totals(),
            {
                "subtotal": 2500,
                "discount": 250,
                "total": 2250,
            },
        )

    def test_empty_cart_and_clear(self):
        self.assertEqual(self.cart.calculate_total(), 0)

        with self.assertRaises(ValueError):
            self.cart.validate_items()

        self.cart.add_item(self.notebook, 2)
        self.cart.clear()

        self.assertTrue(self.cart.is_empty)
        self.assertEqual(self.notebook.stock, 10)

    def test_cart_entries_are_protected(self):
        self.cart.add_item(self.notebook, 2)

        snapshot = self.cart.items
        snapshot[0]["quantity"] = 999
        snapshot.clear()

        self.assertEqual(self.cart.items[0]["quantity"], 2)

    def test_duplicate_id_with_different_product_is_rejected(self):
        self.cart.add_item(self.notebook, 1)
        other = Item("101", "Different product", 100, 50)

        with self.assertRaises(ValueError):
            self.cart.add_item(other, 1)

        self.assertEqual(self.cart.calculate_total(), 500)

    def test_stock_is_rechecked(self):
        self.cart.add_item(self.notebook, 5)

        # Simulate stock changing after the product was added.
        self.notebook.reduce_stock(6)

        with self.assertRaises(ValueError):
            self.cart.validate_items()

        self.assertEqual(self.cart.items[0]["quantity"], 5)

    def test_product_subclasses(self):
        expired = PerishableItem(
            "108",
            "Sandwich",
            1500,
            5,
            date.today() - timedelta(days=1),
        )

        with self.assertRaises(ValueError):
            self.cart.add_item(expired, 1)

        voucher = DigitalVoucher("109", "Printing voucher", 1000)
        self.cart.add_item(voucher, 100)
        self.cart.validate_items()

        self.assertEqual(self.cart.calculate_total(), 90000)
        self.assertIsNone(voucher.stock)


if __name__ == "__main__":
    unittest.main()