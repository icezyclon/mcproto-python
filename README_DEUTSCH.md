[English 👈](README.md)

# MCProto Python Client Bibliothek

Diese Bibliothek ist dafür gedacht einen Minecraft Java Server, so wie zum Beispiel [Spigot](https://www.spigotmc.org/) oder [Paper](https://papermc.io/), der das **[mcproto](https://github.com/icezyclon/mcproto) Plugin** verwedet, mit Python zu steuern.

Sie wurde dabei sehr von [MCPI](https://github.com/martinohanlon/mcpi) und dessen dazugehörigen Plugin [RaspberryJuice](https://github.com/zhuowei/RaspberryJuice) inspiriert und versucht deren Konzepte zu nehmen und zu modernisieren um mit neueren Versionen von Minecraft umgehen zu können.

Die Bibliothek verwendet dabei sogenannte Protocol Buffers und kommuniziert mittels der Bibliothek [gRPC](https://grpc.io/) und deren Protokollen mit dem Plugin auf dem Server.

Wegen den neuen Python Features die im Projekt verwendet werden wird **Python 3.10+** benötigt!

## Versionen und Kompatibilität

Die Versionierung dieser Bibliothek ist lustig aber sehr einfach:

* Die ersten 4 Nummern der Versionsnummer geben die *Version des Plugins* an mit dem diese Bibliothek kompatibel ist.
* Die letzte Nummer ist die Patch-Nummer, welche nach kleineren Änderungen oder vom Plugin unabhängige Verbesserungen geändert wird. 

Zum Beispiel, die Version `1.18.2.1.X` würde bedeuten, dass das [mcproto Plugin](https://github.com/icezyclon/mcproto) 1.18.2.1 oder neuer benötigt wird.
Also, es *sollte* mit neueren Version des Plugins funktionieren falls es keine großen Änderungen im Protokoll gegeben hat.
Andererseits wird die Bibliothek sehr wahrscheinlich nicht mit älteren Versionen des Plugins als der angegebenen funktionieren.

TLDR; stimme die ersten 4 Nummern der Bibliothek mit der Version deines Plugins ab und wähle anschließend die Patch-Nummer so hoch wie möglich.

## Installationsanleitung

Im Moment befindet sich die Bibliothek noch *nicht* auf [PyPI](https://pypi.org/), wo sie aber potentiell in Zukunft zu finden sein wird.

Stattdessen kann die Bibliothek direkt von Github mit `pip install git+https://github.com/icezyclon/mcproto-python.git@main` installiert werden, wofür `git` benötigt wird.
Alternativ kann auch im heruntergeladenen Repository `pip install .` ausgeführt werden.

Weiters kann die Bibliothek wie folgt als *requirement* zu `requirements.txt` hinzugefügt werden:
```
mcproto @ git+https://github.com/icezyclon/mcproto-python.git@main
```

Für lokales Bauen der Bibliothek können wheel und dist mit `python -m build` nach `dist/*` gebaut werden.
Anschließend kann dann die tar Datei mit `pip install mcproto-0.0.0.0.0.tar.gz` mittels pip installiert werden.

Falls man selbst an der Bibliothek herumprobieren möchte, kann man das Repository als [git submodule](https://git-scm.com/book/en/v2/Git-Tools-Submodules) klonen.

## Todos

Die Bibliothek ist noch nicht ausgereift und es gibt noch eine Menge zu tun!

[Liste mit TODOS](TODOS.md)

## Lizenz

[LGPLv3](LICENSE)

> Notiz: Die *Absicht* hinder der gewählten Lizenz ist, dass die lizensierte Software frei *verwendet* werden darf (in der vorliegenden Form), sogar für kommerzielle oder proprietäre Projekte.
> Allerdings müssen Änderungen *an der lizensierten Software selbst* unter der selben Lizenz öffentlich gemacht werden.
> Dieser englischer [Blog](https://fossa.com/blog/open-source-software-licenses-101-lgpl-license/) erklärt die Details auf verständliche Art und Weise.
