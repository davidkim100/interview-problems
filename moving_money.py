"""
At Stripe we keep track of where the money is and move money between bank accounts to make sure their balances are not below some threshold. 
This is for operational and regulatory reasons, e.g. we should have enough funds to pay out to our users, and we are legally required to separate our users' funds from our own. 
This interview question is a simplified version of a real-world problem we have here.
Let's say there are at most 500 bank accounts, some of their balances are above 100 and some are below. 
How do you move money between them so that they all have at least 100?
Just to be clear we are not looking for the optimal solution, but a working one.
Example input:

     AU: 80
     US: 140
     MX: 110
     SG: 120
     FR: 70

Output:

from: US, to: AU, amount: 20
from: US, to: FR, amount: 20
from: MX, to: FR, amount: 10
Potential follow ups/parts (in no specific order):
(Practical) If this code will be used to move millions of dollars in production, how would you change it? 
Specifically, we just eyeballed that our end goal of each balance >= 100 is met, 
how would you check that in reality? What should we do if the check fails?
(Algorithmic) Do it in the minimum number of moves. For the input data in the original prompt:

from: US, to: FR, amount: 30
from: SG, to: AU, amount: 20
"""

"""
at most 500 bank accounts
some balances are above 100 some below.
Move money between them so that they all have at least 100

Assumptions: There is always enough money for all bank accounts to have at least 100?

     AU: 80
     US: 140
     MX: 110
     SG: 120
     FR: 70

70, 80, 110, 120, 140

70 110 -> min(30,10)
"""


def move_money(accounts, min_balance=100):

     accounts.sort()
     while accounts[0][0] < min_balance:
          low_account = accounts[0][0]
          high_account = accounts[-1][0]

          low_account_diff = min_balance-low_account
          high_account_diff = high_account-min_balance

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
          raise ValueError("not enough total funds for every account to reach min_balance")

     # Work on a copy sorted ascending by balance so we never touch the input.
     ordered = sorted(accounts)
     moves = []

     low, high = 0, len(ordered) - 1
     while low < high:
          low_balance, low_name = ordered[low]
          high_balance, high_name = ordered[high]

          if low_balance >= min_balance:
               break  # everyone at/above low is already funded

          need = min_balance - low_balance        # amount low still needs
          surplus = high_balance - min_balance     # amount high can give
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


if __name__=="__main__":
     accounts=[[80,"AU"],[140,"US"],[110,"MX"],[120,"SG"],[70,"FR"]]
     new_accounts = move_money(accounts,100)

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

     # Optimized version: prints the actual moves and verifies the invariant.
     accounts2 = [[80,"AU"],[140,"US"],[110,"MX"],[120,"SG"],[70,"FR"]]
     moves, balances = move_money_optimized(accounts2, 100)
     for frm, to, amount in moves:
          print(f"from: {frm}, to: {to}, amount: {amount}")
     assert all(balance >= 100 for balance, _ in balances)
     assert sum(b for b, _ in balances) == sum(b for b, _ in accounts2)
     print("optimized success")