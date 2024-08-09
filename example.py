from mcpb import Minecraft, Vec3

mc = Minecraft()

mc.postToChat("Hello Minecraft!")

origin = Vec3(0, 0, 0)
block = mc.getBlock(origin)

mc.postToChat("Block type at origin:", block)

mc.postToChat("Changing that block to obsidian!")

mc.setBlock("obsidian", origin)
