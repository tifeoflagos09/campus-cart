"""Generate receipts from saved orders, independently of the live cart."""


def stream_receipt_lines(order):
    """Yield receipt lines without printing or changing the order."""
    yield "=" * 44
    yield "              CAMPUSCART RECEIPT"
    yield "=" * 44
    yield f"Order: {order['order_id']}"
    yield f"Date (UTC): {order['timestamp']}"
    yield "-" * 44

    for entry in order["items"]:
        yield entry["name"]
        yield (
            f"  {entry['quantity']} x ₦{entry['unit_price']:,.2f}"
            f" = ₦{entry['subtotal']:,.2f}"
        )

    yield "-" * 44
    yield f"Subtotal:       ₦{order['subtotal']:,.2f}"
    yield f"Discount (10%): ₦{order['discount']:,.2f}"
    yield f"TOTAL:          ₦{order['total']:,.2f}"
    yield f"Payment: {order['payment']['method']}"
    yield f"Reference: {order['payment']['reference']}"

    if "change" in order["payment"]:
        yield (
            f"Cash received:  "
            f"₦{order['payment']['amount_tendered']:,.2f}"
        )
        yield f"Change:         ₦{order['payment']['change']:,.2f}"

    yield "Demo transaction: no real payment collected."
    yield "=" * 44
    yield "Thank you for using CampusCart!"