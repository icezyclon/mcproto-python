from __future__ import annotations

from functools import partial
from typing import Literal

from . import entity
from ._base import HasStub, _EntityProvider
from ._types import CARDINAL, COLOR
from .exception import raise_on_error
from .mcpb import MinecraftStub
from .mcpb import minecraft_pb2 as pb
from .vec3 import Vec3

MAX_BLOCKS = 50000  # TODO: replace with block stream


class _DefaultWorld(HasStub, _EntityProvider):
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
                # TODO: think about getitem and setitem again
                # elif all(isinstance(el, (int, slice)) for el in pos):
                #     spos = [el if isinstance(el, slice) else slice(el, el + 1) for el in pos]
                #     if any(s.start is None or s.stop is None for s in spos):
                #         raise ValueError("Open slices are forbidden")
                #     for el in spos:
                #         el.indices(0)  # only to raise Errors such as float or zero checks
                #     # if all(s.step is None or s.step == 1 or s.step == -1 for s in spos):
                #     #     p1 = Vec3(*[el.start for el in spos])
                #     #     # BlockCube pos2 is INCLUSIVE
                #     #     p2 = Vec3(*[el.stop - (el.step or 1) for el in spos])
                #     #     # TODO: check if identical to code below (is prob. not, check at some point)
                #     #     return self.getBlockCube(Vec3(*p1), Vec3(*p2))
                #     # else:
                #     xit = range(spos[0].start, spos[0].stop, spos[0].step or 1)
                #     yit = range(spos[1].start, spos[1].stop, spos[1].step or 1)
                #     zit = range(spos[2].start, spos[2].stop, spos[2].step or 1)
                #     positions = [
                #         Vec3(x, y, z) for x in xit for y in yit for z in zit
                #     ]  # TODO: make getBlockList to take Iterable instead of list
                #     # -> [(1, 1, 1), (1, 1, 2), (1, 2, 1), (1, 2, 2), (2, 1, 1) ...]
                #     results = self.getBlockList(positions)
                #     blocktypes = [
                #         [
                #             [
                #                 results[z + y * len(zit) + x * len(yit) * len(zit)]
                #                 for z in range(len(zit))
                #             ]
                #             for y in range(len(yit))
                #         ]
                #         for x in range(len(xit))
                #     ]
                #     return blocktypes
                else:
                    raise TypeError("Expected tuple with int types")
            # elif len(pos) == 2:
            #     if all(isinstance(el, Vec3) for el in pos):
            #         return self.copyBlockCube(*pos)
            #     else:
            #         raise TypeError("Expected tuple with 2 elements to have two Vec3 types")
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
        world[1:4, 2, 0:10:2] == world[1:4, 2:3, 0:10:2] for slice access
        world[Vec3(1,2,3), Vec3(5,6,7)] == world[(1,2,3), (5,6,7)] for cube access.
        btw. world[Vec3(1,2,3), Vec3(5,6,7)] == world[1:6, 2:7, 3:8]"""
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
                    # if all(s.step is None or s.step == 1 or s.step == -1 for s in spos):
                    #     p1 = Vec3(*[el.start for el in spos])
                    #     # BlockCube is INCLUSIVE
                    #     p2 = Vec3(*[el.stop - (el.step or 1) for el in spos])
                    #     # TODO: check if identical with below (is not, fix at some point)
                    #     return self.setBlockCube(blocktype, Vec3(*p1), Vec3(*p2))
                    # else:
                    positions = [
                        Vec3(x, y, z)
                        for x in range(spos[0].start, spos[0].stop, spos[0].step or 1)
                        for y in range(spos[1].start, spos[1].stop, spos[1].step or 1)
                        for z in range(spos[2].start, spos[2].stop, spos[2].step or 1)
                    ]  # TODO: make setBlockList to take Iterable instead of list
                    return self.setBlockList(blocktype, positions)
                else:
                    raise TypeError("Expected tuple with int or slice types")
            # TODO: think about setitem and getitem again
            # elif len(pos) == 2:
            #     if all(isinstance(el, Vec3) for el in pos):
            #         return self.setBlockCube(blocktype, *pos)
            #     else:
            #         raise TypeError("Expected tuple with 2 elements to have two Vec3 types")
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
                world=self._pb_world, type=entity_type, includeNotSpawnable=include_non_spawnable
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
        self, pos: Vec3, distance: float, type: str | None = None, only_spawnable: bool = True
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
        sign = lambda x: 1 if x >= 0 else -1
        pos1, pos2 = pos1.floor(), pos2.floor()
        d = pos2 - pos1
        return [
            [
                [
                    self.getBlock(Vec3(x, y, z))
                    for z in range(pos1.z, pos2.z + sign(d.z), sign(d.z))
                ]
                for y in range(pos1.y, pos2.y + sign(d.y), sign(d.y))
            ]
            for x in range(pos1.x, pos2.x + sign(d.x), sign(d.x))
        ]

    def pasteBlockCube(self, blocktypes: list[list[list[str]]], pos: Vec3) -> None:
        x, y, z = pos.floor()
        for sliceindex, xi in enumerate(range(x, x + len(blocktypes))):
            for lineindex, yi in enumerate(range(y, y + len(blocktypes[0]))):
                for pointindex, zi in enumerate(range(z, z + len(blocktypes[0][0]))):
                    blocktype = blocktypes[sliceindex][lineindex][pointindex]
                    self.setBlock(blocktype, Vec3(xi, yi, zi))

    def placeBed(self, pos: Vec3, direction: CARDINAL = "east", color: COLOR = "red") -> None:
        pos = pos.floor()
        pos2 = getattr(pos, direction)(1)
        self.runCommand(
            f"setblock {pos.x} {pos.y} {pos.z} {color}_bed[part=foot,facing={direction}]"
        )
        self.runCommand(
            f"setblock {pos2.x} {pos2.y} {pos2.z} {color}_bed[part=head,facing={direction}]"
        )


class World(_DefaultWorld, HasStub, _EntityProvider):
    def __init__(
        self, stub: MinecraftStub, name: str, key: str, entity_provider: _EntityProvider
    ) -> None:
        super().__init__(stub)
        self._name = name
        self._key = key
        self._entity_provider = entity_provider

    def _get_or_create_entity(self, entity_id: str):
        return self._entity_provider._get_or_create_entity(entity_id)

    @property
    def _pb_world(self) -> pb.World:
        return pb.World(name=self.name)

    @property
    def name(self) -> str:
        return self._name

    @property
    def key(self) -> str:
        return self._key

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
        command = f"execute in {self.key} run " + command
        return super().runCommand(command)


class _WorldHub(HasStub, _EntityProvider):
    def __init__(self, stub: MinecraftStub) -> None:
        super().__init__(stub)
        self._worlds_by_name: dict[str, World] = dict()

    @property
    def worlds(self) -> tuple[World, ...]:
        if not self._worlds_by_name:
            response = self._stub.accessWorlds(pb.WorldRequest())
            raise_on_error(response.status)
            self._worlds_by_name = {
                world.name: World(self._stub, world.name, world.info.key, self)
                for world in response.worlds
            }
        return tuple(self._worlds_by_name.values())

    @property
    def overworld(self) -> World:
        for world in self.worlds:
            if world.key == "minecraft:overworld":
                # if not world.name.endswith("_nether") and not world.name.endswith("_the_end"):
                return world
        raise_on_error(pb.Status(code=pb.WORLD_NOT_FOUND))

    @property
    def nether(self) -> World:
        for world in self.worlds:
            if world.key == "minecraft:the_nether":
                # if world.name.endswith("_nether"):
                return world
        raise_on_error(pb.Status(code=pb.WORLD_NOT_FOUND))

    @property
    def end(self) -> World:
        for world in self.worlds:
            if world.key == "minecraft:the_end":
                # if world.name.endswith("_the_end"):
                return world
        raise_on_error(pb.Status(code=pb.WORLD_NOT_FOUND))

    def getWorldByName(self, name: str) -> World:
        """World name == Folder name, eg. 'world', 'world_the_nether' or 'world_the_end'"""
        if not self._worlds_by_name:
            worlds = self.worlds  # will load worlds if not loaded
        if name not in self._worlds_by_name:
            raise_on_error(pb.Status(code=pb.WORLD_NOT_FOUND, extra="name=" + name))
        return self._worlds_by_name[name]

    def getWorldByKey(self, key: str) -> World:
        """World key == Minecraft key, eg. 'the_nether' or 'minecraft:the_nether'"""
        parts = key.split(":", maxsplit=1)
        if len(parts) == 1:
            key = "minecraft:" + key
        for world in self.worlds:  # will load worlds if not loaded
            if world.key == key:
                return world
        raise_on_error(pb.Status(code=pb.WORLD_NOT_FOUND, extra="key=" + key))
