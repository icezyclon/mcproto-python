from typing import Literal, TypeAlias

__all__ = ["CARDINAL", "DIRECTION", "COLOR"]

CARDINAL: TypeAlias = Literal["east", "south", "west", "north"]
DIRECTION: TypeAlias = Literal[CARDINAL, "up", "down"]

COLOR: TypeAlias = Literal[
    "white",
    "orange",
    "magenta",
    "light_blue",
    "yellow",
    "lime",
    "pink",
    "gray",
    "light_gray",
    "cyan",
    "purple",
    "blue",
    "brown",
    "green",
    "red",
    "black",
]

EFFECTE: TypeAlias = Literal[
    "speed", 
    "slowness", 
    "haste", "mining_fatigue", 
    "strength", 
    "instant_health", 
    "instant_damage", 
    "jump_boost", 
    "nausea", 
    "regeneration", 
    "resistance", 
    "fire_resistance", 
    "water_breathing", 
    "invisibility", 
    "blindness", 
    "night_vision", 
    "hunger", 
    "weakness", 
    "poison", 
    "wither", 
    "health_boost", 
    "absorption", 
    "saturation", 
    "glowing", 
    "levitation", 
    "slow_falling", 
    "conduit_power", 
    "bad_omen", 
    "hero_of_the_village", 
    "dolphins_grace"
]
