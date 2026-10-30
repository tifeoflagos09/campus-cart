"""Sample catalogue for Campus Essentials."""

from datetime import date, timedelta

from models.item import Item, PerishableItem, DigitalVoucher


def create_catalog():
    """Create fresh products for a new shopping session."""
    today = date.today()

    return [
        # Stationery
        Item(
            "101", "A5 Notebook", 500, 30, "Stationery"
        ),
        Item(
            "102", "Ballpoint Pen", 200, 40, "Stationery"
        ),
        Item(
            "103", "Document Folder", 300, 20, "Stationery"
        ),

        # Campus merchandise
        Item(
            "104", "Campus T-shirt", 5000, 12,
            "Campus merchandise"
        ),
        Item(
            "105", "Canvas Tote Bag", 2500, 10,
            "Campus merchandise"
        ),
        Item(
            "110", "Campus Baseball Cap", 3000, 8,
            "Campus merchandise"
        ),

        # Tech accessories
        Item(
            "106", "Wireless Mouse", 4000, 8,
            "Tech accessories"
        ),
        Item(
            "107", "Adjustable Laptop Stand", 6000, 5,
            "Tech accessories"
        ),
        Item(
            "111", "USB-C Cable", 2500, 15,
            "Tech accessories"
        ),

        # Food and drinks
        PerishableItem(
            "108",
            "Packaged Sandwich",
            1500,
            8,
            today + timedelta(days=2),
            "Food & drinks",
        ),
        PerishableItem(
            "112",
            "Bottled Water",
            300,
            24,
            today + timedelta(days=90),
            "Food & drinks",
        ),
        PerishableItem(
            "113",
            "Packaged Biscuits",
            500,
            20,
            today + timedelta(days=30),
            "Food & drinks",
        ),

        # Digital services
        DigitalVoucher(
            "109",
            "Printing Voucher",
            1000,
            "Digital services",
        ),
        DigitalVoucher(
            "114",
            "Scanning Voucher",
            500,
            "Digital services",
        ),
        DigitalVoucher(
            "115",
            "Document Formatting Voucher",
            2000,
            "Digital services",
        ),
    ]