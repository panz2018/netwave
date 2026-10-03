"""netwave: network scattering-parameter math.

Public package. The compiled Rust extension lives in the hidden submodule
`netwave._netwave` (mixed maturin layout); this shell re-exports it so the
public import surface is just `netwave`. The `_` prefix marks the extension
as an implementation detail — import `netwave`, never `netwave._netwave`.
"""

from . import _netwave
from ._netwave import *  # noqa: F403

__doc__ = _netwave.__doc__
if hasattr(_netwave, "__all__"):
    __all__ = _netwave.__all__
