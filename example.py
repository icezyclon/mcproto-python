from mcpb import Minecraft, Vec3

mc = Minecraft()

mc.postToChat("Hello Minecraft!")

print("Block at origin:", mc.getBlock(Vec3(0, 0, 0)))
