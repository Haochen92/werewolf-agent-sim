"""Root conftest = plugin manifest only (the dota2pred pattern): fixtures live in
tests/fixtures/, one module per resource; hand-written data builders (plain functions,
imported not registered) live in tests/factories/builders.py."""

pytest_plugins = [
    "tests.fixtures.stream",
    "tests.fixtures.server",
    "tests.factories.events",
]
