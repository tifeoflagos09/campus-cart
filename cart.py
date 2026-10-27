"""
CampusCart cart module.

Handles cart selections, item removal, subtotal calculations,
and receipt generation.

Inventory stock is deducted during checkout, not when adding items.
"""

from inventory import is_stock_available


def add_to_cart(cart, inventory, item_id, quantity):
    """Add an item while checking the total quantity already selected."""
    if item_id not in inventory:
        raise ValueError("Product ID not found.")

    if type(quantity) is not int or quantity <= 0:
        raise ValueError("Quantity must be a whole number greater than zero.")

    quantity_in_cart = sum(
        entry["qty"] for entry in cart if entry["id"] == item_id
    )
    combined_quantity = quantity_in_cart + quantity

    if not is_stock_available(inventory, item_id, combined_quantity):
        remaining = inventory[item_id]["stock"] - quantity_in_cart
        raise ValueError(
            f"Not enough stock. You can add {max(0, remaining)} more."
        )

    unit_price = inventory[item_id]["price"]

    for entry in cart:
        if entry["id"] == item_id:
            entry["qty"] = combined_quantity
            entry["subtotal"] = round(unit_price * combined_quantity, 2)
            return True

    cart.append({
        "id": item_id,
        "qty": quantity,
        "subtotal": round(unit_price * quantity, 2),
    })
    return True


def remove_from_cart(cart, inventory, item_id, quantity):
    """Remove some or all selected units without changing inventory stock."""
    if type(quantity) is not int or quantity <= 0:
        raise ValueError("Quantity must be a whole number greater than zero.")

    if item_id not in inventory:
        raise ValueError("Product ID not found.")

    for entry in cart:
        if entry["id"] == item_id:
            if quantity > entry["qty"]:
                raise ValueError(
                    f"You only have {entry['qty']} units in your cart."
                )

            if quantity == entry["qty"]:
                cart.remove(entry)
            else:
                entry["qty"] -= quantity
                entry["subtotal"] = round(
                    inventory[item_id]["price"] * entry["qty"], 2
                )

            return True

    raise ValueError("This product is not in your cart.")


def calculate_subtotal(cart):
    """Return the sum of all cart line subtotals."""
    return round(sum(entry["subtotal"] for entry in cart), 2)


def calculate_totals(cart):
    """Apply the existing 10% discount to orders above ₦2,000."""
    subtotal = calculate_subtotal(cart)
    discount = round(subtotal * 0.10, 2) if subtotal > 2000 else 0

    return {
        "subtotal": subtotal,
        "discount": discount,
        "total": round(subtotal - discount, 2),
    }


def stream_receipt_lines(cart, inventory):
    """Yield receipt lines one at a time instead of printing them."""
    if not cart:
        yield "Your cart is empty."
        return

    totals = calculate_totals(cart)

    yield "=" * 44
    yield "              CAMPUSCART RECEIPT"
    yield "=" * 44

    for entry in cart:
        product = inventory[entry["id"]]
        yield product["name"]
        yield (
            f"  {entry['qty']} x ₦{product['price']:,.2f}"
            f" = ₦{entry['subtotal']:,.2f}"
        )

    yield "-" * 44
    yield f"Subtotal:       ₦{totals['subtotal']:,.2f}"
    yield f"Discount (10%): ₦{totals['discount']:,.2f}"
    yield f"TOTAL:          ₦{totals['total']:,.2f}"
    yield "=" * 44
    yield "Thank you for using CampusCart!"


def run_checks():
    """Check this module independently using fresh sample data."""
    inventory = {
        "101": {"name": "Notebook", "price": 200, "stock": 5},
        "103": {"name": "Calculator", "price": 2000, "stock": 3},
    }
    cart = []

    # Repeated additions combine into one cart entry.
    add_to_cart(cart, inventory, "101", 2)
    add_to_cart(cart, inventory, "101", 3)
    assert cart[0]["qty"] == 5
    assert len(cart) == 1

    # Adding to the cart must not deduct inventory stock.
    assert inventory["101"]["stock"] == 5

    # Reject invalid quantities, unknown products, and excess stock.
    invalid_requests = [
        ("101", 0),
        ("101", -1),
        ("101", 1.5),
        ("101", True),
        ("999", 1),
        ("101", 1),
    ]

    for item_id, quantity in invalid_requests:
        try:
            add_to_cart(cart, inventory, item_id, quantity)
        except ValueError:
            pass
        else:
            raise AssertionError(
                f"Invalid request accepted: {item_id}, {quantity}"
            )

    add_to_cart(cart, inventory, "103", 2)
    totals = calculate_totals(cart)

    assert totals["subtotal"] == 5000
    assert totals["discount"] == 500
    assert totals["total"] == 4500

    # Exactly ₦2,000 does not qualify for the discount.
    assert calculate_totals([{"subtotal": 2000}])["discount"] == 0

    # Check partial and full removal using a separate cart.
    removal_cart = []
    add_to_cart(removal_cart, inventory, "101", 3)

    remove_from_cart(removal_cart, inventory, "101", 1)
    assert removal_cart[0]["qty"] == 2
    assert calculate_subtotal(removal_cart) == 400

    # Reject invalid removal quantities.
    for quantity in (0, -1, 1.5, True, 4):
        try:
            remove_from_cart(removal_cart, inventory, "101", quantity)
        except ValueError:
            pass
        else:
            raise AssertionError(
                f"Invalid removal quantity accepted: {quantity}"
            )

    # Failed removals must leave the cart unchanged.
    assert removal_cart[0]["qty"] == 2

    remove_from_cart(removal_cart, inventory, "101", 2)
    assert removal_cart == []
    assert inventory["101"]["stock"] == 5

    print("All cart checks passed.\n")

    for line in stream_receipt_lines(cart, inventory):
        print(line)


if __name__ == "__main__":
    run_checks()