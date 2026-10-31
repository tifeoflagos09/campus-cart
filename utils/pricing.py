"""Shared coupon and delivery calculations for CampusCart."""

from math import isfinite


def calculate_quote(subtotal, coupon_code="", delivery_method="Pickup",
                    has_physical_items=True, coupon_used=False):
    """Return a quote; CAMPUS15 replaces the automatic 10% discount."""
    if type(subtotal) not in (int, float):
        raise ValueError("Subtotal must be a finite, non-negative number.")
    try:
        valid = isfinite(subtotal) and subtotal >= 0
    except OverflowError:
        valid = False
    if not valid:
        raise ValueError("Subtotal must be a finite, non-negative number.")
    if not isinstance(coupon_code, str):
        raise ValueError("Coupon code must be text.")
    code = coupon_code.strip().upper()
    if code not in ("", "CAMPUS15"):
        raise ValueError("Coupon not recognised. Use CAMPUS15 or leave it blank.")
    if delivery_method not in ("Pickup", "Campus delivery"):
        raise ValueError("Choose Pickup or Campus delivery.")
    if type(has_physical_items) is not bool:
        raise ValueError("Physical-product indicator must be True or False.")
    if type(coupon_used) is not bool:
        raise ValueError("Coupon usage indicator must be True or False.")

    subtotal = round(subtotal, 2)
    if code and coupon_used:
        raise ValueError("CAMPUS15 has already been used in this session.")
    if code and subtotal < 5000:
        raise ValueError("CAMPUS15 requires a subtotal of at least ₦5,000.")
    rate = 0.15 if code else (0.10 if subtotal > 2000 else 0)
    discount = round(subtotal * rate, 2)
    delivery_fee = (
        500 if subtotal > 0 and has_physical_items
        and delivery_method == "Campus delivery" else 0
    )
    total = round(subtotal - discount + delivery_fee, 2)
    if not isfinite(total):
        raise ValueError("Order total is too large to calculate.")

    return {
        "subtotal": subtotal,
        "discount": discount,
        "discount_label": "Coupon (15%)" if code else "Discount (10%)",
        "coupon_code": code,
        "delivery_method": delivery_method if has_physical_items else "No physical delivery",
        "delivery_fee": delivery_fee,
        "total": total,
    }
