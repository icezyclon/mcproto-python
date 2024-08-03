from unittest.mock import MagicMock, PropertyMock, call

import pytest
from pytest_mock import MockerFixture

from mcpb import Minecraft, Vec3, World
from mcpb.tools import Turtle

# see https://docs.python.org/3/library/unittest.mock.html#unittest.mock.PropertyMock


def test_init_wrong_mc():
    with pytest.raises(TypeError):
        Turtle(object())


def test_init_wrong_pos():
    mc = MagicMock(spec=Minecraft)
    assert isinstance(mc, Minecraft)

    with pytest.raises(TypeError):
        Turtle(mc, object())


def test_init_wrong_world():
    mc = MagicMock(spec=Minecraft)
    assert isinstance(mc, Minecraft)

    with pytest.raises(TypeError):
        Turtle(mc, Vec3(1, -2, 3), object())


@pytest.mark.skip(reason="should be adjusted after Turtle update")
def test_init_correct_all_provided():
    mc = MagicMock(spec=Minecraft)
    assert isinstance(mc, Minecraft)
    pos = Vec3(1, -2, 3)
    world = World(mc, mc, "minecraft:test", "my_test_world")

    # execute
    t = Turtle(mc, pos, world)

    # check
    assert t._mc is mc
    assert t._pos is pos
    assert t._world is world
    assert len(mc.mock_calls) == 2  # no mc.getPlayer() and one setBlock call
    assert not mc.getPlayer.called
    assert mc.setBlock.called or mc.setBlockIn.called


@pytest.mark.skip(reason="should be adjusted after Turtle update")
def test_init_create_new_instance_of_mc_get_pos_and_world_if_not_provided(
    mocker: MockerFixture,
):
    # setup
    mocked_mcclass = mocker.patch("mcpb.tools.mcturtle.Minecraft", spec=True)
    mc = MagicMock(spec=Minecraft)
    mocked_mcclass.return_value = mc
    assert isinstance(mc, Minecraft)
    mocked_player = MagicMock()
    mc.getPlayer.return_value = mocked_player
    pos = Vec3(1, -2, 3)
    mocked_pos = PropertyMock(return_value=pos)
    type(mocked_player).pos = mocked_pos
    world = "my_test_world"
    mocked_world = PropertyMock(return_value=world)
    type(mocked_player).world = mocked_world

    # execute
    t = Turtle()

    # check
    assert t._mc is mc
    assert t._pos == pos
    assert t._world == world
    mocked_mcclass.assert_called_once()
    mc.getPlayer.assert_called_once()
    assert mocked_pos.call_count == 1
    assert mocked_world.call_count == 1
    assert len(mc.mock_calls) == 2  # one mc.getPlayer() and one mc.setBlock call
    assert mc.getPlayer.called
    assert mc.setBlock.called or mc.setBlockIn.called


@pytest.mark.skip(reason="should be adjusted after Turtle update")
def test_init_create_new_instance_of_mc_if_not_provided(mocker: MockerFixture):
    # setup
    mocked_mcclass = mocker.patch("mcpb.tools.mcturtle.Minecraft", spec=True)
    mc = MagicMock(spec=Minecraft)
    mocked_mcclass.return_value = mc
    assert isinstance(mc, Minecraft)

    # execute
    t = Turtle(pos=Vec3(1, -2, 3), world="test")

    # check
    mocked_mcclass.assert_called_once()
    assert t._mc is mc
    assert len(mc.mock_calls) == 1  # no mc.getPlayer() and one setBlock call
    assert not mc.getPlayer.called
    assert mc.setBlock.called or mc.setBlockIn.called


@pytest.mark.skip(reason="should be adjusted after Turtle update")
def test_init_get_player_position_if_not_provided():
    # setup
    mc = MagicMock(spec=Minecraft)
    assert isinstance(mc, Minecraft)
    mocked_player = MagicMock()
    mc.getPlayer.return_value = mocked_player
    pos = Vec3(1, -2, 3)
    mocked_pos = PropertyMock(return_value=pos)
    type(mocked_player).pos = mocked_pos

    # execute
    t = Turtle(mc, world="test")

    # check
    assert t._mc is mc
    mc.getPlayer.assert_called_once()
    assert t._pos == pos
    assert mocked_pos.call_count == 1
    assert len(mc.mock_calls) == 2  # one mc.getPlayer() and one mc.setBlock call
    assert mc.getPlayer.called
    assert mc.setBlock.called or mc.setBlockIn.called


@pytest.mark.skip(reason="should be adjusted after Turtle update")
def test_init_get_player_position_and_world_if_both_not_provided():
    # setup
    mc = MagicMock(spec=Minecraft)
    assert isinstance(mc, Minecraft)
    mocked_player = MagicMock()
    mc.getPlayer.return_value = mocked_player
    pos = Vec3(1, -2, 3)
    mocked_pos = PropertyMock(return_value=pos)
    type(mocked_player).pos = mocked_pos
    world = "my_test_world"
    mocked_world = PropertyMock(return_value=world)
    type(mocked_player).world = mocked_world

    # execute
    t = Turtle(mc)

    # check
    assert t._mc is mc
    mc.getPlayer.assert_called_once()
    assert t._pos == pos
    assert mocked_pos.call_count == 1
    assert mocked_world.call_count == 1
    assert len(mc.mock_calls) == 2  # one mc.getPlayer() and one mc.setBlock call
    assert mc.getPlayer.called
    assert mc.setBlock.called or mc.setBlockIn.called


@pytest.mark.skip(reason="should be adjusted after Turtle update")
def test_init_empty_world_and_no_player_call_if_not_provided():
    mc = MagicMock(spec=Minecraft)
    assert isinstance(mc, Minecraft)
    pos = Vec3(1, -2, 3)

    # execute
    t = Turtle(mc, pos)

    # check
    assert t._mc is mc
    assert t._pos is pos
    assert t._world is None
    assert len(mc.mock_calls) == 1  # no mc.getPlayer() and one setBlock call
    assert not mc.getPlayer.called
    assert mc.setBlock.called or mc.setBlockIn.called


@pytest.mark.skip(reason="should be adjusted after Turtle update")
def test_body_pos_is_floored():
    # setup
    mc = MagicMock(spec=Minecraft)
    assert isinstance(mc, Minecraft)
    pos = Vec3(1.2, -2.6, 3.5)

    # execute
    t = Turtle(mc, pos)

    # check
    assert t._body_pos == pos.floor()


@pytest.mark.skip(reason="should be adjusted after Turtle update")
def test_move_forward():
    # setup
    mc = MagicMock(spec=Minecraft)
    assert isinstance(mc, Minecraft)
    pos = Vec3(1, -2, 3)

    # execute
    t = Turtle(mc, pos).forward(2)

    # check
    assert t._body_pos == pos.east(2)
    assert len(mc.mock_calls) == 5
    mc.assert_has_calls(
        [
            call.setBlock(t._head, pos),
            call.setBlock(t._body, pos),
            call.setBlock(t._head, pos.east()),
            call.setBlock(t._body, pos.east()),
            call.setBlock(t._head, pos.east(2)),
        ],
        any_order=False,
    )


@pytest.mark.skip(reason="should be adjusted after Turtle update")
def test_turn_and_move_right():
    # setup
    mc = MagicMock(spec=Minecraft)
    assert isinstance(mc, Minecraft)
    pos = Vec3(1, -2, 3)

    # execute
    t = Turtle(mc, pos).right(90).forward(1)

    # check
    assert t._body_pos == pos.south()
    assert len(mc.mock_calls) == 3
    mc.assert_has_calls(
        [
            call.setBlock(t._head, pos),
            call.setBlock(t._body, pos),
            call.setBlock(t._head, pos.south()),
        ],
        any_order=False,
    )
