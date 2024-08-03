.. MCPB documentation master file, created by
   sphinx-quickstart on Fri Aug  2 10:38:07 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

MCPB documentation
==================

.. .. .. toctree::
.. ..    :maxdepth: 2
.. ..    :caption: Contents:

.. .. include:: source/mcpb.rst
   .. :inherited-members:

-----

Minecraft - Connection
======================

.. autoclass:: mcpb.Minecraft

Commands
--------

.. autoclass:: mcpb._base._HasStub

Entities
--------

.. autoclass:: mcpb.entity._EntityCache

Players
-------

.. autoclass:: mcpb.player._PlayerCache

Blocks/Entities/Items
---------------------

.. autoclass:: mcpb.world._DefaultWorld
   :no-index:

Worlds
------

.. autoclass:: mcpb.world._WorldHub

Events
------

.. autoclass:: mcpb.events._EventHandler

.. autoclass:: mcpb.events.PlayerJoinEvent
   :inherited-members:

.. autoclass:: mcpb.events.PlayerLeaveEvent
   :inherited-members:

.. autoclass:: mcpb.events.PlayerDeathEvent
   :inherited-members:

.. autoclass:: mcpb.events.ChatEvent
   :inherited-members:

.. autoclass:: mcpb.events.BlockHitEvent
   :inherited-members:

.. autoclass:: mcpb.events.ProjectileHitEvent
   :inherited-members:

-----

Entity
======

.. autoclass:: mcpb.entity.Entity

Player
======

.. autoclass:: mcpb.player.Player

-----

World - Dimensions
==================

.. autoclass:: mcpb.world.World

.. autoclass:: mcpb.world._DefaultWorld

-----

Vec3 - Coordinates
==================

.. autoclass:: mcpb.Vec3
