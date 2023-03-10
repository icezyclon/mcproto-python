import math
from numbers import Number

import pytest

from mcproto import Vec3


def close(a, b) -> bool:
    if isinstance(a, Number) and isinstance(b, Number):
        return math.isclose(a, b, abs_tol=6)
    return all(math.isclose(i, j, abs_tol=6) for i, j in zip(a, b, strict=True))


def test_eq() -> None:
    # created by dataclass, only sanity checks
    assert Vec3() == Vec3()
    assert Vec3(1, 2, 3) == Vec3(1, 2, 3)
    assert Vec3(1, 2, 3) == Vec3(1.0, 2.0, 3.0)
    assert Vec3(1, 2, 3) != Vec3()
    assert Vec3() != Vec3(1, 2, 3)
    assert Vec3() != 0  # type: ignore
    assert 0 != Vec3()  # type: ignore
    assert Vec3() != 0.0  # type: ignore
    assert 0.0 != Vec3()  # type: ignore
    assert Vec3() != False  # type: ignore
    assert False != Vec3()  # type: ignore
    assert Vec3() != True  # type: ignore
    assert True != Vec3()  # type: ignore
    assert Vec3() != None  # type: ignore
    assert None != Vec3()  # type: ignore
    assert Vec3() != object()


def test_bool() -> None:
    assert bool(Vec3(1, -2, 3)) == True
    assert bool(Vec3()) == True  # better to have any vector be True


def test_init() -> None:
    assert Vec3(0, 0, 0) == Vec3(x=0, y=0, z=0)
    assert Vec3() == Vec3(x=0, y=0, z=0)
    assert Vec3(2.5, 3.5, 4.5)
    assert Vec3(2.5, y=3.5, z=4.5)
    assert Vec3(y=3.5, z=4.5).x == 0
    assert Vec3()


def test_statics() -> None:
    a = 12
    assert Vec3().up() == Vec3(0, 1, 0)
    assert Vec3().down() == Vec3(0, -1, 0)
    assert Vec3().south() == Vec3(0, 0, 1)
    assert Vec3().north() == Vec3(0, 0, -1)
    assert Vec3().east() == Vec3(1, 0, 0)
    assert Vec3().west() == Vec3(-1, 0, 0)
    assert Vec3().east(a) == Vec3(a, 0, 0)
    assert Vec3().up(a) == Vec3(0, a, 0)
    assert Vec3().south(a) == Vec3(0, 0, a)
    assert Vec3().east(-a) == Vec3(-a, 0, 0)
    assert Vec3().up(-a) == Vec3(0, -a, 0)
    assert Vec3().south(-a) == Vec3(0, 0, -a)
    assert Vec3().east(-a) == Vec3().west(a)
    assert Vec3().up(-a) == Vec3().down(a)
    assert Vec3().south(-a) == Vec3().north(a)
    assert Vec3().withX(a) == Vec3(x=a)
    assert Vec3().withX(-a) == Vec3(x=-a)
    assert Vec3().withY(a) == Vec3(y=a)
    assert Vec3().withY(-a) == Vec3(y=-a)
    assert Vec3().withZ(a) == Vec3(z=a)
    assert Vec3().withZ(-a) == Vec3(z=-a)
    myvec = Vec3(112, -1, -99)
    assert myvec.up() == myvec + Vec3(0, 1, 0)
    assert myvec.down() == myvec + Vec3(0, -1, 0)
    assert myvec.south() == myvec + Vec3(0, 0, 1)
    assert myvec.north() == myvec + Vec3(0, 0, -1)
    assert myvec.east() == myvec + Vec3(1, 0, 0)
    assert myvec.west() == myvec + Vec3(-1, 0, 0)
    assert myvec.east(a) == myvec + Vec3(a, 0, 0)
    assert myvec.up(a) == myvec + Vec3(0, a, 0)
    assert myvec.south(a) == myvec + Vec3(0, 0, a)
    assert myvec.east(-a) == myvec + Vec3(-a, 0, 0)
    assert myvec.up(-a) == myvec + Vec3(0, -a, 0)
    assert myvec.south(-a) == myvec + Vec3(0, 0, -a)
    assert myvec.east(-a) == myvec + Vec3().west(a)
    assert myvec.up(-a) == myvec + Vec3().down(a)
    assert myvec.south(-a) == myvec + Vec3().north(a)
    assert myvec.withX(a) == Vec3(a, myvec.y, myvec.z)
    assert myvec.withY(a) == Vec3(myvec.x, a, myvec.z)
    assert myvec.withZ(a) == Vec3(myvec.x, myvec.y, a)


def test_neg() -> None:
    v = Vec3(1, 2, 3)
    assert -v == Vec3(-v.x, -v.y, -v.z)
    assert +(-v) == -v
    assert -(+v) == -v
    assert -(-v) == v
    assert +(+v) == v


def test_abs_length() -> None:
    from math import sqrt

    v = Vec3(1, -2, 3)
    l = sqrt(v.x**2 + v.y**2 + v.z**2)
    assert close(v.length(), l)
    assert close(abs(v), v.length())


def test_distance() -> None:
    v1 = Vec3(1, -2, 3)
    v2 = Vec3(5, 6, 1)
    assert v1.distance(v2) == (v2 - v1).length()
    assert v1.distance(v2) == v2.distance(v1)
    assert close(v1.distance(v2), 9.1651513)


def test_add() -> None:
    a = 5
    v = Vec3(1, 2, 3)
    assert v + a == Vec3(v.x + a, v.y + a, v.z + a)
    assert a + v == Vec3(v.x + a, v.y + a, v.z + a)
    assert v + v == Vec3(v.x + v.x, v.y + v.y, v.z + v.z)
    assert v + (-v) == Vec3()
    with pytest.raises(TypeError):
        assert v + object()  # type: ignore
    with pytest.raises(TypeError):
        assert object() + v  # type: ignore


def test_sub() -> None:
    a = 5
    v = Vec3(1, 2, 3)
    w = Vec3(-12, 133, -4.5)
    assert v - a == Vec3(v.x - a, v.y - a, v.z - a)
    assert a - v == Vec3(v.x - a, v.y - a, v.z - a)
    assert v - v == Vec3(v.x - v.x, v.y - v.y, v.z - v.z)
    assert v - v == Vec3()
    assert v - w != w - v
    assert v - w == -w + v
    assert v - (-v) == v + v
    with pytest.raises(TypeError):
        assert v - object()  # type: ignore
    with pytest.raises(TypeError):
        assert object() - v  # type: ignore


def test_mul() -> None:
    a = 5
    v = Vec3(1, 2, 3)
    k = v + Vec3(4, 2, 0)

    assert v * a == Vec3(v.x * a, v.y * a, v.z * a)
    assert a * v == Vec3(v.x * a, v.y * a, v.z * a)

    assert v ^ v == v.dot(v)
    assert v ^ v == 14
    assert v ^ v == v.x * v.x + v.y * v.y + v.z * v.z
    assert v ^ v > 0
    assert v ^ (-v) < 0
    assert v ^ k == k ^ v == v.dot(k) == k.dot(v) == 22

    assert v * Vec3() == Vec3()
    assert v * Vec3(1, 1, 1) == v
    assert v * k == Vec3(v.x * k.x, v.y * k.y, v.z * k.z)
    assert v * k == v.multiply_elementwise(k)
    assert v.multiply_elementwise(k) == k.multiply_elementwise(v)
    assert v.multiply_elementwise(k) == Vec3(5, 8, 9)

    assert v @ v == v.cross(v)
    assert v @ v == Vec3()
    assert v @ k == v.cross(k)
    assert k @ v == k.cross(v)
    assert v @ k != k.cross(v)
    assert v @ k == -k.cross(v)
    assert v @ k == Vec3(-6, 12, -6)

    with pytest.raises(TypeError):
        assert v ^ object()  # type: ignore
    with pytest.raises(TypeError):
        assert object() ^ v  # type: ignore
    with pytest.raises(TypeError):
        assert v * object()  # type: ignore
    with pytest.raises(TypeError):
        assert object() * v  # type: ignore
    with pytest.raises(TypeError):
        assert v @ object()  # type: ignore
    with pytest.raises(TypeError):
        assert object() @ v  # type: ignore


def test_div() -> None:
    a = 2
    v = Vec3(1, 2, 3)
    assert v / a == Vec3(v.x / a, v.y / a, v.z / a)
    assert v // a == Vec3(v.x // a, v.y // a, v.z // a)
    assert v / a == v * (1.0 / a)
    assert v // a != v * (1.0 // a)
    assert v // a == v.map(lambda w: w // a)
    with pytest.raises(TypeError):
        assert v / object()  # type: ignore
    with pytest.raises(TypeError):
        # does not make sense to implement, use mul
        assert a / v == v * (a / 1.0)  # type: ignore
    with pytest.raises(TypeError):
        # does not make sense
        assert a // v  # type: ignore
    with pytest.raises(ZeroDivisionError):
        assert v / 0
    with pytest.raises(ZeroDivisionError):
        assert v // 0


def test_round() -> None:
    from math import ceil, floor

    v = Vec3(1.4, 2.61, 3.8)
    assert round(v) == v.round() == Vec3(1, 3, 4)
    assert round(v) == v.round(0) == Vec3(1, 3, 4)
    assert round(v, 0) == v.round() == Vec3(1, 3, 4)
    assert round(v, 0) == v.round(0) == Vec3(1, 3, 4)
    assert floor(v) == v.floor() == Vec3(1, 2, 3)
    assert ceil(v) == v.ceil() == Vec3(2, 3, 4)

    assert round(v, 1) != v
    assert round(v, 2) == v

    assert all(isinstance(w, int) for w in v.round())  # round can guarantee int
    assert all(isinstance(w, int) for w in round(v))  # round can guarantee int

    assert all(isinstance(w, int) for w in v.round(0))  # round can guarantee int
    assert all(isinstance(w, int) for w in round(v, 0))  # round can guarantee int

    assert all(
        isinstance(w, float) for i in range(1, 4) for w in v.round(i)
    )  # requires float ndigits > 0
    assert all(
        isinstance(w, float) for i in range(1, 4) for w in round(v, i)
    )  # requires float ndigits > 0

    # python uses backer's rounding, so not correct for 0.5
    # and also not accurate for negative numbers
    assert v.round() == v.map(lambda w: int(w + 0.5))


def test_iter() -> None:
    v = Vec3(1, 2, 3)
    assert list(iter(v)) == list(range(1, 4))
    assert list(v) == list(range(1, 4))


def test_len_norm() -> None:
    v = Vec3(1, -2, 3)
    assert close(v.length(), (1 + 4 + 9) ** 0.5)
    assert close(v.norm(), v / v.length())
    assert close(v.norm().length(), 1)


def test_map() -> None:
    import operator

    v = Vec3(1.2, -2.9, 3)
    assert v.map(abs) == v.map(lambda w: w * (1 if w >= 0 else -1))
    f = lambda w: w + 0.5
    assert v.map(f) == Vec3(*list(map(f, v)))
    f = lambda w: (w * 3 + 12.5) % 19
    assert v.map(f) == Vec3(*list(map(f, v)))
    assert v.map(operator.neg) == -v
    w = Vec3(-3, 0, 2)
    assert v.map_pairwise(min, w) == Vec3(-3, -2.9, 2)
    assert v.map_pairwise(max, w) == Vec3(1.2, 0, 3)
    assert v.map_pairwise(lambda e1, e2: e1 if isinstance(e1, int) else e2, w) == Vec3(-3, 0, 3)
    assert v.map_pairwise(operator.add, w) == v + w
    assert v.map_pairwise(operator.mul, w) == v * w
    assert v.map_pairwise(operator.pow, w) == Vec3(v.x**w.x, v.y**w.y, v.z**w.z)


def test_rotate() -> None:
    from math import radians

    v = Vec3(1, 2, 3)
    k = Vec3().up()
    w90 = radians(90)
    w180 = radians(180)
    w270 = radians(270)
    w360 = radians(360)
    assert 4 * w90 == w360
    assert 3 * w90 == w270
    assert 2 * w90 == w180
    assert 2 * w180 == w360
    assert close(Vec3(3, 2, -1), v.rotate_rad(k, w90))
    assert close(Vec3(-1, 2, -3), v.rotate_rad(k, w180))
    assert close(Vec3(-3, 2, 1), v.rotate_rad(k, w270))

    def all_tests() -> None:
        assert close(v, v.rotate_rad(k, w360))
        assert close(v.rotate_rad(k, w90), v.rotate_rad(k, -w270))
        assert close(v.rotate_rad(k, w90).rotate_rad(k, w90), v.rotate_rad(k, w180))
        assert close(v.rotate_rad(k, w180).rotate_rad(k, w90), v.rotate_rad(k, -w90))
        assert close(v, v.rotate_rad(k, -w360))
        assert close(v.rotate_rad(k, w270), v.rotate_rad(-k, w90))
        assert close(v.rotate_rad(k, w180), v.rotate_rad(-k, w180))
        assert close(v.rotate_rad(k, w90), v.rotate_rad(-k, w270))
        for i in range(360):
            assert v.rotate(k, i) == v.rotate_rad(k, radians(i))

    all_tests()
    k = Vec3().north(5.5)
    assert close(Vec3(2, -1, 3), v.rotate_rad(k, w90))
    assert close(Vec3(-1, -2, 3), v.rotate_rad(k, w180))
    assert close(Vec3(-2, 1, 3), v.rotate_rad(k, w270))
    all_tests()
    k = Vec3().west(-2)
    assert close(Vec3(1, -3, 2), v.rotate_rad(k, w90))
    assert close(Vec3(1, -2, -3), v.rotate_rad(k, w180))
    assert close(Vec3(1, 3, -2), v.rotate_rad(k, w270))
    all_tests()


def test_order() -> None:
    v1 = Vec3(0, 0, 0)
    v2 = Vec3(1, 2, 3)
    v3 = Vec3(3, 2, 1)
    assert sorted([v3, v1, v2]) == [v1, v2, v3]


def test_frozen() -> None:
    from dataclasses import FrozenInstanceError

    v = Vec3(1, 2, 3)
    with pytest.raises(FrozenInstanceError):
        v.x = 5  # type: ignore
    with pytest.raises(FrozenInstanceError):
        v.y = 5  # type: ignore
    with pytest.raises(FrozenInstanceError):
        v.z = 5  # type: ignore
    with pytest.raises(FrozenInstanceError):
        v.x += 5  # type: ignore
    with pytest.raises(FrozenInstanceError):
        v.y += 5  # type: ignore
    with pytest.raises(FrozenInstanceError):
        v.z += 5  # type: ignore


def test_asdict() -> None:
    v = Vec3(1, 2, 3)
    assert v.asdict() == {"x": 1, "y": 2, "z": 3}


def test_pickle() -> None:
    import pickle

    def assert_load_eq_dump(v: Vec3) -> None:
        assert pickle.loads(pickle.dumps(v)) == v

    assert_load_eq_dump(Vec3())
    assert_load_eq_dump(Vec3(z=1 / 3))
    assert_load_eq_dump(Vec3(-123456, -22, 123.6))


def test_copy() -> None:
    import copy

    v = Vec3(0, -22, 123.6)
    cp = copy.copy(v)
    dc = copy.deepcopy(v)
    assert v == cp == dc
    assert v is cp  # due to immutable
    assert v is dc  # due to immutable

    class NewTestVec(Vec3):
        pass

    nv = NewTestVec(0, -22, 123.6)
    cp = copy.copy(nv)
    dc = copy.deepcopy(nv)
    assert nv == cp == dc
    assert isinstance(cp, NewTestVec)
    assert isinstance(dc, NewTestVec)
    assert v != nv


def test_hash() -> None:
    assert hash(Vec3(0, -22, 123.6)) == hash(Vec3(0, -22, 123.6))
    assert hash(Vec3()) == hash(Vec3())
    assert hash(Vec3(0, -22, 123.6)) != hash(Vec3())
    assert hash(Vec3()) != hash(0)
    assert hash(Vec3()) != hash(object())
    assert hash(Vec3()) != hash(0.0)
    assert hash(Vec3()) != hash(False)


def test_pow() -> None:
    v = Vec3(1, -2, 3)
    a = 4
    with pytest.raises(TypeError):
        v**a  # type: ignore
    with pytest.raises(TypeError):
        a**v  # type: ignore
    with pytest.raises(TypeError):
        v**v  # type: ignore
    with pytest.raises(TypeError):
        v**-1  # type: ignore
    with pytest.raises(TypeError):
        v**0  # type: ignore
    with pytest.raises(TypeError):
        v**1  # type: ignore
