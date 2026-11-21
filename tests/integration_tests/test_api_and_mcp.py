import json
from collections.abc import Iterator
from datetime import date

import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel

from main import app
from src.adapters.driving.mcp_server import build_mcp_server
from src.container import Container, set_container
from tests.factories import build_container


@pytest.fixture
def container() -> Container:
    built = build_container()
    set_container(built)
    return built


@pytest.fixture
def client(container: Container) -> Iterator[TestClient]:
    assert container is not None
    yield TestClient(app)


class TestHttpApi:
    def test_full_cooking_flow(self, client: TestClient) -> None:
        # Given
        client.post("/api/stock", json={"name": "pâtes", "quantity": 500, "unit": "g"})
        created = client.post(
            "/api/recipes",
            json={
                "title": "Pâtes au beurre",
                "prep_minutes": 15,
                "ingredients": [{"name": "pâtes", "quantity": 400, "unit": "g"}],
                "steps": ["Cuire."],
                "cooks": ["Alex"],
            },
        ).json()

        # When
        suggestions = client.get("/api/suggestions", params={"member": "Alex", "quick": "true"}).json()
        cooked = client.post(f"/api/recipes/{created['id']}/cook", json={"member": "Alex"})
        stock = client.get("/api/stock").json()
        week = client.get("/api/cook-logs/week").json()

        # Then
        assert created["is_quick"] is True
        assert suggestions[0]["recipe"]["id"] == created["id"]
        assert cooked.status_code == 201
        assert stock[0]["quantity"] == 100
        assert [log["recipe_title"] for log in week] == ["Pâtes au beurre"]

    def test_preferences_toggle_per_member(self, client: TestClient) -> None:
        # Given
        recipe = client.post(
            "/api/recipes",
            json={"title": "Causa", "prep_minutes": 60, "ingredients": [], "steps": ["Monter."]},
        ).json()

        # When
        updated = client.put(f"/api/recipes/{recipe['id']}/preferences", json={"member": "sam", "likes": True})
        mine = client.get("/api/recipes", params={"member": "Sam"}).json()

        # Then
        assert updated.json()["fans"] == ["Sam"]
        assert [current["title"] for current in mine] == ["Causa"]

    def test_running_low_flag_feeds_shopping_context(self, client: TestClient) -> None:
        # Given
        salt = client.post("/api/stock", json={"name": "sel", "kind": "basique"}).json()

        # When
        client.put(f"/api/stock/{salt['id']}/running-low", json={"running_low": True})
        context = client.get("/api/shopping/context").json()

        # Then
        assert [item["name"] for item in context["to_buy_drive"]] == ["sel"]

    def test_domain_errors_are_mapped_to_http_status(self, client: TestClient) -> None:
        # Given
        client.post("/api/stock", json={"name": "riz"})

        # When
        duplicate = client.post("/api/stock", json={"name": "Riz"})
        unknown_member = client.get("/api/recipes", params={"member": "Personne"})

        # Then
        assert duplicate.status_code == 409
        assert unknown_member.status_code == 400

    def test_draft_generation(self, client: TestClient) -> None:
        # Given
        client.post("/api/stock", json={"name": "courgettes", "quantity": 3, "unit": "piece"})

        # When
        response = client.post("/api/recipes/drafts", json={"request": "un gratin", "member": "Alex"})

        # Then
        assert response.status_code == 200
        assert response.json()["ingredients"][0]["name"] == "courgettes"


class TestMcpServer:
    async def test_tools_cover_the_shopping_workflow(self, container: Container) -> None:
        # Given
        server = build_mcp_server(lambda: container)
        await server.call_tool(
            "update_stock_item",
            {"name": "papier toilette", "running_low": True},
        )

        # When
        tools = {tool.name for tool in await server.list_tools()}
        context_result = await server.call_tool("get_shopping_context", {})
        await server.call_tool(
            "record_shopping_trip",
            {
                "store": "Auchan Drive",
                "items": [
                    {
                        "product_name": "Papier toilette 12 rouleaux",
                        "stock_name": "papier toilette",
                        "kind": "maison",
                        "unit_price": 4.65,
                    },
                ],
            },
        )
        after = await container.shopping_service.context(date.today())  # noqa: DTZ011

        # Then
        assert {"get_shopping_context", "list_available_ingredients", "add_recipe", "record_shopping_trip"} <= tools
        assert "papier toilette" in json.dumps(_as_json(context_result), ensure_ascii=False)
        assert after.to_buy_drive == []
        assert after.preferred_products[0].product_name == "Papier toilette 12 rouleaux"


def _as_json(result: object) -> object:
    if isinstance(result, BaseModel):
        return result.model_dump(mode="json")
    return str(result)
