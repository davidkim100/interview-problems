"""
Moving Money

Given a list of bank accounts with balances, move money between accounts so that all balances
are at or above a minimum threshold (at most 500 accounts).

Example:
    Input:  AU: 80, US: 140, MX: 110, SG: 120, FR: 70
    Output: from US to AU: 20, from US to FR: 20, from MX to FR: 10

Follow-ups:
    - (Practical)   In production, how would you verify transfers? What should happen if a
                    post-transfer balance check fails?
    - (Algorithmic) Minimise the number of moves.
                    Optimal: from US to FR: 30, from SG to AU: 20
"""


def move_money(accounts, min_balance=100):

    accounts.sort()
    while accounts[0][0] < min_balance:
        low_account = accounts[0][0]
        high_account = accounts[-1][0]

        low_account_diff = min_balance - low_account
        high_account_diff = high_account - min_balance

        money_transfer = min(low_account_diff, high_account_diff)

        accounts[0][0] += money_transfer
        accounts[-1][0] -= money_transfer

        accounts.sort()

    return accounts


def move_money_optimized(accounts, min_balance=100):
    """Single sort + two pointers -> O(n log n). Returns (moves, balances).

    - Records the actual transfers (from, to, amount) instead of just mutating.
    - Does not mutate the caller's input.
    - Raises if there isn't enough total money to satisfy every account.
    """
    total = sum(balance for balance, _ in accounts)
    if total < min_balance * len(accounts):
        raise ValueError(
            "not enough total funds for every account to reach min_balance"
        )

    # Work on a copy sorted ascending by balance so we never touch the input.
    ordered = sorted(accounts)
    moves = []

    low, high = 0, len(ordered) - 1
    while low < high:
        low_balance, low_name = ordered[low]
        high_balance, high_name = ordered[high]

        if low_balance >= min_balance:
            break  # everyone at/above low is already funded

        need = min_balance - low_balance  # amount low still needs
        surplus = high_balance - min_balance  # amount high can give
        amount = min(need, surplus)

        if amount > 0:
            moves.append((high_name, low_name, amount))
            ordered[low][0] += amount
            ordered[high][0] -= amount

        # Advance whichever side is now satisfied.
        if ordered[low][0] >= min_balance:
            low += 1
        if ordered[high][0] <= min_balance:
            high -= 1

    return moves, ordered


def test():
    accounts = [[80, "AU"], [140, "US"], [110, "MX"], [120, "SG"], [70, "FR"]]
    new_accounts = move_money(accounts, 100)

    money_total_prev = 0
    for account in accounts:
        money_total_prev += account[0]
    print(money_total_prev)
    money_total_new = 0
    for account in new_accounts:
        money_total_new += account[0]
    print(money_total_new)
    assert money_total_prev == money_total_new
    print("success")

    accounts2 = [[80, "AU"], [140, "US"], [110, "MX"], [120, "SG"], [70, "FR"]]
    moves, balances = move_money_optimized(accounts2, 100)
    for frm, to, amount in moves:
        print(f"from: {frm}, to: {to}, amount: {amount}")
    assert all(balance >= 100 for balance, _ in balances)
    assert sum(b for b, _ in balances) == sum(b for b, _ in accounts2)
    print("optimized success")


if __name__ == "__main__":
    test()
