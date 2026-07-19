class InsufficientChangeError(Exception):
    pass


def compute_change_breakdown(
    balance_amount: float, available_denominations: dict[int, int]
) -> dict[int, int]:
    remaining = round(balance_amount)
    if remaining < 0:
        raise ValueError("Balance amount cannot be negative")

    breakdown: dict[int, int] = {}
    for value in sorted(available_denominations.keys(), reverse=True):
        if remaining <= 0:
            break
        if value <= 0:
            continue
        available = available_denominations[value]
        if available <= 0:
            continue
        needed = remaining // value
        used = min(needed, available)
        if used > 0:
            breakdown[value] = used
            remaining -= used * value

    if remaining > 0:
        raise InsufficientChangeError(
            f"Shop does not have enough denominations to give exact change. "
            f"Rs. {remaining} of the balance could not be covered."
        )

    return breakdown
