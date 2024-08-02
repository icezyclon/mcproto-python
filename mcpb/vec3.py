from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from numbers import Number
from typing import Any, Callable, Iterator, Union

from ._types import CARDINAL, DIRECTION

_NumType = Union[int, float]
_NumVec = Union["Vec3", _NumType]

__all__ = ["Vec3"]


@dataclass(frozen=True, eq=True, order=True, repr=True)
class Vec3:
    """:class:`Vec3` is a 3-dimensional vector for representing ``x``, ``y`` and ``z`` coordinates.
    Each instance of this class is **frozen**, so calculations on it yield new instances of :class:`Vec3` instead of changing the x, y and z values directly.
    """

    x: float = 0
    y: float = 0
    z: float = 0

    @classmethod
    def from_yaw_pitch(cls, yaw: _NumType = 0, pitch: _NumType = 0) -> Vec3:
        """Build direction unit-vector from yaw and pitch.
        yaw: -180..179.99 (-180/180 north, -90 east, 0 south, 90 west)
        pitch -90..90 (-90 up, 0 straight, 90 down)"""
        yawed = Vec3().south().rotate(Vec3().down(), yaw)
        pitched = yawed.rotate(yawed.cross(Vec3().down()), pitch)
        return pitched  # .norm()  # already normed

    def yaw_pitch(self) -> tuple[float, float]:
        """Return the yaw and pitch value from self as directional vector.
        yaw: -180..179.99 (-180 north, -90 east, 0 south, 90 west)
        pitch -90..90 (-90 up, 0 straight, 90 down)"""
        if self.x == 0 and self.y == 0 and self.z == 0:
            return 0.0, 0.0
        yaw = -math.degrees(math.atan2(self.x, self.z))
        pitch = math.degrees(math.atan2(math.sqrt(self.z**2 + self.x**2), self.y)) - 90.0
        return yaw, pitch

    def __add__(self, v: _NumVec) -> Vec3:
        if isinstance(v, Number):
            return Vec3(self.x + v, self.y + v, self.z + v)
        if isinstance(v, Vec3):
            return Vec3(self.x + v.x, self.y + v.y, self.z + v.z)
        return NotImplemented

    def __radd__(self, v: _NumVec) -> Vec3:
        return self + v

    def __sub__(self, v: _NumVec) -> Vec3:
        if isinstance(v, Number):
            return Vec3(self.x - v, self.y - v, self.z - v)
        if isinstance(v, Vec3):
            return Vec3(self.x - v.x, self.y - v.y, self.z - v.z)
        return NotImplemented

    def __rsub__(self, v: _NumVec) -> Vec3:
        return self - v

    def __xor__(self, v: Vec3) -> float:
        if isinstance(v, Vec3):
            return self.dot(v)
        return NotImplemented

    def __matmul__(self, v: Vec3) -> Vec3:
        if isinstance(v, Vec3):
            return self.cross(v)
        return NotImplemented

    def __mul__(self, v: _NumVec) -> Vec3:
        if isinstance(v, Number):
            return Vec3(self.x * v, self.y * v, self.z * v)
        if isinstance(v, Vec3):
            return self.multiply_elementwise(v)
        return NotImplemented

    def __rmul__(self, v: _NumVec) -> Vec3:
        return self * v

    def __truediv__(self, v: _NumType) -> Vec3:
        if isinstance(v, Number):
            return Vec3(self.x / v, self.y / v, self.z / v)
        return NotImplemented

    def __floordiv__(self, v: _NumType) -> Vec3:
        if isinstance(v, Number):
            return Vec3(self.x // v, self.y // v, self.z // v)
        return NotImplemented

    def __neg__(self) -> Vec3:
        return Vec3(-self.x, -self.y, -self.z)

    def __pos__(self) -> Vec3:
        return self  # no change

    def __round__(self, ndigits: int = 0) -> Vec3:
        if ndigits == 0:
            # round returns int if no second parameter is given
            return self.map(lambda v: round(v))
        else:
            # returns float otherwise (even if ndigits = 0)
            return self.map(lambda v: round(v, ndigits))

    def __floor__(self) -> Vec3:
        return self.map(math.floor)

    def __ceil__(self) -> Vec3:
        return self.map(math.ceil)

    def __trunc__(self) -> Vec3:
        return self.map(math.trunc)

    def __copy__(self) -> Vec3:
        if type(self) == Vec3:
            return self  # immutable
        return self.__class__(self.x, self.y, self.z)

    def __deepcopy__(self, memo: Any) -> Vec3:
        if type(self) == Vec3:
            return self  # immutable
        return self.__class__(self.x, self.y, self.z)

    def __iter__(self) -> Iterator[_NumType]:
        return iter((self.x, self.y, self.z))

    def __abs__(self) -> float:
        """Return (absolute) length of vector"""
        return math.hypot(*self)

    def length(self) -> float:
        return self.__abs__()

    def distance(self, v: Vec3) -> float:
        return (self - v).length()

    def dot(self, v: Vec3) -> float:
        return self.x * v.x + self.y * v.y + self.z * v.z

    def cross(self, v: Vec3) -> Vec3:
        return Vec3(
            self.y * v.z - self.z * v.y,
            self.z * v.x - self.x * v.z,
            self.x * v.y - self.y * v.x,
        )

    def multiply_elementwise(self, v: Vec3) -> Vec3:
        return Vec3(self.x * v.x, self.y * v.y, self.z * v.z)

    def norm(self) -> Vec3:
        return self / self.length()

    def map(self, func: Callable[[_NumType], _NumType]) -> Vec3:
        return Vec3(func(self.x), func(self.y), func(self.z))

    def map_pairwise(self, func: Callable[[_NumType, _NumType], _NumType], v: Vec3) -> Vec3:
        return Vec3(func(self.x, v.x), func(self.y, v.y), func(self.z, v.z))

    def rotate(self, v: Vec3, degree: float) -> Vec3:
        """Rotate self around vector v by degrees"""
        return self.rotate_rad(v, math.radians(degree))

    def rotate_rad(self, v: Vec3, phi: float) -> Vec3:
        """Rotate self around vector v by phi degree radians - Rodrigues rotation"""
        v = v.norm()
        return (
            self * math.cos(phi)
            + v.cross(self) * math.sin(phi)
            + v * v.dot(self) * (1.0 - math.cos(phi))
        )

    def round(self, ndigits: int = 0) -> Vec3:
        return self.__round__(ndigits)

    def floor(self) -> Vec3:
        return self.__floor__()

    def ceil(self) -> Vec3:
        return self.__ceil__()

    def trunc(self) -> Vec3:
        return self.__trunc__()

    def asdict(self) -> dict[str, _NumType]:
        return asdict(self)

    def closest_axis(self) -> Vec3:
        greatest = max(self.map(abs))
        if abs(self.x) == greatest:
            return Vec3(x=self.x)
        elif abs(self.y) == greatest:
            return Vec3(y=self.y)
        elif abs(self.z) == greatest:
            return Vec3(z=self.z)
        else:
            return Vec3()

    def direction_label(self) -> DIRECTION:
        axis = self.closest_axis()
        if axis.x > 0:
            return "east"
        elif axis.x < 0:
            return "west"
        elif axis.y > 0:
            return "up"
        elif axis.y < 0:
            return "down"
        elif axis.z > 0:
            return "south"
        elif axis.z < 0:
            return "north"
        else:
            return "east"

    def cardinal_label(self) -> CARDINAL:
        return self.withY(0).direction_label()  # type: ignore

    def east(self, n: _NumType = 1) -> Vec3:
        return Vec3(self.x + n, self.y, self.z)

    def west(self, n: _NumType = 1) -> Vec3:
        return Vec3(self.x - n, self.y, self.z)

    def up(self, n: _NumType = 1) -> Vec3:
        return Vec3(self.x, self.y + n, self.z)

    def down(self, n: _NumType = 1) -> Vec3:
        return Vec3(self.x, self.y - n, self.z)

    def south(self, n: _NumType = 1) -> Vec3:
        return Vec3(self.x, self.y, self.z + n)

    def north(self, n: _NumType = 1) -> Vec3:
        return Vec3(self.x, self.y, self.z - n)

    def withX(self, n: _NumType) -> Vec3:
        return Vec3(n, self.y, self.z)

    def withY(self, n: _NumType) -> Vec3:
        return Vec3(self.x, n, self.z)

    def withZ(self, n: _NumType) -> Vec3:
        return Vec3(self.x, self.y, n)


if __name__ == "__main__":
    # run some performance benchmarks for dataclass Vec3
    import sys
    import timeit
    from statistics import mean

    print("(Aprox.) Size of a Vec3:", sys.getsizeof(Vec3(1, -333, 98765)))

    repeat = 10
    benchmarks = [
        "Vec3(1, -3, 2)",
        "Vec3(x=1, y=-3, z=2)",
        "Vec3().up() + Vec3().down()",
        "Vec3(1,2,3).cross(Vec3(3,2,1))",
    ]
    for bm in benchmarks:
        times = [timeit.timeit(bm, globals=globals()) for _ in range(repeat)]
        print(f"{mean(times):.3f}", "->", bm)

    # fastest is frozen=False and slots=True
    # then frozen=False and slots=False
    # then frozen=True and slots=True
    # finally frozen=True and slots=False
