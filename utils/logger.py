"""
CampusCart audit and logging module.

Records transaction outcomes and duration
without a global log list.
"""

from datetime import datetime, timezone
from functools import wraps
from time import perf_counter


def log_transaction(action_name):
    """Create a decorator that records a transaction's outcome."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, audit_log=None, **kwargs):
            if not isinstance(audit_log, list):
                raise ValueError(
                    "Pass a log list using audit_log=your_log_list."
                )

            started = perf_counter()

            entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(
                    timespec="seconds"
                ),
                "action": action_name,
                "function": func.__name__,
                "status": "SUCCESS",
                "details": "Completed successfully.",
            }

            try:
                result = func(*args, **kwargs)

                # A returned False represents an unsuccessful operation.
                if result is False:
                    entry["status"] = "FAILED"
                    entry["details"] = "The operation returned False."

                # Recognise explicit unsuccessful transaction statuses.
                elif isinstance(result, dict):
                    status = str(
                        result.get("status", "SUCCESS")
                    ).upper()

                    if status in (
                        "FAILED",
                        "FAILURE",
                        "DECLINED",
                        "CANCELLED",
                    ):
                        entry["status"] = status
                        entry["details"] = result.get(
                            "message",
                            "Transaction was not completed.",
                        )

                return result

            except Exception as error:
                entry["status"] = "FAILED"
                entry["details"] = str(error)
                raise

            finally:
                entry["duration_ms"] = round(
                    (perf_counter() - started) * 1000,
                    3,
                )
                audit_log.append(entry)

        return wrapper

    return decorator


def summarize_logs(logs, filter_func=None):
    """Return records, optionally filtered by a supplied function."""
    if filter_func is not None:
        return list(filter(filter_func, logs))

    return list(logs)


def run_checks():
    """Check success, failures, declined payments, and separate logs."""
    logs = []

    @log_transaction("TEST_CHECKOUT")
    def sample_checkout(amount):
        if amount <= 0:
            raise ValueError("Amount must be greater than zero.")

        return {
            "status": "SUCCESS",
            "amount": amount,
        }

    @log_transaction("TEST_PAYMENT")
    def sample_decline():
        return {
            "status": "DECLINED",
            "message": "Demo payment declined.",
        }

    @log_transaction("TEST_STOCK_UPDATE")
    def sample_failure():
        return False

    # Check a successful call and its return value.
    result = sample_checkout(4500, audit_log=logs)

    assert result["amount"] == 4500
    assert logs[-1]["status"] == "SUCCESS"
    assert logs[-1]["duration_ms"] >= 0
    assert sample_checkout.__name__ == "sample_checkout"

    # Check that exceptions are logged and still raised.
    try:
        sample_checkout(-1, audit_log=logs)
    except ValueError:
        pass
    else:
        raise AssertionError(
            "The invalid checkout should have failed."
        )

    assert logs[-1]["status"] == "FAILED"
    assert (
        logs[-1]["details"]
        == "Amount must be greater than zero."
    )

    # A declined payment must not be logged as successful.
    result = sample_decline(audit_log=logs)

    assert result["status"] == "DECLINED"
    assert logs[-1]["status"] == "DECLINED"

    # A returned False must not be logged as successful.
    assert sample_failure(audit_log=logs) is False
    assert logs[-1]["status"] == "FAILED"
    assert len(logs) == 4

    # Check filtering with a lambda function.
    successful = summarize_logs(
        logs,
        lambda entry: entry["status"] == "SUCCESS",
    )

    assert len(successful) == 1
    assert len(summarize_logs(logs)) == 4

    # Separate applications or sessions can use separate logs.
    other_logs = []
    sample_checkout(100, audit_log=other_logs)

    assert len(other_logs) == 1
    assert len(logs) == 4

    # Reject calls that do not supply log storage.
    try:
        sample_checkout(100)
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Missing log storage should be rejected."
        )

    print("All logger checks passed.")
    print(f"Recorded attempts: {len(logs)}")
    print(f"Successful attempts: {len(successful)}")
    print(
        "Other outcomes:",
        [entry["status"] for entry in logs[1:]],
    )


if __name__ == "__main__":
    run_checks()