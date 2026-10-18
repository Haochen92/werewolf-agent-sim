"""Level 7 of the deduction engine (slice 12): possible explanations of a claim (catalogue F8, §0
grade 3) and the budgets the public counts across nights (F9).

- branches.py (F8): a claim that agrees with the record only on some branches gets one line with
  every branch, the claim being false always one; a claim with none left is false. In the seat block,
  in the claimant's entry (claims change with every message). It replaces Table E's conditional forms
  of the same claims (E4a, E8a, and E8b's with a branch left): one proposition, said once.
- budgets.py (F9): a budget the mornings fix exactly and that is used up (the Fortune Teller's
  self-bets, the Illusionist's conceals). From the public record alone, so in the public block.
"""

from __future__ import annotations

from Agents.deduction.explanations.budgets import budget_items

__all__ = ["budget_items"]
