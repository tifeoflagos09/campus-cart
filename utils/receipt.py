"""Generate readable receipts from saved orders."""

from datetime import datetime, timedelta, timezone


def format_receipt_date(timestamp):
    """Display the stored timestamp in West Africa Time."""
    recorded = datetime.fromisoformat(timestamp)

    if recorded.tzinfo is None:
        recorded = recorded.replace(tzinfo=timezone.utc)

    local = recorded.astimezone(
        timezone(timedelta(hours=1))
    )
    clock = local.strftime("%I:%M %p").lstrip("0")

    return f"{local:%d %b %Y}, {clock} WAT"


def stream_receipt_lines(order):
    """Yield receipt lines without changing the saved order."""
    yield "=" * 44
    yield "              CAMPUSCART RECEIPT"
    yield "=" * 44
    yield f"Order: {order['order_id']}"
    yield f"Date: {format_receipt_date(order['timestamp'])}"
    yield "-" * 44

    for entry in order["items"]:
        yield entry["name"]
        yield (
            f"  {entry['quantity']} x ₦{entry['unit_price']:,.2f}"
            f" = ₦{entry['subtotal']:,.2f}"
        )

    yield "-" * 44
    yield f"Subtotal:       ₦{order['subtotal']:,.2f}"

    label = order.get("discount_label", "Discount (10%)")
    yield f"{label}: ₦{order['discount']:,.2f}"

    if order.get("coupon_code"):
        yield f"Coupon code: {order['coupon_code']}"

    if "delivery_method" in order:
        yield f"Delivery: {order['delivery_method']}"
        yield f"Delivery fee:   ₦{order['delivery_fee']:,.2f}"

    yield f"TOTAL:          ₦{order['total']:,.2f}"

    payment_label = order["payment"]["method"]

    if order["payment"].get("simulated", False):
        payment_label += " (simulated)"

    yield f"Payment: {payment_label}"
    yield f"Reference: {order['payment']['reference']}"

    if "change" in order["payment"]:
        yield (
            f"Cash received:  "
            f"₦{order['payment']['amount_tendered']:,.2f}"
        )
        yield f"Change:         ₦{order['payment']['change']:,.2f}"

    yield "=" * 44
    yield "Thank you for using CampusCart!"