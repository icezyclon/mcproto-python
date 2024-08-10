from __future__ import annotations

from functools import partial

from . import entity
from ._base import _EntityProvider, _HasStub
from ._proto import MinecraftStub
from ._proto import minecraft_pb2 as pb
from ._types import CARDINAL, COLOR, DIRECTION
from ._util import ThreadSafeSingeltonCache
from .exception import raise_on_error
from .vec3 import Vec3

MAX_BLOCKS = 50000  # TODO: replace with block stream


class _DefaultWorld(_HasStub, _EntityProvider):
    @property
    def pvp(self) -> bool:
        # TODO: returning if ANY world has pvp
        response = self._stub.accessWorlds(pb.WorldRequest())
        raise_on_error(response.status)
        return any(world.info.pvp for world in response.worlds)

    @pvp.setter
    def pvp(self, value: bool) -> None:
        # TODO: setting ALL world pvp variables
        response = self._stub.accessWorlds(pb.WorldRequest())
        raise_on_error(response.status)
        response = self._stub.accessWorlds(
            pb.WorldRequest(
                worlds=[
                    pb.World(name=world.name, info=pb.WorldInfo(pvp=value))
                    for world in response.worlds
                ]
            )
        )
        raise_on_error(response.status)

    @property
    def _pb_world(self) -> pb.World | None:
        return None

    def getHighestPos(self, x: int, z: int) -> Vec3:
        response = self._stub.getHeight(pb.HeightRequest(world=self._pb_world, x=x, z=z))
        raise_on_error(response.status)
        pos = Vec3(response.block.pos.x, response.block.pos.y, response.block.pos.z)
        return pos

    def getHeight(self, x: int, z: int) -> int:
        return self.getHighestPos(x, z).y  # type: ignore

    def getBlock(self, pos: Vec3) -> str:
        response = self._stub.getBlock(
            pb.BlockRequest(world=self._pb_world, pos=pb.Vec3(**pos.floor().asdict()))
        )
        raise_on_error(response.status)
        return response.info.blockType

    # TODO: differentiate between block type and Block
    # def getBlockWithData(self, pos: Vec3) -> Block:
    #     raise NotImplementedError

    def getBlockList(self, positions: list[Vec3]) -> list[str]:
        # TODO: natively support this operation
        return [self.getBlock(pos) for pos in positions]

    def setBlock(self, blocktype: str, pos: Vec3) -> None:
        response = self._stub.setBlock(
            pb.Block(
                world=self._pb_world,
                info=pb.BlockInfo(blockType=blocktype),
                pos=pb.Vec3(**pos.floor().asdict()),
            )
        )
        raise_on_error(response)

    def setBlockList(self, blocktype: str, positions: list[Vec3]) -> None:
        for chunk in (
            positions[index : index + MAX_BLOCKS] for index in range(0, len(positions), MAX_BLOCKS)
        ):
            response = self._stub.setBlocks(
                pb.Blocks(
                    world=self._pb_world,
                    info=pb.BlockInfo(blockType=blocktype),
                    pos=[pb.Vec3(**pos.floor().asdict()) for pos in chunk],
                )
            )
            raise_on_error(response)

    def setBlockCube(self, blocktype: str, pos1: Vec3, pos2: Vec3) -> None:
        response = self._stub.setBlockCube(
            pb.Blocks(
                world=self._pb_world,
                info=pb.BlockInfo(blockType=blocktype),
                pos=[
                    pb.Vec3(**pos1.floor().asdict()),
                    pb.Vec3(**pos2.floor().asdict()),
                ],
            )
        )
        raise_on_error(response)

    def __getitem__(
        self,
        pos: tuple[int, int, int] | Vec3,
    ) -> str:
        """Allowed access:
        world[1,2,3] == world[Vec3(1,2,3)] == world[(1,2,3)] for single block access"""
        if isinstance(pos, Vec3):
            return self.getBlock(pos)
        elif isinstance(pos, tuple):
            if len(pos) == 3:
                if all(isinstance(el, int) for el in pos):
                    return self.getBlock(Vec3(*pos))
                # TODO: think about getitem and setitem and possible options again
                else:
                    raise TypeError("Expected tuple with int types")
            else:
                raise TypeError("Expected tuple 3 elements")
        else:
            x, y, z = pos  # attempt to unpack
            return self.getBlock(Vec3(x, y, z))
            # raise TypeError("Expected tuple or Vec3 for block access")

    def __setitem__(
        self,
        pos: tuple[int | slice, int | slice, int | slice] | Vec3,
        blocktype: str,
    ) -> None:
        """Allowed access:
        world[1,2,3] == world[Vec3(1,2,3)] == world[(1,2,3)] for single block access
        world[1:4, 2, 0:10:2] == world[1:4, 2:3, 0:10:2] for slice access]"""
        if not isinstance(blocktype, str):
            raise TypeError(f"Expected to set blocktype str, got {type(blocktype)} instead")

        if isinstance(pos, Vec3):
            return self.setBlock(blocktype, pos)
        elif isinstance(pos, tuple):
            if len(pos) == 3:
                if all(isinstance(el, int) for el in pos):
                    return self.setBlock(blocktype, Vec3(*pos))
                elif all(isinstance(el, (int, slice)) for el in pos):
                    spos = [el if isinstance(el, slice) else slice(el, el + 1) for el in pos]
                    if any(s.start is None or s.stop is None for s in spos):
                        raise ValueError("Open slices are forbidden")
                    for el in spos:
                        el.indices(0)  # only to raise Errors such as float or zero checks
                    positions = [
                        Vec3(x, y, z)
                        for x in range(spos[0].start, spos[0].stop, spos[0].step or 1)
                        for y in range(spos[1].start, spos[1].stop, spos[1].step or 1)
                        for z in range(spos[2].start, spos[2].stop, spos[2].step or 1)
                    ]  # TODO: make setBlockList to take Iterable instead of list
                    return self.setBlockList(blocktype, positions)
                else:
                    raise TypeError("Expected tuple with int or slice types")
            # TODO: think about setitem and getitem and possible options again
            else:
                raise TypeError("Expected a tuple 3 elements")
        else:
            x, y, z = pos  # attempt to unpack
            return self.setBlock(blocktype, Vec3(x, y, z))

    def _fetch_entities(
        self, include_non_spawnable: bool, with_locations: bool, entity_type: str
    ) -> list[entity.Entity]:
        request = pb.EntityRequest(
            worldwide=pb.EntityRequest.WorldEntities(
                world=self._pb_world,
                type=entity_type,
                includeNotSpawnable=include_non_spawnable,
            ),
            withLocations=with_locations,
        )
        response = self._stub.getEntities(request)
        raise_on_error(response.status)
        entities = []
        for e in response.entities:
            if include_non_spawnable and e.type == "player":
                # TODO: players are also included in getEntities(includeNotSpawnable=True) call
                continue
            nativeE = self._get_or_create_entity(e.id)
            if with_locations:
                nativeE._inject_update(e)
            else:
                # update only type
                nativeE._type = e.type
            entities.append(nativeE)
        return entities

    def spawnEntity(self, type: str, pos: Vec3) -> entity.Entity:
        response = self._stub.spawnEntity(
            pb.Entity(
                type=type,
                location=pb.EntityLocation(world=self._pb_world, pos=pb.Vec3f(**pos.asdict())),
            )
        )
        raise_on_error(response.status)
        entity = self._get_or_create_entity(response.entity.id)
        entity._type = response.entity.type
        return entity

    def getEntities(
        self, type: str | None = None, only_spawnable: bool = True
    ) -> list[entity.Entity]:
        return self._fetch_entities(not only_spawnable, False, type if type else "")

    def getEntitiesAround(
        self,
        pos: Vec3,
        distance: float,
        type: str | None = None,
        only_spawnable: bool = True,
    ) -> list[entity.Entity]:
        entities = self._fetch_entities(not only_spawnable, True, type if type else "")
        return [e for e in entities if pos.distance(e.pos) <= distance]

    def removeEntities(self, type: str | None = None) -> None:
        # TODO: support natively
        if type is None:
            self.runCommand("tp @e[type=!player] 0 -50000 0")
            self.runCommand("kill @e[type=!player]")
        elif isinstance(type, str):
            self.runCommand(f"tp @e[type={type}] 0 -50000 0")
            self.runCommand(f"kill @e[type={type}]")
        else:
            raise TypeError("Type should be of type str")

    def copyBlockCube(self, pos1: Vec3, pos2: Vec3) -> list[list[list[str]]]:
        # pos2 inclusive
        pos1, pos2 = pos1.map_pairwise(min, pos2), pos1.map_pairwise(max, pos2)
        pos1, pos2 = pos1.floor(), pos2.floor()
        return [
            [
                [self.getBlock(Vec3(x, y, z)) for z in range(pos1.z, pos2.z + 1)]
                for y in range(pos1.y, pos2.y + 1)
            ]
            for x in range(pos1.x, pos2.x + 1)
        ]

    def pasteBlockCube(
        self,
        blocktypes: list[list[list[str]]],
        pos: Vec3,
        rotation: DIRECTION = "east",
        flip_x: bool = False,
        flip_y: bool = False,
        flip_z: bool = False,
    ) -> None:
        pos = pos.floor()
        xlen, ylen, zlen = len(blocktypes), len(blocktypes[0]), len(blocktypes[0][0])
        xstride, ystride, zstride = ylen * zlen, zlen, 1
        blocks = [blocktype for xslice in blocktypes for yline in xslice for blocktype in yline]
        if rotation == "east":
            pass  # noting to do
        elif rotation == "south":
            # np.rot90(c, k=1, axes=(0,2)) == np.flip(c, axis=2).T
            zstride = -zstride
            xlen, xstride, zlen, zstride = zlen, zstride, xlen, xstride
        elif rotation == "west":
            xstride = -xstride
            zstride = -zstride
        elif rotation == "north":
            # np.rot90(c, k=3, axes=(0,2)) == np.flip(c.T, axis=2)
            xlen, xstride, zlen, zstride = zlen, zstride, xlen, xstride
            zstride = -zstride
        elif rotation == "up":
            ystride = -ystride
            xlen, xstride, ylen, ystride = ylen, ystride, xlen, xstride
        elif rotation == "down":
            xlen, xstride, ylen, ystride = ylen, ystride, xlen, xstride
            ystride = -ystride
        else:
            raise ValueError(f"Rotation should be a direction, was '{rotation}'")
        if flip_x:
            xstride = -xstride
        if flip_y:
            ystride = -ystride
        if flip_z:
            zstride = -zstride
        xrange = range(xlen) if xstride >= 0 else range(xlen - 1, -1, -1)
        yrange = range(ylen) if ystride >= 0 else range(ylen - 1, -1, -1)
        zrange = range(zlen) if zstride >= 0 else range(zlen - 1, -1, -1)
        for xindex, x in enumerate(xrange):
            for yindex, y in enumerate(yrange):
                for zindex, z in enumerate(zrange):
                    index = x * abs(xstride) + y * abs(ystride) + z * abs(zstride)
                    assert (
                        0 <= index < len(blocks)
                    ), f"{x=} {y=}, {z=} {xstride=} {ystride=} {zstride=} {index=} len={len(blocks)}"
                    self.setBlock(
                        blocks[index],
                        Vec3(pos.x + xindex, pos.y + yindex, pos.z + zindex),
                    )

    def placeBed(self, pos: Vec3, direction: CARDINAL = "east", color: COLOR = "red") -> None:
        pos = pos.floor()
        pos2 = getattr(pos, direction)(1)
        self.runCommand(
            f"setblock {pos.x} {pos.y} {pos.z} {color}_bed[part=foot,facing={direction}]"
        )
        self.runCommand(
            f"setblock {pos2.x} {pos2.y} {pos2.z} {color}_bed[part=head,facing={direction}]"
        )

    def spawnItems(self, pos: Vec3, type: str, amount: int = 1) -> None:
        pos = pos.floor()
        self.runCommand(
            f'summon item {pos.x} {pos.y} {pos.z} {{Item:{{id:"{type}", Count:{amount}}}}}'
        )


class World(_DefaultWorld, _HasStub, _EntityProvider):
    def __init__(
        self, stub: MinecraftStub, entity_provider: _EntityProvider, key: str, name: str
    ) -> None:
        super().__init__(stub)
        self._entity_provider = entity_provider
        self._key = key
        self._name = name

    def _get_or_create_entity(self, entity_id: str):
        return self._entity_provider._get_or_create_entity(entity_id)

    @property
    def _pb_world(self) -> pb.World:
        return pb.World(name=self.name)

    @property
    def key(self) -> str:
        return self._key

    @property
    def name(self) -> str:
        return self._name

    @property
    def pvp(self) -> bool:
        response = self._stub.accessWorlds(pb.WorldRequest(worlds=[self._pb_world]))
        raise_on_error(response.status)
        return response.worlds[0].info.pvp

    @pvp.setter
    def pvp(self, value: bool) -> None:
        response = self._stub.accessWorlds(
            pb.WorldRequest(worlds=[pb.World(name=self.name, info=pb.WorldInfo(pvp=value))])
        )
        raise_on_error(response.status)

    def __repr__(self) -> str:
        # return f"{self.__class__.__name__}(name={self.name}, key={self.key})"
        return f"{self.__class__.__name__}(key={self.key})"

    def runCommand(self, command: str) -> None:
        """Run the `command` as if it was typed in chat as ``/``-command and executed in this specific world/dimension..

        .. code-block:: python

           world.runCommand("kill @e")  # kill all loaded entities in this world

        :param command: the command without the slash ``/``
        :type command: str
        """
        command = f"execute in {self.key} run " + command
        return super().runCommand(command)


class _WorldHub(_HasStub, _EntityProvider):
    """All functions regarding getting World objects and interacting with different worlds.

    .. note::

       What is called :class:`World` here is referred to as a dimension in game.

    """

    def __init__(self, stub: MinecraftStub) -> None:
        super().__init__(stub)
        self._world_by_name_cache = ThreadSafeSingeltonCache(None)

    @property
    def worlds(self) -> tuple[World, ...]:
        """Give a tuple of all worlds loaded on the server.
        Does not automatically call :func:`refreshWorlds`.

        :return: A tuple of all worlds loaded on the server
        :rtype: tuple[World, ...]
        """
        if not self._world_by_name_cache:
            self.refreshWorlds()
        return tuple(self._world_by_name_cache.values())

    @property
    def overworld(self) -> World:
        """Identical to :func:`getWorldByKey` with key ``"minecraft:overworld"``.

        :return: The overworld world :class:`World` object
        :rtype: World
        """
        return self.getWorldByKey("minecraft:overworld")

    @property
    def nether(self) -> World:
        """Identical to :func:`getWorldByKey` with key ``"minecraft:the_nether"``.

        :return: The nether world :class:`World` object
        :rtype: World
        """
        return self.getWorldByKey("minecraft:the_nether")

    @property
    def end(self) -> World:
        """Identical to :func:`getWorldByKey` with key ``"minecraft:the_end"``.

        :return: The end world :class:`World` object
        :rtype: World
        """
        return self.getWorldByKey("minecraft:the_end")

    def getWorldByKey(self, key: str) -> World:
        """The `key` of a world is the dimensions internal name/id.
        Typically a regular server has the following worlds/keys:

        - ``"minecraft:overworld"``

        - ``"minecraft:the_nether"``

        - ``"minecraft:the_end"``

        The ``"minecraft:"`` prefix may be omitted, e.g., ``"the_nether"``.

        If the given `key` does not exist an exception is raised.

        :param key: Internal name/id of the world, such as ``"minecraft:the_nether"`` or ``"the_nether"``
        :type key: str
        :return: The corresponding :class:`World` object
        :rtype: World
        """
        parts = key.split(":", maxsplit=1)
        if len(parts) == 1:
            key = "minecraft:" + key
        for world in self.worlds:
            if world.key == key:
                return world
        raise_on_error(pb.Status(code=pb.WORLD_NOT_FOUND, extra="key=" + key))

    def getWorldByName(self, name: str) -> World:
        """The `name` of a world is the folder or namespace the world resides in.
        The setting for the world the server opens is found in ``server.properties``.
        A typical, unmodified PaperMC_ server will save the worlds in the following folders:

        .. _PaperMC: https://papermc.io/

        - ``"world"``, for the overworld

        - ``"world_the_nether"``, for the nether

        - ``"world_the_end"``, for the end

        The name of the overworld (default ``world``) is used as the prefix for the other folders.

        If the given `name` does not exist an exception is raised.

        :param name: Foldername the world is saved in, such as ``world``
        :type name: str
        :return: The corresponding :class:`World` object
        :rtype: World
        """
        if not self._world_by_name_cache:
            self.refreshWorlds()
        world = self._world_by_name_cache.get(name)
        if world is None:
            raise_on_error(pb.Status(code=pb.WORLD_NOT_FOUND, extra="name=" + name))
        return world

    def refreshWorlds(self) -> None:
        """Fetches the currently loaded worlds from server and updates the world objects.
        This should only be called if the loaded worlds on the server change, for example, with the Multiverse Core Plugin.
        By default, the worlds will be refreshed on first use only.
        """
        response = self._stub.accessWorlds(pb.WorldRequest())
        raise_on_error(response.status)
        for world in response.worlds:
            factory = partial(World, self._stub, self, world.info.key)
            self._world_by_name_cache.get_or_create(world.name, factory)
