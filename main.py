"""
CampusCart CLI.

Connects inventory, cart management, receipts,
and transaction logging.
"""

from inventory import (
    show_inventory,
    is_stock_available,
    update_item_stock,
    filter_in_stock,
    sort_by_price,
)

from cart import (
    add_to_cart,
    remove_from_cart,
    calculate_totals,
    stream_receipt_lines,
)

from logger import log_transaction, summarize_logs


def create_inventory():
    """Create fresh inventory for each application session."""
    return {
        "101": {"name": "Notebook", "price": 200, "stock": 30},
        "102": {"name": "Pen", "price": 100, "stock": 40},
        "103": {"name": "Calculator", "price": 2000, "stock": 30},
        "104": {"name": "Stapler", "price": 2500, "stock": 25},
        "105": {"name": "A4 Paper", "price": 3000, "stock": 25},
        "106": {
            "name": "Document Folder",
            "price": 150,
            "stock": 20,
        },
        "107": {"name": "Spiral Bind", "price": 300, "stock": 30},
    }


def read_product_id(inventory, prompt="Enter product ID: "):
    """Validate the product ID before asking for a quantity."""
    item_id = input(prompt).strip()

    if not item_id or not item_id.isascii() or not item_id.isdigit():
        raise ValueError(
            "Product ID must contain digits only, such as 103."
        )

    if item_id not in inventory:
        raise ValueError(
            "Product ID not found. Choose an ID from inventory."
        )

    return item_id


def read_quantity(prompt, maximum):
    """Accept positive whole numbers within the available quantity."""
    text = input(prompt).strip()

    if not text or not text.isascii() or not text.isdigit():
        raise ValueError(
            "Quantity must be a whole number greater than zero."
        )

    try:
        quantity = int(text)
    except ValueError:
        raise ValueError(
            "Enter a smaller whole-number quantity."
        ) from None

    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero.")

    if quantity > maximum:
        raise ValueError(
            f"You can select at most {maximum} units."
        )

    return quantity


def show_cart(cart, inventory):
    """Display the basket and its estimated checkout total."""
    if not cart:
        print("Your cart is empty.")
        return

    print("\nYOUR CART")
    print("-" * 44)

    for entry in cart:
        name = inventory[entry["id"]]["name"]
        print(
            f"{name} x {entry['qty']}: "
            f"₦{entry['subtotal']:,.2f}"
        )

    totals = calculate_totals(cart)

    print(f"Subtotal: ₦{totals['subtotal']:,.2f}")
    print(f"Discount: ₦{totals['discount']:,.2f}")
    print(f"Total:    ₦{totals['total']:,.2f}")


@log_transaction("CHECKOUT")
def checkout_cart(cart, inventory):
    """Validate the cart, capture a receipt, and deduct stock."""
    if not cart:
        raise ValueError(
            "Your cart is empty. Add items before checkout."
        )

    requested = {}

    for entry in cart:
        quantity = entry["qty"]

        if type(quantity) is not int or quantity <= 0:
            raise ValueError(
                "Cart quantities must be positive whole numbers."
            )

        item_id = entry["id"]
        requested[item_id] = requested.get(item_id, 0) + quantity

    # Validate every product before changing stock.
    for item_id, quantity in requested.items():
        if not is_stock_available(inventory, item_id, quantity):
            raise ValueError(
                f"Stock is unavailable for product {item_id}. "
                "Review your cart."
            )

    # Capture the receipt before clearing the cart.
    receipt = "\n".join(
        stream_receipt_lines(cart, inventory)
    )
    totals = calculate_totals(cart)

    original_stock = {
        item_id: inventory[item_id]["stock"]
        for item_id in requested
    }

    try:
        for item_id, quantity in requested.items():
            updated = update_item_stock(
                inventory, item_id, -quantity
            )

            if not updated:
                raise ValueError(
                    "Stock update failed. "
                    "Checkout was not completed."
                )

    except Exception:
        # Restore stock if an update fails.
        for item_id, stock in original_stock.items():
            inventory[item_id]["stock"] = stock
        raise

    cart.clear()

    return {
        "status": "SUCCESS",
        "receipt": receipt,
        "total": totals["total"],
    }


def show_transaction_summary(logs):
    """Display recorded checkout outcomes."""
    if not logs:
        print("No checkout attempts recorded yet.")
        return

    successful = summarize_logs(
        logs,
        lambda entry: entry["status"] == "SUCCESS",
    )

    print(f"\nCheckout attempts: {len(logs)}")
    print(f"Successful: {len(successful)}")
    print(f"Unsuccessful: {len(logs) - len(successful)}")

    for entry in logs:
        print(
            f"{entry['timestamp']} | "
            f"{entry['status']} | "
            f"{entry['details']}"
        )


def main():
    inventory = create_inventory()
    cart = []
    logs = []

    while True:
        print("\n================================")
        print("          CAMPUSCART")
        print("================================")
        print("1. View Inventory")
        print("2. Add Item to Cart")
        print("3. View Cart")
        print("4. Checkout")
        print("5. Remove Item from Cart")
        print("6. View Available Products by Price")
        print("7. View Transaction Summary")
        print("8. Exit")

        try:
            choice = input(
                "Select an option (1-8): "
            ).strip()

            if choice == "1":
                show_inventory(inventory)

            elif choice == "2":
                item_id = read_product_id(inventory)

                selected = sum(
                    entry["qty"]
                    for entry in cart
                    if entry["id"] == item_id
                )

                remaining = inventory[item_id]["stock"] - selected

                if remaining <= 0:
                    raise ValueError(
                        "No more stock is available for this product."
                    )

                quantity = read_quantity(
                    f"Enter quantity (available: {remaining}): ",
                    remaining,
                )

                add_to_cart(
                    cart, inventory, item_id, quantity
                )

                print(
                    f"Added {quantity} x "
                    f"{inventory[item_id]['name']} to cart."
                )

            elif choice == "3":
                show_cart(cart, inventory)

            elif choice == "4":
                result = checkout_cart(
                    cart,
                    inventory,
                    audit_log=logs,
                )

                print("\n" + result["receipt"])

            elif choice == "5":
                if not cart:
                    raise ValueError(
                        "Your cart is empty. "
                        "There is nothing to remove."
                    )

                item_id = read_product_id(
                    inventory,
                    "Enter product ID to remove: ",
                )

                selected = sum(
                    entry["qty"]
                    for entry in cart
                    if entry["id"] == item_id
                )

                if selected == 0:
                    raise ValueError(
                        "This product is not in your cart."
                    )

                quantity = read_quantity(
                    f"Enter quantity to remove (in cart: {selected}): ",
                    selected,
                )

                remove_from_cart(
                    cart, inventory, item_id, quantity
                )

                print(
                    f"Removed {quantity} x "
                    f"{inventory[item_id]['name']} from cart."
                )

            elif choice == "6":
                available = filter_in_stock(inventory)

                if available:
                    show_inventory(sort_by_price(available))
                else:
                    print("No products are currently in stock.")

            elif choice == "7":
                show_transaction_summary(logs)

            elif choice == "8":
                print("Goodbye!")
                break

            else:
                print(
                    "Invalid option. "
                    "Please enter a number from 1 to 8."
                )

        except ValueError as error:
            print(f"Cannot complete action: {error}")

        except (EOFError, KeyboardInterrupt):
            print("\nSession ended. Goodbye!")
            break


if __name__ == "__main__":
    main()