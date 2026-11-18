"""Tests that call real models over the network and cost money. Excluded from the default set by the
``-m "not contract and not slow"`` default in pyproject; run them on purpose, with the owner's
agreement, with ``poetry run pytest -m contract``.
"""
