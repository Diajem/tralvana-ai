from dataclasses import dataclass

import pytest

from travelos.shared.base_repository import BaseRepository
from travelos.shared.base_service import BaseService
from travelos.shared.pagination import Pagination


@dataclass
class Entity:
    id: str
    name: str


class MemoryRepository(BaseRepository[Entity]):
    def __init__(self, entities: list[Entity] | None = None) -> None:
        self.entities = {entity.id: entity for entity in entities or []}

    def save(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity | None:
        return self.entities.get(entity_id)

    def delete(self, entity_id: str) -> bool:
        return self.entities.pop(entity_id, None) is not None

    def list_all(self) -> list[Entity]:
        return list(self.entities.values())


class ExampleService(BaseService):
    pass


def test_base_repository_is_abstract():
    with pytest.raises(TypeError):
        BaseRepository()


def test_repository_default_exists_and_pagination_contract():
    repository = MemoryRepository(
        [Entity(str(index), f"Entity {index}") for index in range(5)]
    )

    assert repository.exists("2") is True
    assert repository.exists("missing") is False

    page = repository.list_page(Pagination(limit=2, offset=2))
    assert [entity.id for entity in page.items] == ["2", "3"]
    assert page.pagination.total == 5
    assert page.pagination.limit == 2
    assert page.pagination.offset == 2


def test_repository_save_update_and_delete():
    repository = MemoryRepository()

    assert repository.save(Entity("1", "Original")).name == "Original"
    assert repository.save(Entity("1", "Updated")).name == "Updated"
    assert repository.get("1") == Entity("1", "Updated")
    assert repository.delete("1") is True
    assert repository.delete("1") is False


def test_base_service_exposes_stable_name_and_logger():
    service = ExampleService()

    assert service.service_name == "ExampleService"
    assert service.logger._name == "ExampleService"
