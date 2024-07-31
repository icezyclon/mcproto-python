from __future__ import annotations

import atexit
import logging

import grpc

from ._base import HasStub
from ._proto import MinecraftStub
from ._proto import minecraft_pb2 as pb
from .entity import _EntityCache
from .events import _EventHandler
from .exception import raise_on_error
from .player import _PlayerCache
from .world import _DefaultWorld, _WorldHub

__all__ = ["Minecraft"]

logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)
# logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.DEBUG)


class Minecraft(_DefaultWorld, _EventHandler, _PlayerCache, _EntityCache, _WorldHub, HasStub):
    """:class:`Minecraft` is the main object of interacting with Minecraft servers that have the mcpb-plugin_.
    When constructing the class, a ``host`` and ``port`` of the server should be provided to which a connection will be built. They default to ``"localhost"`` and ``1789`` respectively.
    All other worlds, events, entities and more are then received via the methods of that instance.

    .. _mcpb-plugin: https://github.com/icezyclon/mcproto

    >>> from mcpb import Minecraft
    >>> mc = Minecraft()  # connect to localhost
    >>> mc.postToChat("Hello Minecraft")  # send  message in chat

    .. note::

       Generally, it is sufficient to construct one :class:`Minecraft` instance per server or active connection.
       However, it is generally possible to connect with multiple instances from the same or different hosts as the connection.

    .. warning::

       The connection used by the server is not encrypted or otherwise secured, meaning that any man-in-the-middle can read and modify any information sent between the program and the Minecraft server.
       For security reasons it is recommended to connect from the same host as the server. By default, the plugin does only allow connections from ``localhost``.

    :return: New :class:`Minecraft` instance connected to ``host`` and ``port``
    :rtype: Minecraft
    """

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
