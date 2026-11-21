from pathlib import Path

from src.use_cases.seed_database import SeedData


def _read(path: Path) -> SeedData:
    if not path.is_file():
        return SeedData()
    return SeedData.model_validate_json(path.read_text(encoding="utf-8"))


def load_seed_data(paths: list[Path]) -> SeedData:
    data = SeedData()
    for path in paths:
        data = data.merged_with(_read(path))
    return data
