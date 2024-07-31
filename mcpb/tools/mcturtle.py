from __future__ import annotations

from time import sleep

from .. import Minecraft, Vec3, World


def _sign(num: int | float) -> float:
    return 1.0 if num >= 0.0 else -1.0


class Turtle:
    def __init__(
        self,
        mc: Minecraft | None = None,
        pos: Vec3 | None = None,
        world: World | str | None = None,
    ) -> None:
        if mc is None:
            self._mc = Minecraft()
        elif not isinstance(mc, Minecraft):
            raise TypeError("Argument mc must be of type Minecraft")
        else:
            self._mc = mc

        if isinstance(world, World):
            self._world = world
        elif isinstance(world, str):
            self._world = self._mc.getWorldByKey(world)
        elif world is not None:
            raise TypeError("Argument world must be of type str or mcpb.World")
        else:
            self._world = None

        if pos is None:
            player = self._mc.getPlayer()
            self._pos = player.pos
            if world is None:
                self._world = player.world
        elif not isinstance(pos, Vec3):
            raise TypeError("Argument pos must be of type Vec3")
        else:
            self._pos = pos

        if self._world is None:
            self._set_block = self._mc.setBlock
        else:
            self._set_block = self._world.setBlock

        self._dir_front: Vec3 = Vec3().east(1)
        self._dir_up: Vec3 = Vec3().up(1)
        self._head: str = "diamond_block"
        self._body: str = "black_wool"
        self._speed: float = 1
        self._pendown: bool = True
        self._show_head: bool = True
        self._penwidth: float = 1  # TODO: use
        self._batch_time: float = 0.0  # TODO: use

        self._paint_head()

        # Deutsche Funktionsnamen
        self.vorne = self.forward
        self.hinten = self.backward
        self.oben = self.up
        self.unten = self.down
        self.links = self.left
        self.rechts = self.right
        self.geschwindigkeit = self.speed
        self.kopf = self.head
        self.rumpf = self.body
        self.stift_anheben = self.penup
        self.stift_absetzten = self.pendown
        self.verstecke_kopf = self.hidehead
        self.zeige_kopf = self.showhead
        self.springe_zu = self.goto

        # Kürzel
        self.fd = self.forward
        self.back = self.backward
        self.bk = self.backward
        self.rt = self.right
        self.lt = self.left
        # self.ut = self.up # same length as up itself
        self.dt = self.down

    @property
    def _dir_right(self) -> Vec3:
        return self._dir_front.cross(self._dir_up).norm()

    @property
    def _body_pos(self) -> Vec3:
        return self._pos.floor()

    def _rotate(self, angle: float, to: Vec3) -> None:
        k = self._dir_front.cross(to).norm()
        self._dir_front = self._dir_front.rotate(k, angle).norm()
        self._dir_up = self._dir_up.rotate(k, angle).norm()

    def _paint_body(self) -> None:
        if self._pendown:
            self._set_block(self._body, self._body_pos)
        elif self._show_head:
            self._set_block("air", self._body_pos)

    def _paint_head(self) -> None:
        if self._show_head:
            self._set_block(self._head, self._body_pos)

    def goto(self, new_position: Vec3) -> Turtle:
        self._paint_body()
        self._pos = new_position
        self._paint_head()
        return self

    def head(self, block: str) -> Turtle:
        self._head = block
        return self

    def body(self, block: str) -> Turtle:
        self._body = block
        return self

    def speed(self, speed: float) -> Turtle:
        """Define how many blocks should be set in a second"""
        if speed > 0:
            self._speed = speed
        else:
            raise ValueError("The speed of the Turtle must be a positive number")
        return self

    def forward(self, by: float) -> Turtle:
        wait = 1.0 / self._speed
        for _ in range(int(abs(by))):
            self._paint_body()
            self._pos = self._pos + (self._dir_front * _sign(by))
            self._paint_head()
            sleep(wait)
        return self

    def backward(self, by: float) -> Turtle:
        self.forward(-by)
        return self

    def right(self, angle: float) -> Turtle:
        self._rotate(angle, self._dir_right)
        return self

    def left(self, angle: float) -> Turtle:
        self.right(-angle)
        return self

    def up(self, angle: float) -> Turtle:
        self._rotate(angle, self._dir_up)
        return self

    def down(self, angle: float) -> Turtle:
        self.up(-angle)
        return self

    def pendown(self) -> Turtle:
        self._pendown = True
        return self

    def penup(self) -> Turtle:
        self._pendown = False
        return self

    def hidehead(self) -> Turtle:
        self._show_head = False
        self._set_block("air", self._body_pos)
        return self

    def showhead(self) -> Turtle:
        self._show_head = True
        self._set_block(self._head, self._body_pos)
        return self
