"""Pure game-rule arithmetic, shared across the engine and (soon) the wire translator.

Leaf modules only — nothing here may import from nodes/state/graphs, which is what lets
every layer (nodes, memory, server) import the rulebook without cycles.

board_clocks.py — faction win-clocks + alive-role census from PUBLIC board facts
closing.py     — who gets a last word before the vote (most accused, by the accusation tags)
resolution.py  — night attack precedence + day-vote plurality classification
seats.py       — seat order for any player list (never one faction before the other)
"""
