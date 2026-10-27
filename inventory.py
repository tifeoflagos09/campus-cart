"""
CampusCart inventory module.

Handles inventory display, stock checks, price quotes,
and inventory filtering/sorting.
"""

from math import isfinite


def is_non_negative_number(value):
    """Check that a value is a finite, non-negative number."""
    if type(value) not in (int, float):
        return False

    try:
        return isfinite(value) and value >= 0
    except OverflowError:
        return False


def show_inventory(inventory):
    """Display products, prices, and stock."""
    print(f"\n{'ID':<6}{'Product':<20}{'Price':<14}{'Stock':<6}")
    print("-" * 46)

    for item_id, item in inventory.items():
        price = f"₦{item['price']:,.2f}"

        print(
            f"{item_id:<6}{item['name']:<20}"
            f"{price:<14}{item['stock']:<6}"
        )

    print()


def is_stock_available(inventory, item_id, requested_qty):
    """Check whether a positive whole-number quantity is available."""
    item = inventory.get(item_id)

    if item is None:
        return False

    if type(requested_qty) is not int or requested_qty <= 0:
        return False

    stock = item.get("stock")

    if type(stock) is not int or stock < 0:
        return False

    return requested_qty <= stock


def update_item_stock(inventory, item_id, qty_change):
    """Increase or decrease stock without allowing negative stock."""
    item = inventory.get(item_id)

    if item is None or type(qty_change) is not int:
        return False

    stock = item.get("stock")

    if type(stock) is not int or stock < 0:
        return False

    new_stock = stock + qty_change

    if new_stock < 0:
        return False

    item["stock"] = new_stock
    return True


def get_price_quote(
    inventory,
    item_id,
    qty,
    tax_rate=0.0,
    discount_rate=0.10,
    discount_threshold=2000,
):
    """Calculate subtotal, discount, tax, and total for an item quantity."""
    if item_id not in inventory:
        return None

    if type(qty) is not int or qty <= 0:
        raise ValueError(
            "Quantity must be a whole number greater than zero."
        )

    unit_price = inventory[item_id]["price"]

    if not is_non_negative_number(unit_price):
        raise ValueError(
            "Price must be a finite, non-negative number."
        )

    for rate in (tax_rate, discount_rate):
        if not is_non_negative_number(rate) or rate > 1:
            raise ValueError(
                "Tax and discount rates must be between 0 and 1."
            )

    if not is_non_negative_number(discount_threshold):
        raise ValueError(
            "Discount threshold must be finite and non-negative."
        )

    try:
        subtotal = round(unit_price * qty, 2)
    except OverflowError as error:
        raise ValueError(
            "The requested amount is too large."
        ) from error

    if not is_non_negative_number(subtotal):
        raise ValueError("The requested amount is too large.")

    if subtotal > discount_threshold:
        discount = round(subtotal * discount_rate, 2)
    else:
        discount = 0

    taxable_amount = round(subtotal - discount, 2)
    tax = round(taxable_amount * tax_rate, 2)
    total = round(taxable_amount + tax, 2)

    if not is_non_negative_number(total):
        raise ValueError("The requested amount is too large.")

    return {
        "subtotal": subtotal,
        "discount": discount,
        "tax": tax,
        "total": total,
    }


def filter_in_stock(inventory):
    """Return products with stock greater than zero."""
    return dict(
        filter(
            lambda pair: pair[1]["stock"] > 0,
            inventory.items(),
        )
    )


def sort_by_price(inventory):
    """Return products ordered from lowest to highest price."""
    return dict(
        sorted(
            inventory.items(),
            key=lambda pair: pair[1]["price"],
        )
    )


def run_checks():
    """Test the module using fresh sample inventory."""
    inventory = {
        "101": {"name": "Notebook", "price": 200, "stock": 5},
        "102": {"name": "Pen", "price": 100, "stock": 0},
        "103": {"name": "Calculator", "price": 2000, "stock": 3},
    }

    # Check stock availability.
    assert is_stock_available(inventory, "101", 5)
    assert not is_stock_available(inventory, "101", 6)
    assert not is_stock_available(inventory, "999", 1)

    # Reject invalid purchase quantities.
    for quantity in (0, -1, 1.5, True, "2"):
        assert not is_stock_available(
            inventory, "101", quantity
        )

    # Check deductions and restocking.
    assert update_item_stock(inventory, "101", -2)
    assert inventory["101"]["stock"] == 3

    assert update_item_stock(inventory, "101", 2)
    assert inventory["101"]["stock"] == 5

    # Invalid adjustments must leave stock unchanged.
    for change in (-6, 1.5, True, "2"):
        assert not update_item_stock(
            inventory, "101", change
        )
        assert inventory["101"]["stock"] == 5

    assert not update_item_stock(inventory, "999", 1)

    # Check the price quote for two calculators.
    quote = get_price_quote(inventory, "103", 2)

    assert quote == {
        "subtotal": 4000,
        "discount": 400,
        "tax": 0,
        "total": 3600,
    }

    # Exactly ₦2,000 does not qualify for the discount.
    assert get_price_quote(
        inventory, "103", 1
    )["discount"] == 0

    # Check tax after the discount.
    assert get_price_quote(
        inventory, "103", 2, tax_rate=0.075
    )["total"] == 3870

    assert get_price_quote(inventory, "999", 1) is None

    # Reject invalid pricing inputs.
    invalid_options = [
        {"qty": 0},
        {"qty": -1},
        {"qty": 1.5},
        {"qty": True},
        {"tax_rate": -0.1},
        {"tax_rate": 1.1},
        {"discount_rate": True},
        {"discount_rate": float("nan")},
        {"discount_threshold": -1},
        {"discount_threshold": "2000"},
    ]

    for options in invalid_options:
        arguments = {"qty": 1, **options}

        try:
            get_price_quote(
                inventory, "103", **arguments
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                f"Invalid pricing input accepted: {options}"
            )

    # Check filtering and sorting.
    assert list(filter_in_stock(inventory)) == [
        "101", "103"
    ]
    assert list(sort_by_price(inventory)) == [
        "102", "101", "103"
    ]

    print("All inventory checks passed.")
    show_inventory(inventory)
    print("Quote for 2 calculators:", quote)


if __name__ == "__main__":
    run_checks()