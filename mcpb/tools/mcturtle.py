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
            self._set_block_list = self._mc.setBlockList
        else:
            self._set_block_list = self._world.setBlockList

        self._home_pos = self._pos
        self._dir_front: Vec3 = Vec3().east(1)
        self._dir_up: Vec3 = Vec3().up(1)
        self._head: str = "diamond_block"
        self._body: str = "black_wool"
        self._speed: float = 1
        self._pendown: bool = True
        self._show_head: bool = True
        self._pensize: int = 1
        self._batch_time: float = 0.0

        self._head_pos = []
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
        self.stift_breite = self.pensize
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
    def _body_pos(self) -> list[Vec3]:
        center = self._pos.floor()
        if self._pensize == 1:
            return [center]
        ra = range(-(self._pensize // 2), self._pensize // 2 + self._pensize % 2)
        return [center.addX(x).addY(y).addZ(z) for x in ra for y in ra for z in ra]

    def _rotate(self, angle: float, to: Vec3) -> None:
        k = self._dir_front.cross(to).norm()
        self._dir_front = self._dir_front.rotate(k, angle).norm()
        self._dir_up = self._dir_up.rotate(k, angle).norm()

    def _paint_body(self) -> None:
        if self._pendown:
            self._set_block_list(self._body, self._body_pos)
        elif self._show_head:
            self._set_block_list("air", self._body_pos)

    def _paint_head(self) -> None:
        if self._show_head:
            self._head_pos = self._body_pos
            self._set_block_list(self._head, self._head_pos)

    def home(self) -> Turtle:
        dirv = self._home_pos - self._pos
        self._dir_front = dirv.norm()  # TODO: use "rotate_towards" instead
        # TODO: could interrupt during march home
        self.forward(dirv.length())
        self._pos = self._home_pos
        self._dir_front = Vec3().east(1)
        self._dir_up = Vec3().up(1)
        return self

    def goto(self, new_position: Vec3) -> Turtle:
        self._paint_body()
        self._pos = new_position
        self._paint_head()
        return self

    def head(self, block: str) -> Turtle:
        self._head = block
        self._paint_head()
        return self

    def body(self, block: str) -> Turtle:
        self._body = block
        return self

    def speed(self, speed: float | None) -> Turtle:
        """Define how many blocks should be set in a second"""
        if speed is None or speed > 0:
            self._speed = speed
        else:
            raise ValueError("The speed of the Turtle must be a positive number")
        return self

    def forward(self, by: float) -> Turtle:
        wait = (1.0 / self._speed) if self._speed else None
        for _ in range(int(abs(by))):
            self._paint_body()
            self._pos = self._pos + (self._dir_front * _sign(by))
            self._paint_head()
            if self._speed:
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

    def pensize(self, size: int) -> Turtle:
        if not isinstance(size, int):
            raise TypeError("The pensize must be an integer")
        if size < 1:
            raise ValueError("The pensize must be larger or equal to 1")
        self._set_block_list("air", self._body_pos)
        self._pensize = size
        self._paint_head()
        return self

    def hidehead(self) -> Turtle:
        self._show_head = False
        self._set_block_list("air", self._body_pos)
        return self

    def showhead(self) -> Turtle:
        self._show_head = True
        self._paint_head()
        return self

    def start_batch_mode(self, batch_time: float) -> Turtle:
        if batch_time <= 0.0:
            raise ValueError("The batch time must be a positive number")
        if self._batch_time > 0:
            self._batch_time = batch_time
            return self

        from threading import Thread

        def working_loop():
            while self._batch_time > 0.0:
                sleep(self._batch_time)
                lists, self._batch_list = self._batch_list, []
                self._set_block_list(self._body, lists)

        def new_paint_body():
            self._batch_list.extend(self._body_pos)

        self._batch_time = batch_time
        self._old_paint_body = self._paint_body
        self._old_paint_head = self._paint_head
        self._batch_list = []
        self._paint_body = new_paint_body
        self._paint_head = lambda: None
        self._batching_thread = Thread(target=working_loop, daemon=True)
        self._batching_thread.start()
        return self

    def stop_batch_mode(self) -> Turtle:
        if self._batch_time == 0.0:
            return
        self._paint_body = self._old_paint_body
        self._paint_head = self._old_paint_head
        self._batch_time = 0.0
        self._batching_thread.join()
        self._batching_thread = None
        self._set_block_list(self._body, self._batch_list)
        self._batch_list = []
        return self
