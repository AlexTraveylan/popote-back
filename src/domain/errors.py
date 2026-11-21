from uuid import UUID


class DomainError(Exception):
    pass


class NotFoundError(DomainError):
    def __init__(self, entity: str, identifier: UUID | str) -> None:
        super().__init__(f"{entity} introuvable : {identifier}")
        self.entity = entity
        self.identifier = identifier


class UnknownMemberError(DomainError):
    def __init__(self, member: str, members: list[str]) -> None:
        super().__init__(f"{member} ne fait pas partie du foyer ({', '.join(members)})")
        self.member = member


class DuplicateStockItemError(DomainError):
    def __init__(self, name: str) -> None:
        super().__init__(f"{name} existe déjà dans le stock")
        self.name = name


class RecipeGenerationUnavailableError(DomainError):
    def __init__(self) -> None:
        super().__init__("La génération de recettes n'est pas configurée (OPENAI_API_KEY manquante)")


class RecipeGenerationError(DomainError):
    pass
