"""CampusCart web interface for the Campus Essentials demo store."""

import streamlit as st

from catalog import create_catalog
from models.item import PerishableItem
from models.payment import (
    CashPayment,
    CardPayment,
    MobileMoneyPayment,
)
from models.shopping_cart import ShoppingCart


st.set_page_config(
    page_title="CampusCart | Campus Essentials",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)


def initialise_session():
    if "catalog" not in st.session_state:
        st.session_state.catalog = create_catalog()

    if "cart" not in st.session_state:
        st.session_state.cart = ShoppingCart()

    if "audit_log" not in st.session_state:
        st.session_state.audit_log = []

    if "orders" not in st.session_state:
        st.session_state.orders = []


def notify(message):
    st.session_state.notice = message
    st.rerun()


def bounded_quantity(label, key, maximum):
    if (
        maximum is not None
        and st.session_state.get(key, 1) > maximum
    ):
        st.session_state[key] = 1

    return st.number_input(
        label,
        min_value=1,
        max_value=maximum,
        value=1,
        step=1,
        key=key,
    )


def show_product(item, cart):
    selected = sum(
        entry["quantity"]
        for entry in cart.items
        if entry["item"].item_id == item.item_id
    )

    remaining = (
        None
        if item.stock is None
        else max(0, item.stock - selected)
    )

    with st.container(border=True):
        st.caption(item.category.upper())
        st.subheader(item.name)
        st.markdown(f"### ₦{item.price:,.2f}")

        if isinstance(item, PerishableItem):
            st.caption(
                f"Expiry date: {item.expiry_date:%d %b %Y}"
            )

        if item.is_expired:
            st.error("Expired — unavailable")
            return

        if remaining == 0:
            if item.stock:
                st.info("All remaining units are in your cart.")
            else:
                st.info("Out of stock")
            return

        if remaining is None:
            st.caption(
                "Digital product · Unlimited availability"
            )
        else:
            st.caption(
                f"{remaining} available to add · "
                f"{selected} in your cart"
            )

            if item.stock <= 5:
                st.warning(f"Low stock: {item.stock} left")

        quantity = bounded_quantity(
            "Quantity",
            f"qty_{item.item_id}",
            remaining,
        )

        if st.button(
            "Add to cart",
            key=f"add_{item.item_id}",
            width="stretch",
        ):
            try:
                cart.add_item(item, quantity)
            except ValueError as error:
                st.error(str(error))
            else:
                notify(f"Added {quantity} × {item.name}.")


def show_cart(cart):
    with st.sidebar:
        st.title("Your cart")

        if cart.is_empty:
            st.info("Choose a product to start your order.")
            return

        for entry in cart.items:
            item = entry["item"]
            quantity = entry["quantity"]

            st.markdown(f"**{item.name}**")
            st.write(
                f"{quantity} × ₦{item.price:,.2f} = "
                f"₦{quantity * item.price:,.2f}"
            )

            remove_quantity = bounded_quantity(
                "Quantity to remove",
                f"remove_qty_{item.item_id}",
                quantity,
            )

            if st.button(
                "Remove",
                key=f"remove_{item.item_id}",
            ):
                cart.remove_item(
                    item.item_id, remove_quantity
                )
                notify(
                    f"Removed {remove_quantity} × {item.name}."
                )

            st.divider()

        totals = cart.calculate_totals()

        st.write(f"Subtotal: ₦{totals['subtotal']:,.2f}")
        st.write(f"Discount: −₦{totals['discount']:,.2f}")
        st.metric("Total", f"₦{totals['total']:,.2f}")
        st.caption("10% off orders above ₦2,000.")

        valid = True

        try:
            cart.validate_items()
        except ValueError as error:
            valid = False
            st.warning(str(error))

        method = st.selectbox(
            "Payment method",
            ["Cash", "Card", "Mobile money"],
        )

        if method == "Cash":
            cash = st.number_input(
                "Cash tendered (₦)",
                min_value=0.0,
                value=float(totals["total"]),
                step=100.0,
                key="cash_tendered",
            )
            payment = CashPayment(cash)

        elif method == "Card":
            payment = CardPayment()

        else:
            payment = MobileMoneyPayment()

        st.caption(
            "Demonstration only. No real payment is collected."
        )

        if st.button(
            "Complete checkout",
            type="primary",
            disabled=not valid,
            width="stretch",
        ):
            try:
                result = cart.checkout(
                    payment,
                    audit_log=st.session_state.audit_log,
                )

            except ValueError as error:
                st.error(str(error))

            else:
                if result["status"] == "SUCCESS":
                    st.session_state.orders.append(result)
                    notify(
                        "Checkout complete. "
                        "Your receipt is available below."
                    )
                else:
                    st.error(result["message"])

        if st.button("Clear cart", width="stretch"):
            cart.clear()
            notify("Your cart has been cleared.")


def show_receipts():
    st.divider()
    st.subheader("Your receipts")

    orders = st.session_state.orders

    if not orders:
        st.caption(
            "Completed orders will appear here "
            "during this session."
        )
        return

    selected = st.selectbox(
        "Completed order",
        list(reversed(range(len(orders)))),
        format_func=lambda index: (
            f"{orders[index]['order']['order_id']} · "
            f"₦{orders[index]['order']['total']:,.2f}"
        ),
    )

    result = orders[selected]

    st.code(result["receipt"], language=None)

    st.download_button(
        "Download receipt",
        data=result["receipt"],
        file_name=(
            f"CampusCart-{result['order']['order_id']}.txt"
        ),
        mime="text/plain",
    )


def main():
    initialise_session()

    cart = st.session_state.cart
    catalog = st.session_state.catalog

    st.caption("CAMPUSCART · YOUR CAMPUS, YOUR ESSENTIALS")
    st.title("Campus Essentials")
    st.write(
        "Study supplies, campus merchandise "
        "and everyday extras in one place."
    )

    if "notice" in st.session_state:
        st.success(st.session_state.pop("notice"))

    metrics = st.columns(3)

    metrics[0].metric("Products", len(catalog))
    metrics[1].metric(
        "Items in cart",
        sum(entry["quantity"] for entry in cart.items),
    )
    metrics[2].metric(
        "Completed orders",
        len(st.session_state.orders),
    )

    filters = st.columns([2, 2, 1])

    search = filters[0].text_input(
        "Search products",
        placeholder="Try notebook or mouse",
    ).strip().lower()

    category = filters[1].selectbox(
        "Category",
        ["All categories"]
        + sorted({item.category for item in catalog}),
    )

    sort = filters[2].selectbox(
        "Sort by",
        [
            "Featured",
            "Price: low to high",
            "Price: high to low",
        ],
    )

    products = [
        item
        for item in catalog
        if (
            category == "All categories"
            or item.category == category
        )
        and (
            not search
            or search in item.name.lower()
        )
    ]

    if sort != "Featured":
        products = sorted(
            products,
            key=lambda item: item.price,
            reverse=sort == "Price: high to low",
        )

    show_cart(cart)

    if not products:
        st.info("No products match your search.")

    columns = st.columns(3)

    for index, item in enumerate(products):
        with columns[index % 3]:
            show_product(item, cart)

    show_receipts()

    with st.expander("Session transaction summary"):
        logs = st.session_state.audit_log

        successful = sum(
            entry["status"] == "SUCCESS"
            for entry in logs
        )

        st.write(
            f"Checkout attempts: {len(logs)} · "
            f"Successful: {successful} · "
            f"Other outcomes: {len(logs) - successful}"
        )

        if logs:
            st.dataframe(
                logs,
                hide_index=True,
                width="stretch",
            )

    st.caption(
        "Demo store · Sample prices · Cart, stock and receipts "
        "are held for this browser session."
    )


if __name__ == "__main__":
    main()