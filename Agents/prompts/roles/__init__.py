"""The role cards: one module per role of the pool, each holding its ``CARD`` (a RoleCard with the
public rules and the private words of every turn), and ``pack``, the words every wolf shares.
``card(role)`` is the loader the composers use."""

from importlib import import_module

from Agents.schemas.role_card import RoleCard


def card(role: str) -> RoleCard:
    """The card of a role."""
    return import_module(f"Agents.prompts.roles.{role}").CARD


__all__ = ["card"]
