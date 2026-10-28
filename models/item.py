"""Product classes for CampusCart."""

from datetime import date
from math import isfinite


def validate_quantity(quantity):
    """Accept positive whole numbers, excluding booleans."""
    if type(quantity) is not int or quantity <= 0:
        raise ValueError("Quantity must be a whole number greater than zero.")


class Item:
    """A physical product with validated pricing and guarded stock changes."""

    def __init__(self, item_id, name, price, stock, category="General"):
        for label, value in (
            ("Product ID", item_id),
            ("Name", name),
            ("Category", category),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{label} must be non-empty text.")

        if type(stock) is not int or stock < 0:
            raise ValueError("Stock must be a non-negative whole number.")

        self._item_id = item_id.strip()
        self._name = name.strip()
        self._category = category.strip()
        self._stock = stock
        self.price = price

    @property
    def item_id(self):
        return self._item_id

    @property
    def name(self):
        return self._name

    @property
    def category(self):
        return self._category

    @property
    def price(self):
        return self._price

    @price.setter
    def price(self, value):
        if type(value) not in (int, float):
            raise ValueError("Price must be a positive, finite number.")

        try:
            valid = isfinite(value) and value > 0
        except OverflowError:
            valid = False

        if not valid:
            raise ValueError("Price must be a positive, finite number.")

        rounded_price = round(value, 2)

        if rounded_price <= 0:
            raise ValueError("Price must be at least 0.01.")

        self._price = rounded_price

    @property
    def stock(self):
        return self._stock

    @property
    def is_expired(self):
        return False

    @property
    def availability(self):
        return f"{self.stock} available" if self.stock else "Out of stock"

    def validate_purchase(self, quantity):
        """Check quantity and stock without changing the product."""
        validate_quantity(quantity)

        if quantity > self.stock:
            raise ValueError(
                f"Only {self.stock} units of {self.name} are available."
            )

    def reduce_stock(self, quantity):
        """Deduct stock only after validating the purchase."""
        self.validate_purchase(quantity)
        self._stock -= quantity

    def restock(self, quantity):
        """Increase physical stock using a valid quantity."""
        validate_quantity(quantity)
        self._stock += quantity


class PerishableItem(Item):
    """A product unavailable for purchase on or after its expiry date."""

    def __init__(
        self, item_id, name, price, stock, expiry_date, category="Food"
    ):
        super().__init__(item_id, name, price, stock, category)

        if type(expiry_date) is not date:
            raise ValueError("Expiry date must be a date object.")

        self._expiry_date = expiry_date

    @property
    def expiry_date(self):
        return self._expiry_date

    @property
    def is_expired(self):
        return date.today() >= self.expiry_date

    @property
    def availability(self):
        if self.is_expired:
            return "Expired / unavailable"

        return super().availability

    def validate_purchase(self, quantity):
        super().validate_purchase(quantity)

        if self.is_expired:
            raise ValueError(
                f"{self.name} has expired and cannot be sold."
            )


class DigitalVoucher(Item):
    """An unlimited digital product with no physical stock to deduct."""

    def __init__(self, item_id, name, price, category="Digital"):
        super().__init__(item_id, name, price, 0, category)

    @property
    def stock(self):
        return None

    @property
    def availability(self):
        return "Digital / unlimited"

    def validate_purchase(self, quantity):
        validate_quantity(quantity)

    def reduce_stock(self, quantity):
        """Validate the quantity without deducting physical inventory."""
        self.validate_purchase(quantity)

    def restock(self, quantity):
        raise ValueError(
            "Digital vouchers do not need physical stock."
        )