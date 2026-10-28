"""Tests for the simulated polymorphic payment methods."""

import unittest

from models.payment import (
    PaymentMethod,
    CashPayment,
    CardPayment,
    MobileMoneyPayment,
)


class PaymentTests(unittest.TestCase):

    def test_base_class_cannot_be_instantiated(self):
        with self.assertRaises(TypeError):
            PaymentMethod()

    def test_cash_payment_and_change(self):
        result = CashPayment(8000).process_payment(7200)

        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(result["amount"], 7200)
        self.assertEqual(result["amount_tendered"], 8000)
        self.assertEqual(result["change"], 800)

        exact = CashPayment(7200).process_payment(7200)
        self.assertEqual(exact["change"], 0)

    def test_insufficient_cash_is_declined(self):
        for cash in (0, 1000):
            result = CashPayment(cash).process_payment(7200)

            self.assertEqual(result["status"], "DECLINED")
            self.assertIsNone(result["reference"])

    def test_invalid_cash_tendered(self):
        invalid_cash = (
            -1,
            True,
            "8000",
            None,
            float("inf"),
            float("nan"),
        )

        for cash in invalid_cash:
            with self.subTest(cash=cash):
                with self.assertRaises(ValueError):
                    CashPayment(cash)

    def test_invalid_payment_amounts(self):
        payments = [
            CashPayment(8000),
            CardPayment(),
            MobileMoneyPayment(),
        ]

        invalid_amounts = (
            0,
            -1,
            True,
            "100",
            None,
            0.001,
            float("inf"),
            float("nan"),
            10 ** 1000,
        )

        for payment in payments:
            for amount in invalid_amounts:
                with self.subTest(
                    method=type(payment).__name__,
                    amount=amount,
                ):
                    with self.assertRaises(ValueError):
                        payment.process_payment(amount)

    def test_electronic_payment_success(self):
        payments = (
            (CardPayment(), "Card"),
            (MobileMoneyPayment(), "Mobile money"),
        )

        for payment, name in payments:
            result = payment.process_payment(7200)

            self.assertEqual(result["status"], "SUCCESS")
            self.assertEqual(result["method"], name)
            self.assertEqual(result["amount"], 7200)
            self.assertTrue(result["simulated"])
            self.assertTrue(result["reference"])

    def test_electronic_payment_decline(self):
        payments = (
            CardPayment(False),
            MobileMoneyPayment(False),
        )

        for payment in payments:
            result = payment.process_payment(7200)

            self.assertEqual(result["status"], "DECLINED")
            self.assertIsNone(result["reference"])

    def test_invalid_approval_flags(self):
        for payment_class in (CardPayment, MobileMoneyPayment):
            for approved in ("False", 0, 1, None):
                with self.assertRaises(ValueError):
                    payment_class(approved)

    def test_common_interface_and_unique_references(self):
        references = []

        payments = (
            CashPayment(8000),
            CardPayment(),
            MobileMoneyPayment(),
        )

        for payment in payments:
            self.assertIsInstance(payment, PaymentMethod)

            result = payment.process_payment(7200)

            self.assertEqual(result["status"], "SUCCESS")
            self.assertEqual(result["amount"], 7200)

            references.append(result["reference"])

        self.assertEqual(len(set(references)), 3)


if __name__ == "__main__":
    unittest.main()