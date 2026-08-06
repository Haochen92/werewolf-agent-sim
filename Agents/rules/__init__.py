"""Pure game-rule arithmetic, shared across the engine and (soon) the wire translator.

Leaf modules only — nothing here may import from nodes/state/graphs, which is what lets
every layer (nodes, memory, server) import the rulebook without cycles.

board_clocks.py — faction win-clocks + alive-role census from PUBLIC board facts
resolution.py  — night attack precedence + day-vote plurality classification
"""
