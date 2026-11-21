from src.domain.errors import UnknownMemberError


class Household:
    def __init__(self, members: list[str]) -> None:
        self._members = [member.strip() for member in members if member.strip()]

    @property
    def members(self) -> list[str]:
        return list(self._members)

    def ensure_member(self, member: str) -> str:
        for known in self._members:
            if known.lower() == member.strip().lower():
                return known
        raise UnknownMemberError(member, self._members)

    def ensure_members(self, members: list[str]) -> list[str]:
        return list(dict.fromkeys(self.ensure_member(member) for member in members))
