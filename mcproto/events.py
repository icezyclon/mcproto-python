from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from itertools import repeat
from queue import Empty, Queue, SimpleQueue
from threading import Thread

import grpc

from ._base import HasStub, _EntityProvider, _PlayerProvider
from ._types import DIRECTION
from .entity import Entity
from .mcpb import MinecraftStub
from .mcpb import minecraft_pb2 as pb
from .player import Player
from .vec3 import Vec3

__all__ = [
    "Event",
    "PlayerJoinEvent",
    "PlayerLeaveEvent",
    "PlayerDeathEvent",
    "ChatEvent",
    "BlockHitEvent",
    "ProjetileHitEvent",
]

POLL_DEFAULT: int | None = 10

# TODO: check if working correctly, kotlin queue does always seem to hold 1 (or no cap?)
MAX_QUEUE_SIZE: int = 100

# TODO: make events frozen?
# TODO: make tests for events
# also, put direction in utils?


@dataclass(order=True)  # TODO: order does not work between different Type of events?
class Event:
    timestamp: float = field(
        init=False, repr=False, compare=True, hash=False, default_factory=time.time
    )


@dataclass
class PlayerJoinEvent(Event):
    player: Player


@dataclass
class PlayerLeaveEvent(Event):
    player: Player


@dataclass
class PlayerDeathEvent(Event):
    player: Player
    deathMessage: str


@dataclass
class ChatEvent(Event):
    player: Player
    message: str


@dataclass
class BlockHitEvent(Event):
    player: Player
    right_hand: bool
    held_item: str
    pos: Vec3
    face: DIRECTION


@dataclass
class ProjetileHitEvent(Event):
    player: Player
    target: Player | Entity | str
    projectile_type: str
    pos: Vec3
    face: DIRECTION | None

    @property
    def target_player(self) -> Player | None:
        if isinstance(self.target, Player):
            # assert self.face is None
            return self.target
        return None

    @property
    def target_entity(self) -> Entity | None:
        if isinstance(self.target, Entity):
            # assert self.face is None
            return self.target
        return None

    @property
    def target_block(self) -> str | None:
        if isinstance(self.target, str):
            # assert self.face is not None
            return self.target
        return None


class _EventPoller:
    def __init__(self, key: int, stream: grpc.Future, handler: _EventHandler) -> None:
        self.key = key
        self.stream = stream
        self.handler = handler
        self.events: Queue[Event] = Queue(MAX_QUEUE_SIZE)
        self.thread = Thread(
            target=self._poll, name=f"EvenPoller-EventType-{self.key}", daemon=True
        )
        self.thread_cancelled = False
        logging.debug(f"_EventPoller: __init__: Starting thread...")
        self.thread.start()

    def _cleanup(self) -> None:
        logging.debug("EventPoller: _cleanup: cancelling stream...")
        self.thread_cancelled = True
        self.stream.cancel()
        logging.debug("EventPoller: _cleanup: joining thread...")
        self.thread.join()
        logging.debug("EventPoller: _cleanup: joined thread")

    def _poll(self) -> None:
        logging.debug(f"EventPoller: _poll: started polling")
        try:
            for rpc_event in self.stream:
                logging.debug(f"EventPoller: _poll: putting event in queue: {rpc_event}")
                self.events.put(self._parse_to_event(rpc_event), block=True, timeout=None)
                if self.thread_cancelled:
                    logging.info(f"EventPoller: _poll: stream was cancelled via variable")
                    return
        except grpc.RpcError as e:
            if hasattr(e, "code") and callable(e.code) and e.code() == grpc.StatusCode.CANCELLED:
                if self.thread_cancelled:
                    logging.info(f"EventPoller: _poll: stream was cancelled")
                else:
                    logging.error(
                        f"EventPoller: _poll: stream was cancelled, but NOT via cleanup!"
                    )
                    raise e
            else:
                logging.error(f"EventPoller: _poll: stream was closed by RpcError: {e}")
                raise e

    def _parse_to_event(self, res: pb.Event) -> Event:
        event: Event | None = None
        if res.type != self.key:
            raise ValueError(
                f"Received event type was not of type {self.key}, was {res.type} instead"
            )
        match res.type:
            case pb.EVENT_PLAYER_JOIN:
                event = PlayerJoinEvent(
                    self.handler._get_or_create_player(res.playerMsg.trigger.name)
                )
            case pb.EVENT_PLAYER_LEAVE:
                event = PlayerLeaveEvent(
                    self.handler._get_or_create_player(res.playerMsg.trigger.name)
                )
            case pb.EVENT_PLAYER_DEATH:
                event = PlayerDeathEvent(
                    self.handler._get_or_create_player(res.playerMsg.trigger.name),
                    res.playerMsg.message,
                )
            case pb.EVENT_CHAT_MESSAGE:
                event = ChatEvent(
                    self.handler._get_or_create_player(res.playerMsg.trigger.name),
                    res.playerMsg.message,
                )
            case pb.EVENT_BLOCK_HIT:
                event = BlockHitEvent(
                    self.handler._get_or_create_player(res.blockHit.trigger.name),
                    res.blockHit.right_hand,
                    res.blockHit.item_type,
                    Vec3(res.blockHit.pos.x, res.blockHit.pos.y, res.blockHit.pos.z),
                    res.blockHit.face,
                )
            case pb.EVENT_PROJECTILE_HIT:
                target = (
                    self.handler._get_or_create_player(res.projectileHit.player.name)
                    if res.projectileHit.HasField("player")
                    else (
                        self.handler._get_or_create_entity(res.projectileHit.entity.id)
                        if res.projectileHit.HasField("entity")
                        else res.projectileHit.block
                    )
                )
                if isinstance(target, Entity):
                    target._type = res.projectileHit.entity.type
                event = ProjetileHitEvent(
                    self.handler._get_or_create_player(res.projectileHit.trigger.name),
                    target,
                    res.projectileHit.projectile,
                    Vec3(
                        res.projectileHit.pos.x,
                        res.projectileHit.pos.y,
                        res.projectileHit.pos.z,
                    ),
                    res.projectileHit.face if res.projectileHit.face else None,
                )
            case _:
                logging.error(str(res))
                raise NotImplementedError(f"Event with code {res.type} is not supported yet")
        return event


class _EventHandler(HasStub, _EntityProvider, _PlayerProvider):
    def __init__(self, stub: MinecraftStub) -> None:
        super().__init__(stub)
        self._poller: dict[int, _EventPoller] = {}

    def _cleanup(self) -> None:
        logging.debug(f"EventHandler: _cleanup: called...")
        for key, poller in self._poller.items():
            logging.debug(f"EventHandler: _cleanup: calling cleanup in poller with key {key}")
            poller._cleanup()
        self._poller.clear()
        logging.debug(f"EventHandler: _cleanup: done")

    def _get_poller(self, key: int) -> _EventPoller:
        if key not in self._poller:
            logging.info(f"EventHandler: _get_poller: Starting polling for events with key {key}")
            stream = self._stub.getEventStream(pb.EventStreamRequest(eventType=key))
            self._poller[key] = _EventPoller(key, stream, self)
        return self._poller[key]

    def _poll_upto(self, key: int, max_events: int | None) -> list[Event]:
        poller = self._get_poller(key)
        events = []
        _range = repeat(None) if max_events is None else range(max_events)
        try:
            for _ in _range:
                events.append(poller.events.get_nowait())
        except Empty:
            pass
        return events

    def pollPlayerJoinEvents(self, maximum: int | None = POLL_DEFAULT) -> list[PlayerJoinEvent]:
        return self._poll_upto(pb.EVENT_PLAYER_JOIN, maximum)  # type: ignore

    # def clearPlayerJoinEvents(self) -> None:
    #     TODO: accessing poller is not thread safe, use utils cache?

    def pollPlayerLeaveEvents(self, maximum: int | None = POLL_DEFAULT) -> list[PlayerLeaveEvent]:
        return self._poll_upto(pb.EVENT_PLAYER_LEAVE, maximum)  # type: ignore

    def pollPlayerDeathEvents(self, maximum: int | None = POLL_DEFAULT) -> list[PlayerDeathEvent]:
        return self._poll_upto(pb.EVENT_PLAYER_DEATH, maximum)  # type: ignore

    def pollChatEvents(self, maximum: int | None = POLL_DEFAULT) -> list[ChatEvent]:
        return self._poll_upto(pb.EVENT_CHAT_MESSAGE, maximum)  # type: ignore

    def pollBlockHitEvents(self, maximum: int | None = POLL_DEFAULT) -> list[BlockHitEvent]:
        return self._poll_upto(pb.EVENT_BLOCK_HIT, maximum)  # type: ignore

    def pollProjectileHitEvents(
        self, maximum: int | None = POLL_DEFAULT
    ) -> list[ProjetileHitEvent]:
        return self._poll_upto(pb.EVENT_PROJECTILE_HIT, maximum)  # type: ignore
