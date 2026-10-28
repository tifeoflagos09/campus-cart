"""Simulated payment methods. No real money is collected."""

from abc import ABC, abstractmethod
from math import isfinite
from uuid import uuid4


def validate_amount(amount, allow_zero=False):
    """Validate and round an amount expressed in naira."""
    if type(amount) not in (int, float):
        raise ValueError("Amount must be a finite number.")

    try:
        valid = isfinite(amount) and amount >= 0
    except OverflowError:
        valid = False

    if not valid:
        raise ValueError(
            "Amount must be a finite, non-negative number."
        )

    amount = round(amount, 2)

    if not allow_zero and amount <= 0:
        raise ValueError(
            "Payment amount must be greater than zero."
        )

    return amount


def payment_result(status, method, amount, message):
    """Give each payment method the same result structure."""
    return {
        "status": status,
        "method": method,
        "amount": amount,
        "message": message,
        "reference": uuid4().hex if status == "SUCCESS" else None,
        "simulated": True,
    }


class PaymentMethod(ABC):
    """Require each payment method to implement a common operation."""

    @abstractmethod
    def process_payment(self, amount):
        """Return a payment result dictionary."""
        pass


class CashPayment(PaymentMethod):
    """Compare cash tendered with the bill and calculate change."""

    def __init__(self, amount_tendered):
        self._amount_tendered = validate_amount(
            amount_tendered, allow_zero=True
        )

    def process_payment(self, amount):
        amount = validate_amount(amount)

        if self._amount_tendered < amount:
            return payment_result(
                "DECLINED",
                "Cash",
                amount,
                "Cash tendered is insufficient.",
            )

        result = payment_result(
            "SUCCESS",
            "Cash",
            amount,
            "Simulated cash payment completed.",
        )

        result["amount_tendered"] = self._amount_tendered
        result["change"] = round(
            self._amount_tendered - amount, 2
        )

        return result


class CardPayment(PaymentMethod):
    """Simulate card approval or decline without card details."""

    def __init__(self, approved=True):
        if type(approved) is not bool:
            raise ValueError("Approval must be True or False.")

        self._approved = approved

    def process_payment(self, amount):
        amount = validate_amount(amount)

        if not self._approved:
            return payment_result(
                "DECLINED",
                "Card",
                amount,
                "Simulated card payment declined.",
            )

        return payment_result(
            "SUCCESS",
            "Card",
            amount,
            "Simulated card payment completed.",
        )


class MobileMoneyPayment(PaymentMethod):
    """Simulate mobile money approval or decline."""

    def __init__(self, approved=True):
        if type(approved) is not bool:
            raise ValueError("Approval must be True or False.")

        self._approved = approved

    def process_payment(self, amount):
        amount = validate_amount(amount)

        if not self._approved:
            return payment_result(
                "DECLINED",
                "Mobile money",
                amount,
                "Simulated mobile money payment declined.",
            )

        return payment_result(
            "SUCCESS",
            "Mobile money",
            amount,
            "Simulated mobile money payment completed.",
        )