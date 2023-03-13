from mcproto import Entity, Event, MCProtoFehler, Minecraft, Player, Vec3, World


def test_mc_creation():
    mc = Minecraft()
    assert mc.host == "localhost"
    name = "IceZyclon"
    p = mc.getOfflinePlayer(name)
    assert p
    assert p.name == p.id == name
