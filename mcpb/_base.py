from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from ._proto import MinecraftStub
from ._proto import minecraft_pb2 as pb
from .exception import raise_on_error

if TYPE_CHECKING:
    from .entity import Entity
    from .player import Player


class HasStub:
    """Has a MinecraftStub and can use it for very generic things, such as running commands"""

    def __init__(self, stub: MinecraftStub) -> None:
        if not isinstance(stub, MinecraftStub):
            raise TypeError(f"Argument 'stub' must be of type MinecraftStub was '{type(stub)}'")
        self._stub = stub

    def __repr__(self) -> str:
        return (
            self.__class__.__qualname__
            + "("
            + ", ".join(
                f"{var}={val!r}" for var, val in self.__dict__.items() if not var.startswith("_")
            )
            + ")"
        )

    def runCommand(self, command: str) -> None:
        response = self._stub.runCommand(pb.CommandRequest(command=command))
        raise_on_error(response)


class _EntityProvider(ABC):
    @abstractmethod
    def _get_or_create_entity(self, entity_id: str) -> Entity:
        raise NotImplementedError


class _PlayerProvider(ABC):
    @abstractmethod
    def _get_or_create_player(self, name: str) -> Player:
        raise NotImplementedError
