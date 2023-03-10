from __future__ import annotations

import atexit
import itertools as it
import logging

import grpc

from ._base import HasStub
from .entity import _EntityCache
from .events import _EventHandler
from .exception import raise_on_error
from .mcpb import MinecraftStub
from .mcpb import minecraft_pb2 as pb
from .player import _PlayerCache
from .vec3 import Vec3
from .world import _DefaultWorld, _WorldHub

__all__ = ["Minecraft"]

MAX_BLOCKS = 50000

logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)
# logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.DEBUG)

# TODO: allow also separate argument numbers
# def _flatten(l: Iterable) -> Iterable:
#     for e in l:
#         if isinstance(e, collections.abc.Iterable) and not isinstance(e, str):
#             for ee in _flatten(e):
#                 yield ee
#         else:
#             yield e

# def _vec3(v: tuple[Vec3] | tuple[int, int, int]) -> mcp.Vec3:
#     if len(v) != 1 or len(v) != 3:
#         raise TypeError("Ein Punkt sollte entweder ein Vec3 sein oder aus 3 Zahlen bestehen")
#     if isinstance(v, Vec3):
#         return mcp.Vec3(**v.asdict())
#     return mcp.Vec3(**dict(zip(("x", "y", "z"), _flatten(v), strict=True)))


class Minecraft(_DefaultWorld, _EventHandler, _PlayerCache, _EntityCache, _WorldHub, HasStub):
    def __init__(self, host: str = "localhost", port: int = 1789) -> None:
        self._addr = (host, port)
        self._channel = grpc.insecure_channel(f"{host}:{port}")
        stub = MinecraftStub(self._channel)
        super().__init__(stub)
        atexit.register(self._cleanup)

    def __repr__(self) -> str:
        host, port = self._addr
        return f"{self.__class__.__name__}({host=}, {port=})"

    def _cleanup(self) -> None:
        logging.debug("Minecraft: _cleanup: called, closing channel...")
        atexit.unregister(self._cleanup)
        _EventHandler._cleanup(self)
        self._channel.close()
        logging.debug("Minecraft: _cleanup: done")

    def __del__(self) -> None:
        logging.debug("Minecraft: __del__: called")
        self._cleanup()

    @property
    def host(self) -> str:
        return self._addr[0]

    @property
    def port(self) -> int:
        return self._addr[1]

    def postToChat(self, *args, sep: str = " ") -> None:
        response = self._stub.postToChat(pb.ChatPostRequest(message=sep.join(map(str, args))))
        raise_on_error(response)
