from .mcpb import minecraft_pb2 as pb

__all__ = [
    "MCProtoFehler",
    "UnbekannterFehler",
    "FehlendesArgument",
    "UngültigesArgument",
    "NichtImplementiert",
    "WeltNichtGefunden",
    "SpielerNichtGefunden",
    "BlockTypNichtGefunden",
    "WesenTypNichtGefunden",
    "WesenNichtSpawnbar",
    "WesenNichtGefunden",
]


class MCProtoFehler(Exception):
    pass


class UnbekannterFehler(MCProtoFehler):
    pass


class FehlendesArgument(MCProtoFehler):
    pass


class UngültigesArgument(MCProtoFehler):
    pass


class NichtImplementiert(MCProtoFehler):
    pass


class WeltNichtGefunden(MCProtoFehler):
    pass


class SpielerNichtGefunden(MCProtoFehler):
    pass


class BlockTypNichtGefunden(MCProtoFehler):
    pass


class WesenTypNichtGefunden(MCProtoFehler):
    pass


class WesenNichtSpawnbar(MCProtoFehler):
    pass


class WesenNichtGefunden(MCProtoFehler):
    pass


# Mapping muss mit Fehlernummern in .proto übereinstimmen
exc = {
    1: (
        UnbekannterFehler,
        "Ein unbekannter Fehler ist aufgetreten",
        "Ein unbekannter Fehler ist mit '{}' aufgetreten",
    ),
    2: (
        FehlendesArgument,
        "Ein Argument wurde hat gefehlt",
        "Das Argument '{}' war nicht gesetzt oder hat gefehlt",
    ),
    3: (
        UngültigesArgument,
        "Ein Argument war ungültig oder wurde falsch verwendet",
        "Das Argument '{}' war ungültig oder wurde falsch verwendet",
    ),
    4: (
        NichtImplementiert,
        "Die Verwendung einer Funktion oder eines Feldes wurde noch nicht implementiert",
        "Die Verwendung von Funktion oder Feld '{}' wurde noch nicht implementiert",
    ),
    5: (
        WeltNichtGefunden,
        "Eine angegebene Welt konnte nicht gefunden werden",
        "Die Welt '{}' konnte nicht gefunden werden",
    ),
    6: (
        SpielerNichtGefunden,
        "Ein Spieler konnte nicht gefunden werden",
        "Der Spieler '{}' konnte nicht gefunden werden (vielleicht ist er offline?)",
    ),
    7: (
        BlockTypNichtGefunden,
        "Ein angegebener Blocktyp konnte nicht gefunden werden",
        "'{}' entspricht keinem bekannten Blocktyp",
    ),
    8: (
        WesenTypNichtGefunden,
        "Ein angegebener Wesentyp konnte nicht gefunden werden",
        "'{}' entspricht keinem bekannten Wesentyp",
    ),
    9: (
        WesenNichtSpawnbar,
        "Ein angegebenes Wesen ist nicht spawnbar",
        "'{}' ist nicht spawnbar",
    ),
    10: (
        WesenNichtGefunden,
        "Ein angegebenes Wesen konnte nicht gefunden werden",
        "Das Wesen mit id '{}' konnte nicht gefunden werden",
    ),
}


def exception_from_status(status: pb.Status) -> Exception:
    if status.code in exc.keys():
        e, default, default_extra = exc[status.code]
        print("Status Extra:", status.extra)
        if status.extra:
            return e(default_extra.format(status.extra))
        else:
            return e(default)
    else:
        return NotImplementedError(f"Der Fehlercode {status.code} wurde nocht nicht implementiert")


def raise_on_error(status: pb.Status) -> None:
    if status.code:
        raise exception_from_status(status)
