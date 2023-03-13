"""In diesem Modul befinden sich die Farben und Effekte die auf Text in Minecraft
angewendet werden können.

Dies funktioniert Beispielsweise für den Chat oder für Schilder.

>>> from mcproto.text import *
>>> mc.postToChat(ROT + FETT + "Hallo Python!" + RESET)

oder

>>> from mcproto import text
>>> mc.postToChat(text.ROT + text.FETT + "Hallo Python!" + text.RESET)
"""

BLACK = "§0"
DARK_BLUE = "§1"
DARK_GREEN = "§2"
DARK_AQUA = "§3"
DARK_RED = "§4"
DARK_PURPLE = "§5"
GOLD = "§6"
GRAY = "§7"
DARK_GRAY = "§8"
BLUE = "§9"
GREEN = "§a"
AQUA = "§b"
RED = "§c"
PURPLE = "§d"
YELLOW = "§e"
WHITE = "§f"
MINECOIN_GOLD = "§g"

UNDERLINED = "§u"
BOLD = "§l"
ITALIC = "§o"
STRIKETHROUGH = "§m"
ILLEGIBLE = "§k"
RESET = "§r"

# Deutsche Bezeichnungen

SCHWARZ = BLACK
DUNKEL_BLAU = DARK_BLUE
DUNKEL_GRÜN = DARK_GREEN
DUNKEL_AQUA = DARK_AQUA
DUNKEL_ROT = DARK_RED
DUNKEL_VIOLETT = DARK_PURPLE
# GOLD = GOLD
GRAU = GRAY
DUNKEL_GRAU = DARK_GRAY
BLAU = BLUE
GRÜN = GREEN
TÜRKIS = AQUA
ROT = RED
VIOLETT = PURPLE
GELB = YELLOW
WEIS = WHITE
# MINECOIN_GOLD = MINECOIN_GOLD

UNTERSTRICHEN = UNDERLINED
FETT = BOLD
KURSIV = ITALIC
DURCHGESTRICHEN = STRIKETHROUGH
UNLESBAR = ILLEGIBLE
# RESET = RESET
