[Deutsch 👈](README_DEUTSCH.md)

# MCPB Python Client Library

This library is designed to control a Minecraft Java Server, such as [Spigot](https://www.spigotmc.org/) or [Paper](https://papermc.io/) running the **[mcpb](https://github.com/icezyclon/mcpb) plugin**, with Python.

This library is heavily inspired by [MCPI](https://github.com/martinohanlon/mcpi) (and its corresponding plugin [RaspberryJuice](https://github.com/zhuowei/RaspberryJuice)) and attempts a more modern approach for communication between server and client that also works for more modern versions of Minecraft.

This library uses Protocol Buffers and the [gRPC](https://grpc.io/) library and protocols to communicate with the plugin on the server.

Due to the use of the new type annotations **Python 3.10+** is required!

## Versions and Compatibility

The versioning in this project looks a bit funny, but is very simple:

* The first 4 numbers of the version indicate the *plugin version* this library is compatible with.
* And the final number is this libraries patch number, which is incremented after smaller patches or quality of life changes that are independent of the plugin.

For example, the library version number `1.18.2.1.X` would require the [mcpb plugin](https://github.com/icezyclon/mcpb) version 1.18.2.1 or newer -
that is, this library *should* work for newer versions of the plugin if everything works out and no breaking changes are introduced.
On the other hand, the library will most likely not work for older versions of the plugin.

TLDR; make sure the first 4 numbers of the library version are the same as the plugin's and choose the last number as high as possible.


## Build/Install Instructions

The library is currently *not* on [PyPI](https://pypi.org/). The package may be published there in the future.

You may instead install this package directly by using `pip install git+https://github.com/icezyclon/mcpb-python.git@main` to install it directly from Github (`git` is required for this).
If you cloned the repository already then `pip install .` can be used.

The library can be added as a *requirement* to `requirements.txt` like so:
```
mcpb @ git+https://github.com/icezyclon/mcpb-python.git@main
```

Building the library locally can be done by using `python -m build`, which will build the wheel and dist packages in `dist/*`.
Afterwards the tar file can be installed with pip: `pip install mcpb-0.0.0.0.0.tar.gz`.

If you want to play around with the library itself you can also clone the repository as [git submodule](https://git-scm.com/book/en/v2/Git-Tools-Submodules).

## Todos

The entire library is very much a work-in-progress, so there is still a lot to do!

[collect TODOS](TODOS.md)

## License

[LGPLv3](LICENSE)

> Note: The *intent* behind the chosen license, is to allow the licensed software to be *used* (as is) in any type of project, even commercial or closed-source ones.
> However, changes or modifications *to the licensed software itself* must be shared via the same license openly.
> Checkout [this blog](https://fossa.com/blog/open-source-software-licenses-101-lgpl-license/) for an in-depth explanation.
