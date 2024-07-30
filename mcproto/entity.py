from __future__ import annotations

import time
from functools import partial

from ._base import HasStub, _EntityProvider
from ._types import COLOR
from ._util import ThreadSafeSingeltonCache
from .colors import color_codes
from .exception import raise_on_error
from .mcpb import MinecraftStub
from .mcpb import minecraft_pb2 as pb
from .nbt import NBT
from .vec3 import Vec3
from .world import World, _WorldHub

__all__ = ["Entity"]

CACHE_ENTITY_TIME = 0.2
ALLOW_UNLOADED_ENTITY_OPS = True


class Entity(HasStub):
    def __init__(self, stub: MinecraftStub, worldhub: _WorldHub, entity_id: str) -> None:
        super().__init__(stub)
        self._worldhub = worldhub
        self._id = entity_id
        self._type: str | None = None  # TODO: inject type from outside for now

        self._update_ts: float = 0.0
        self._world: World = None
        self._pos: Vec3 = Vec3()
        self._pitch: float = 0.0
        self._yaw: float = 0.0
        self._loaded: bool = False

    @property
    def id(self) -> str:
        return self._id

    @property
    def type(self) -> str:
        if self._type is not None:
            # TODO: should be updated as types might change (eg. villager to zombie)
            return self._type
        # TODO: lookup entity (if it exists) and its type
        raise NotImplementedError

    def __repr__(self) -> str:
        if self._type is not None:
            return f"{self.__class__.__name__}(type={self.type}, id={self.id})"
        return f"{self.__class__.__name__}(type=?, id={self.id})"

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, type(self)) and self.id == __o.id

    def __gt__(self, __o: object) -> bool:
        if not isinstance(__o, type(self)):
            raise TypeError(
                f"'>' not supported between instances of '{type(self)}' and '{type(__o)}'"
            )
        return self.id > __o.id

    def __hash__(self) -> int:
        return hash((type(self), self.id))

    def _should_update(self) -> bool:
        if time.time() - self._update_ts > CACHE_ENTITY_TIME:
            return True
        return False

    def _inject_update(self, pb_entity: pb.Entity) -> bool:
        assert pb_entity.id == self.id
        if pb_entity.type:
            self._type = pb_entity.type
        self._world = self._worldhub.getWorldByName(pb_entity.location.world.name)
        self._pos = Vec3(
            pb_entity.location.pos.x, pb_entity.location.pos.y, pb_entity.location.pos.z
        )
        self._pitch = pb_entity.location.orientation.pitch
        self._yaw = pb_entity.location.orientation.yaw
        self._update_ts = time.time()
        self._loaded = True
        return True

    def _update(self, allow_dead: bool = ALLOW_UNLOADED_ENTITY_OPS) -> bool:
        response = self._stub.getEntities(
            pb.EntityRequest(
                specific=pb.EntityRequest.SpecificEntities(entities=[pb.Entity(id=self.id)]),
                withLocations=True,
            )
        )
        # getEntities does NOT raise ENTITY_NOT_FOUND if any or all specific entities are not found
        raise_on_error(response.status)
        if len(response.entities) == 0:
            self._loaded = False
            if not allow_dead:
                raise_on_error(pb.Status(code=pb.ENTITY_NOT_FOUND, extra=self.id))
            return False
        else:
            assert len(response.entities) == 1
            e = response.entities[0]
            return self._inject_update(e)

    def runCommand(self, command: str) -> None:
        command = f"execute as {self.id} at @s run " + command
        return super().runCommand(command)

    def kill(self) -> None:
        self.runCommand("kill")

    def remove(self) -> None:
        # TODO: implement natively
        self.runCommand("tp ~ -50000 ~")
        self.kill()

    def getEntitiesAround(
        self, distance: float, type: str | None = None, only_spawnable: bool = True
    ) -> list[Entity]:
        entities = self.world.getEntitiesAround(self.pos, distance, type, only_spawnable)
        return [e for e in entities if e is not self]

    def giveEffect(
        self, effect: str, seconds: int = 30, amplifier: int = 0, particles: bool = True
    ) -> None:
        pbool = str(not bool(particles)).lower()
        self.runCommand(f"effect give @s {effect} {int(seconds)} {amplifier} {pbool}")

    def replaceItem(self, where: str, item: str, amount: int = 1, nbt: NBT | None = None) -> None:
        if nbt is None:
            self.runCommand(f"item replace entity @s {where} with {item} {amount}")
        else:
            self.runCommand(f"item replace entity @s {where} with {item}{nbt} {amount}")

    def replaceHelmet(
        self,
        armortype: str = "leather_helmet",
        unbreakable: bool = True,
        binding: bool = True,
        vanishing: bool = False,
        color: COLOR | int | None = None,
        nbt: NBT | None = None,
    ) -> None:
        nbt = nbt or NBT()
        if binding:
            nbt.add_binding_curse()
        if vanishing:
            nbt.add_vanishing_curse()
        if unbreakable:
            nbt.set_unbreakable()
        if isinstance(color, str) and color in color_codes:
            nbt.get_or_create_nbt("display")["color"] = color_codes[color]
        elif isinstance(color, int):
            nbt.get_or_create_nbt("display")["color"] = color
        self.replaceItem("armor.head", armortype, nbt=nbt)

    @property
    def facing(self) -> Vec3:
        yaw, pitch = self.orientation
        return Vec3.from_yaw_pitch(yaw, pitch)

    @facing.setter
    def facing(self, direction: Vec3) -> None:
        self.orientation = direction.yaw_pitch()

    @property
    def loaded(self) -> bool:
        if self._should_update():
            self._update(allow_dead=True)
            # TODO: loaded being True does not give any guarantees
        return self._loaded

    @property
    def pos(self) -> Vec3:
        if self._should_update():
            self._update()
        return self._pos

    @pos.setter
    def pos(self, pos: Vec3) -> None:
        response = self._stub.setEntity(
            pb.Entity(
                id=self.id,
                location=pb.EntityLocation(pos=pb.Vec3f(**pos.map(float).asdict())),
            )
        )
        if not ALLOW_UNLOADED_ENTITY_OPS or response.code != pb.ENTITY_NOT_FOUND:
            raise_on_error(response)
        self._pos = pos

    @property
    def pitch(self) -> float:
        if self._should_update():
            self._update()
        return self._pitch

    @pitch.setter
    def pitch(self, pitch: float) -> None:
        if self._should_update():
            self._update()  # due to yaw also being set
        response = self._stub.setEntity(
            pb.Entity(
                id=self.id,
                location=pb.EntityLocation(
                    orientation=pb.EntityOrientation(yaw=self._yaw, pitch=float(pitch))
                ),
            )
        )
        if not ALLOW_UNLOADED_ENTITY_OPS or response.code != pb.ENTITY_NOT_FOUND:
            raise_on_error(response)
        self._pitch = pitch

    @property
    def yaw(self) -> float:
        if self._should_update():
            self._update()
        return self._yaw

    @yaw.setter
    def yaw(self, yaw: float) -> None:
        if self._should_update():
            self._update()  # due to pitch also being set
        response = self._stub.setEntity(
            pb.Entity(
                id=self.id,
                location=pb.EntityLocation(
                    orientation=pb.EntityOrientation(yaw=float(yaw), pitch=self._pitch)
                ),
            )
        )
        if not ALLOW_UNLOADED_ENTITY_OPS or response.code != pb.ENTITY_NOT_FOUND:
            raise_on_error(response)
        self._yaw = yaw

    @property
    def orientation(self) -> tuple[float, float]:
        if self._should_update():
            self._update()
        return (self._yaw, self._pitch)

    @orientation.setter
    def orientation(self, orientation: tuple[float, float]) -> None:
        response = self._stub.setEntity(
            pb.Entity(
                id=self.id,
                location=pb.EntityLocation(
                    orientation=pb.EntityOrientation(
                        yaw=float(orientation[0]), pitch=float(orientation[1])
                    )
                ),
            ),
        )
        if not ALLOW_UNLOADED_ENTITY_OPS or response.code != pb.ENTITY_NOT_FOUND:
            raise_on_error(response)
        self._yaw, self._pitch = orientation[:2]

    @property
    def world(self) -> World:
        if self._should_update():
            self._update()
            if self._world is None:
                return self._worldhub.worlds[0]  # TODO: return _DefaultWorld?
        return self._world

    @world.setter
    def world(self, world: World | str) -> None:
        if isinstance(world, str):
            newworld = self._worldhub.getWorldByKey(world)
        elif isinstance(world, World):
            newworld = self._worldhub.getWorldByName(world.name)
            if newworld is not world:
                raise ValueError("World and player are not from same server")
        else:
            raise TypeError("World should be of type World or str")
        response = self._stub.setEntity(
            pb.Entity(
                id=self.id,
                location=pb.EntityLocation(world=pb.World(name=newworld.name)),
            ),
        )
        if not ALLOW_UNLOADED_ENTITY_OPS or response.code != pb.ENTITY_NOT_FOUND:
            raise_on_error(response)
        self._world = newworld


class _EntityCache(_WorldHub, HasStub, _EntityProvider):
    def __init__(self, stub: MinecraftStub) -> None:
        super().__init__(stub)
        self._entity_cache = ThreadSafeSingeltonCache(
            partial(Entity, stub, self), use_weakref=True
        )

    def _get_or_create_entity(self, entity_id: str) -> Entity:
        return self._entity_cache.get_or_create(entity_id)

    def getEntityById(self, entity_id: str) -> Entity:
        entity = self._get_or_create_entity(entity_id)
        entity._update()
        return entity


# if __name__ == "__main__":
#     from functools import partial

#     test_stub_1 = object()
#     test_stub_2 = object()
#     E1 = partial(Entity, test_stub_1)
#     P1 = partial(TestPlayer, test_stub_1)

#     name1 = "test_id"
#     name2 = "other_test_id"

#     e1_1 = E1(name1)
#     e2_1 = E1(name1)
#     e3_1 = E1(name2)
#     print(e1_1)
#     print(e2_1)
#     print(e3_1)
#     assert e1_1 is not e2_1
#     assert e1_1 is not e3_1
#     assert e1_1 == e2_1
#     assert e1_1 != e3_1
#     p1_1 = P1(name1)
#     print(p1_1)
#     assert p1_1 != e1_1
#     e1_1.runCommand("hi")
#     p1_1.runCommand("hi")
#     p1_1.kill()
#     p1_1.kill()
#     p1_1.only_player_cmd("test")

#     print("---")

#     from ._util import ThreadSafeCachedKeyBasedFactory

#     entity1 = ThreadSafeCachedKeyBasedFactory(partial(Entity, test_stub_1), use_weakref=True)
#     player1 = ThreadSafeCachedKeyBasedFactory(partial(TestPlayer, test_stub_1))

#     e1_1 = entity1.get_or_create(name1)
#     e2_1 = entity1.get_or_create(name2)
#     e3_1 = entity1.get_or_create(name1)
#     assert e1_1 is not e2_1
#     assert e1_1 is e3_1
#     p1_1 = player1.get_or_create(name1)
#     p2_1 = player1.get_or_create(name2)
#     p3_1 = player1.get_or_create(name1)
#     assert p1_1 is not p2_1
#     assert p1_1 is p3_1
#     assert p1_1 is not e1_1
