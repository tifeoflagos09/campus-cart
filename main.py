"""
CampusCart CLI
A command-line tool for campus vendors to manage stock,
calculate totals, and generate receipts.
"""

# Nested dictionary: {product_id: {name, price, stock}}
inventory = {
    "101": {"name": "Notebook", "price": 200, "stock": 30},
    "102": {"name": "Pen", "price": 100, "stock": 40},
    "103": {"name": "Calculator", "price": 2000, "stock": 30},
    "104": {"name": "Stapler", "price": 2500, "stock": 25},
    "105": {"name": "A4 Paper", "price": 3000, "stock": 25},
    "106": {"name": "Document Folder", "price": 150, "stock": 20},
    "107": {"name": "Spiral Bind", "price": 300, "stock": 30},
}

# Cart resets at the start of each checkout
cart = []

# Main menu loop, runs until the user exits
while True:
    print("Welcome to CampusCart")
    print("======================")
    print("1. View Stock")
    print("2. Add New Item")
    print("3. Update Stock")
    print("4. Generate Receipt")
    print("5. Exit")

    choice = input("Select an option (1-5): ")

    # View Stock: display all products currently in inventory
    if choice == "1":
        print("\nCurrent Stock:")
        for item_id, details in inventory.items():
            print(f"{item_id}: {details['name']} - ₦{details['price']} ({details['stock']} in stock)")

    # Add New Item: create a new product, blocked if the ID already exists
    elif choice == "2":
        new_id = input("Enter new product ID: ")

        if new_id in inventory:
            print("\nThis product ID already exists. Use Update Stock instead.")
        else:
            new_name = input("Enter product name: ")
            new_price = int(input("Enter product price: "))
            new_stock = int(input("Enter starting stock quantity: "))

            inventory[new_id] = {"name": new_name, "price": new_price, "stock": new_stock}
            print(f"\n{new_name} added to inventory!")

    # Update Stock: modify quantity or price for an existing product
    elif choice == "3":
        item_id = input("Enter product ID to update: ")

        if item_id in inventory:
            print("What would you like to update?")
            print("1. Stock quantity")
            print("2. Price")
            update_choice = input("Select an option (1-2): ")

            if update_choice == "1":
                add_qty = int(input("Enter quantity to add: "))
                inventory[item_id]["stock"] += add_qty
                print(f"\nStock updated! {inventory[item_id]['name']} now has {inventory[item_id]['stock']} in stock.")
            elif update_choice == "2":
                new_price = int(input("Enter new price: "))
                inventory[item_id]["price"] = new_price
                print(f"\nPrice updated! {inventory[item_id]['name']} now costs ₦{inventory[item_id]['price']}.")
            else:
                print("\nInvalid option.")
        else:
            print("\nProduct ID not found.")

    # Generate Receipt: build cart, validate stock, calculate total, apply discount
    elif choice == "4":
        cart = []
        while True:
            item_id = input("Enter product ID to buy (or type 'done' to finish): ")

            if item_id == "done":
                break

            if item_id not in inventory:
                print("Product ID not found.\n")
                continue

            qty = int(input("Enter quantity: "))

            # Track quantity already reserved this session for accurate stock checks
            already_in_cart = 0
            for entry in cart:
                if entry["id"] == item_id:
                    already_in_cart += entry["qty"]

            remaining_stock = inventory[item_id]["stock"] - already_in_cart

            if qty > remaining_stock:
                print(f"Not enough stock. Only {remaining_stock} available.\n")
                continue

            subtotal = inventory[item_id]["price"] * qty
            cart.append({"id": item_id, "qty": qty, "subtotal": subtotal})
            print(f"Added {qty} x {inventory[item_id]['name']} to cart.\n")

        if not cart:
            print("Cart is empty. Returning to menu.\n")
        else:
            total = 0
            print("\n----- Receipt -----")
            for entry in cart:
                item_name = inventory[entry["id"]]["name"]
                print(f"{item_name} x{entry['qty']} - ₦{entry['subtotal']}")
                total += entry["subtotal"]

            # 10% discount on orders over ₦2000
            if total > 2000:
                discount = total * 0.1
                total -= discount
                print(f"Discount applied: -₦{discount}")

            print(f"TOTAL: ₦{total}")
            print("--------------------")
            print("Thank you for using CampusCart!\n")

            for entry in cart:
                inventory[entry["id"]]["stock"] -= entry["qty"]

    # Exit the program
    elif choice == "5":
        print("Goodbye!")
        break

    else:
        print("You selected:", choice)