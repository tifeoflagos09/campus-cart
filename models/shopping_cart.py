"""Shopping cart operations, independent of the CLI and Streamlit."""

from datetime import datetime, timezone
from math import isfinite
from uuid import uuid4

from models.item import Item, validate_quantity
from models.payment import PaymentMethod
from utils.logger import log_transaction
from utils.receipt import stream_receipt_lines


class ShoppingCart:
    """Manage products and complete simulated checkout."""

    def __init__(self):
        self._items = {}

    @property
    def items(self):
        """Return copies so callers cannot overwrite cart quantities."""
        return [entry.copy() for entry in self._items.values()]

    @property
    def is_empty(self):
        return not self._items

    def add_item(self, item, quantity):
        if not isinstance(item, Item):
            raise ValueError("Select a valid product.")

        validate_quantity(quantity)

        existing = self._items.get(item.item_id)

        if existing is not None and existing["item"] is not item:
            raise ValueError(
                "This product ID belongs to a different product."
            )

        current_quantity = existing["quantity"] if existing else 0
        combined_quantity = current_quantity + quantity

        item.validate_purchase(combined_quantity)

        self._items[item.item_id] = {
            "item": item,
            "quantity": combined_quantity,
        }

    def remove_item(self, item_id, quantity):
        validate_quantity(quantity)

        entry = self._items.get(item_id)

        if entry is None:
            raise ValueError("This product is not in your cart.")

        if quantity > entry["quantity"]:
            raise ValueError(
                f"You only have {entry['quantity']} units in your cart."
            )

        if quantity == entry["quantity"]:
            del self._items[item_id]
        else:
            entry["quantity"] -= quantity

    def clear(self):
        self._items.clear()

    def validate_items(self):
        """Recheck availability before checkout."""
        if self.is_empty:
            raise ValueError(
                "Your cart is empty. Add items before checkout."
            )

        for entry in self._items.values():
            entry["item"].validate_purchase(entry["quantity"])

    def calculate_totals(self):
        """Apply 10% off only when the subtotal exceeds 2,000 naira."""
        try:
            subtotal = round(
                sum(
                    entry["item"].price * entry["quantity"]
                    for entry in self._items.values()
                ),
                2,
            )
            valid = isfinite(subtotal)
        except OverflowError:
            valid = False

        if not valid:
            raise ValueError("Cart total is too large to calculate.")

        discount = (
            round(subtotal * 0.10, 2)
            if subtotal > 2000
            else 0.0
        )

        return {
            "subtotal": subtotal,
            "discount": discount,
            "total": round(subtotal - discount, 2),
        }

    def calculate_total(self):
        return self.calculate_totals()["total"]

    @log_transaction("CHECKOUT")
    def checkout(self, payment_method):
        """Complete a simulated payment and preserve its receipt."""
        if not isinstance(payment_method, PaymentMethod):
            raise ValueError("Select a valid payment method.")

        self.validate_items()
        totals = self.calculate_totals()
        entries = self.items

        # Save product details before clearing the cart.
        saved_items = [
            {
                "id": entry["item"].item_id,
                "name": entry["item"].name,
                "quantity": entry["quantity"],
                "unit_price": entry["item"].price,
                "subtotal": round(
                    entry["item"].price * entry["quantity"], 2
                ),
            }
            for entry in entries
        ]

        original_stock = [
            (entry["item"], entry["item"].stock)
            for entry in entries
            if entry["item"].stock is not None
        ]

        def restore_stock():
            """Restore physical stock after an unsuccessful checkout."""
            for item, stock in original_stock:
                difference = stock - item.stock

                if difference > 0:
                    item.restock(difference)

        try:
            # Reserve stock while the local payment simulation runs.
            for entry in entries:
                entry["item"].reduce_stock(entry["quantity"])

            payment = payment_method.process_payment(
                totals["total"]
            )

            if not isinstance(payment, dict):
                raise ValueError(
                    "Payment method returned an invalid result."
                )

            if payment.get("status") == "DECLINED":
                restore_stock()
                return payment

            if (
                payment.get("status") != "SUCCESS"
                or payment.get("amount") != totals["total"]
            ):
                raise ValueError(
                    "Payment was not completed correctly."
                )

            order = {
                "order_id": uuid4().hex[:12].upper(),
                "timestamp": datetime.now(timezone.utc).isoformat(
                    timespec="seconds"
                ),
                "items": saved_items,
                **totals,
                "payment": payment.copy(),
            }

            receipt = "\n".join(stream_receipt_lines(order))

        except Exception:
            restore_stock()
            raise

        self.clear()

        return {
            "status": "SUCCESS",
            "message": "Checkout completed successfully.",
            "order": order,
            "receipt": receipt,
        }