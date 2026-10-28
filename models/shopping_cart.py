"""Shopping cart operations, independent of the CLI and Streamlit."""

from math import isfinite

from models.item import Item, validate_quantity


class ShoppingCart:
    """Manage products without deducting stock before checkout."""

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
        """Recheck availability before a future checkout operation."""
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