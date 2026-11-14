"""What other modules may use from families. Routers and deps.py of other modules take
`FamilyDep` from `jumbaq.families.deps`."""

from jumbaq.families.events import FamilyCreated

__all__ = ["FamilyCreated"]
