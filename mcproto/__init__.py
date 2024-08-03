from warnings import warn

from mcpb import colors, text
from mcpb.constants import *  # All Constants
from mcpb.entity import Entity
from mcpb.events import *  # All Events
from mcpb.exception import *  # All Exceptions
from mcpb.minecraft import Minecraft
from mcpb.nbt import NBT
from mcpb.player import Player
from mcpb.vec3 import Vec3
from mcpb.world import World

warn("The package was moved: the namespace 'mcproto' is deprecated. Use 'mcpb' instead")

[colors, text, Player, Entity, World]  # use

__all__ = [
    "Minecraft",
    "Vec3",
    "NBT",
]
