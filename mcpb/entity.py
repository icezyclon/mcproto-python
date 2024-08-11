from __future__ import annotations

import time
from functools import partial

from ._base import _EntityProvider, _HasStub
from ._proto import MinecraftStub
from ._proto import minecraft_pb2 as pb
from ._types import COLOR
from ._util import ThreadSafeSingeltonCache
from .colors import color_codes
from .exception import raise_on_error
from .nbt import NBT
from .vec3 import Vec3
from .world import World, _WorldHub

__all__ = ["Entity"]

CACHE_ENTITY_TIME = 0.2
ALLOW_UNLOADED_ENTITY_OPS = True


class Entity(_HasStub):
    """The :class:`Entity` class represents an entity on the server.
    It can be used to query information about the entity or manipulate them, such as
    getting or setting their position, orientation, world and more.

    Do not instantiate the :class:`Entity` class directly but use one of the following methods instead:

    .. code-block:: python

       # world can be `mc` for default world or a specific world, like `mc.nether`
       entities = world.getEntities()  # get all entities in world
       entities = world.getEntities("pig")  # get all pigs in world
       entities = world.getEntities("arrow", only_spawnable=False)  # get all arrows in world, which are not spawnable, therefore the second argument
       entities = world.getEntitiesAround(Vec3(0, 0, 0), 20)  # get all entities in world in 20 block radius around origin
       mycreeper = world.spawnEntity("creeper", Vec3(0, 0, 0))  # spawn a creeper at origin and get it as entity

    Once you have your entitiy you can use it in a multitude of ways:

    .. code-block:: python

       # location / movement
       entity.pos  # get the current position of entity
       entity.pos = Vec3(0, 0, 0)  # teleport entity to origin
       entity.world  # get current world the entity is in
       entity.world = mc.end  # teleport entity into end
       entity.facing  # get direction entity is currently looking at as directional vector
       entity.facing = Vec3().east()  # make entity face straight east
       # use teleport if you want to set position, facing direction and/or world at once:
       entity.teleport(pos=Vec3(0, 0, 0), world=mc.end)  # teleport entity into origin in the end

       # other modifiers
       entity.kill()  # kill entity
       entity.giveEffect("glowing", 5)  # give entity glowing for 5 seconds
       entity.runCommand("data merge entity @s {NoAI:1b}")  # run command as entity and disable its ai, @s refers to itself
       ...

    .. note::

       Whether or not exceptions from operations on *unloaded or dead* entities are ignored is controlled by the global variable ``mcpb.entity.ALLOW_UNLOADED_ENTITY_OPS``, which is True by default.
       Entities can get unloaded or die at any time and checking with :attr:`loaded` before every operation will still not guarantee that the entity exists by the time the operation is received by the server.
       To make life easier all EntityNotFound exceptions will be cought and ignored if ``mcpb.entity.ALLOW_UNLOADED_ENTITY_OPS`` is True.
       Note that this will make it look like the operation succeeded, even if the entity was (already) unloaded or offline.

    .. note::

       The number of times the entity data will be updated is controlled by the global variable ``mcpb.entity.CACHE_ENTITY_TIME``, which is 0.2 by default.
       This means, using an entities's position will initially query the position from the server but then use this position for 0.2 seconds before updating the position again (as long as the position is not set in the mean time). The same holds true for all other properties of the entity.
       This improves performance but may also cause bugs or problems if the interval in which the up-to-date position is requred is lower than ``mcpb.entity.CACHE_ENTITY_TIME``.
    """

    def __init__(self, stub: MinecraftStub, worldhub: _WorldHub, entity_id: str) -> None:
        super().__init__(stub)
        self._worldhub = worldhub
        self._id = entity_id
        self._type: str | None = None  # inject type from outside
        self._update_ts: float = 0.0
        self._world: World = None
        self._pos: Vec3 = Vec3()
        self._pitch: float = 0.0
        self._yaw: float = 0.0
        self._loaded: bool = False

    @property
    def id(self) -> str:
        "The unique id of the entity on the server"
        return self._id

    @property
    def type(self) -> str:
        """The entity type, such as ``"sheep"`` or ``"creeper"``"""
        if self._type is not None:
            # entity types rarely update (e.g., villager to zombie), so do not update here
            return self._type
        # entity type should be injected directly after creation
        raise NotImplementedError

    @property
    def loaded(self) -> bool:
        """Whether or not the entity exists, i.e., is loaded and not dead.

        .. note::

           This does not give any guarantees as the entity could be killed or unloaded after the check with the server was made.
        """
        self._update_on_check(allow_dead=True)
        # note: loaded being True does not give any guarantees
        return self._loaded

    @property
    def pos(self) -> Vec3:
        """Get the position as :class:`Vec3` the entity is at.
        When assigned to is equivalent to ``self.teleport(pos=pos)``"""
        self._update_on_check()
        return self._pos

    @pos.setter
    def pos(self, pos: Vec3) -> None:
        self.teleport(pos=pos)

    @property
    def facing(self) -> Vec3:
        """Get the directional :class:`Vec3` unit-vector the entity is facing in.
        When assigned to is equivalent to ``self.teleport(facing=facing)``
        """
        self._update_on_check()
        return Vec3.from_yaw_pitch(self._yaw, self._pitch)

    @facing.setter
    def facing(self, facing: Vec3) -> None:
        self.teleport(facing=facing)

    @property
    def world(self) -> World:
        """Get the world/dimension as :class:`World` the entity is in.
        When assigned to is equivalent to ``self.teleport(world=world)`` and can also be used with the `key` of the world instead of the world object.
        """
        self._update_on_check()
        if self._world is None:
            # TODO: return _DefaultWorld? Does this case even happen?
            return self._worldhub.worlds[0]
        return self._world

    @world.setter
    def world(self, world: World | str) -> None:
        self.teleport(world=world)

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

    def _set_entity_loc(self, entity_loc: pb.EntityLocation) -> None:
        response = self._stub.setEntity(
            pb.Entity(
                id=self.id,
                location=entity_loc,
            )
        )
        if not ALLOW_UNLOADED_ENTITY_OPS or response.code != pb.ENTITY_NOT_FOUND:
            raise_on_error(response)

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

    def _update_on_check(self, allow_dead: bool = ALLOW_UNLOADED_ENTITY_OPS) -> bool:
        if self._should_update():
            self._update(allow_dead=allow_dead)

    def getEntitiesAround(
        self, distance: float, type: str | None = None, only_spawnable: bool = True
    ) -> list[Entity]:
        """Get all other entities in a certain radius around `self`

        :param distance: the radius around `self` in which to get other entities
        :type distance: float
        :param type: the type of entitiy to get, get all types if None, defaults to None
        :type type: str | None, optional
        :param only_spawnable: if True get only entities that can spawn, otherwise also get things like projectiles and drops, defaults to True
        :type only_spawnable: bool, optional
        :return: list of filtered entities with distance from `self` less or equal to `distance`
        :rtype: list[Entity]
        """
        entities = self.world.getEntitiesAround(self.pos, distance, type, only_spawnable)
        return [e for e in entities if e is not self]

    def giveEffect(
        self, effect: str, seconds: int = 30, amplifier: int = 0, particles: bool = True
    ) -> None:
        """Give `self` a (potion) effect

        :param effect: the name of the effect, e.g., ``"glowing"``
        :type effect: str
        :param seconds: the number of seconds the effect should persist, defaults to 30
        :type seconds: int, optional
        :param amplifier: the strength of the effect, `amplifier` + 1 is the level of the effect, defaults to 0
        :type amplifier: int, optional
        :param particles: whether or not to show particles for the effect, defaults to True
        :type particles: bool, optional
        """
        pbool = str(not bool(particles)).lower()
        self.runCommand(f"effect give @s {effect} {int(seconds)} {amplifier} {pbool}")

    def kill(self) -> None:
        "Kill this entity"
        self.runCommand("kill")

    def remove(self) -> None:
        "Remove the entity from world without dropping any drops"
        # TODO: implement natively
        self.runCommand("tp ~ -50000 ~")
        self.kill()

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

    def replaceItem(self, where: str, item: str, amount: int = 1, nbt: NBT | None = None) -> None:
        if nbt is None:
            self.runCommand(f"item replace entity @s {where} with {item} {amount}")
        else:
            self.runCommand(f"item replace entity @s {where} with {item}{nbt} {amount}")

    def runCommand(self, command: str) -> None:
        """Run the `command` as if it was typed in chat as ``/``-command by and at the location of the given entity.

        .. code-block:: python

           entity.runCommand("kill")  # kill this entity
           entity.runCommand("effect give @s glowing")  # @s refers to this entity

        :param command: the command without the slash ``/``
        :type command: str
        """
        command = f"execute as {self.id} at @s run " + command
        return super().runCommand(command)

    def teleport(
        self,
        pos: Vec3 | None = None,
        facing: Vec3 | None = None,
        world: World | str | None = None,
    ) -> None:
        """Change the entities position, facing direction and/or world by teleporting it.
        Any of the arguments not set will not be changed.
        For example, it is possible to only change the world the entity is in without changing its (relative) coordinates or facing direction and vice versa.

        .. code-block:: python

           entity.teleport(pos=Vec3(0, 0, 0))  # teleport entity to origin in same world
           entity.teleport(world=mc.end)  # teleport entity to end at same relative coordinates
           entity.teleport(facing=Vec3().east())  # make entity face straigth east without changing world or position
           entity.teleport(pos=Vec3(), facing=Vec3().east(), world=mc.end)  # teleport entity into origin at end facing east

        :param pos: New position the entity should be teleported to, or None if position should not change, defaults to None
        :type pos: Vec3 | None, optional
        :param facing: New direction (directional vector) the entity should face, or None if facing direction should not change, defaults to None
        :type facing: Vec3 | None, optional
        :param world: New world the entity should be teleported to, or None if world should not change, defaults to None
        :type world: World | str | None, optional
        """
        if pos is None and facing is None and world is None:
            return

        pos_pb = None
        orientation_pb = None
        world_pb = None

        if pos is not None:
            pos_pb = pb.Vec3f(**pos.map(float).asdict())

        if facing is not None:
            orientation = facing.yaw_pitch()
            orientation_pb = pb.EntityOrientation(yaw=orientation[0], pitch=orientation[1])

        if world is not None:
            if isinstance(world, str):
                world = self._worldhub.getWorldByKey(world)
            elif isinstance(world, World):
                newworld = self._worldhub.getWorldByName(world.name)
                if newworld is not world:
                    raise ValueError("World and entity are not from same server")
            else:
                raise TypeError("World should be of type World or str")
            world_pb = pb.World(name=world.name)

        self._set_entity_loc(
            pb.EntityLocation(
                pos=pos_pb,
                orientation=orientation_pb,
                world=world_pb,
            )
        )
        if pos is not None:
            self._pos = pos
        if facing is not None:
            self._yaw, self._pitch = orientation
        if world is not None:
            self._world = world


class _EntityCache(_WorldHub, _HasStub, _EntityProvider):
    def __init__(self, stub: MinecraftStub) -> None:
        super().__init__(stub)
        self._entity_cache = ThreadSafeSingeltonCache(
            partial(Entity, stub, self), use_weakref=True
        )

    def _get_or_create_entity(self, entity_id: str) -> Entity:
        return self._entity_cache.get_or_create(entity_id)

    def getEntityById(self, entity_id: str) -> Entity:
        """Get an entity with a certain `entity_id`, even if it is not loaded.

        Normally the `entity_id` is not known ahead of time.
        Prefer using :func:`getEntities`, :func:`getEntitiesAround` and :func:`spawnEntity`, which all return entities.

        :param entity_id: the unique entity identified
        :type entity_id: str
        :return: the corresponding entity with that id, even if not loaded
        :rtype: Entity
        """
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
