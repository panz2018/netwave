"""Physical constants: a thin re-export of the compiled core.

The single definition site is core `constants.rs`; this module only carries
the name across the package boundary (ironclad rules 11/12 — one value, one
name). Import `netwave.constants`, never `netwave._netwave`.
"""

from ._netwave import SPEED_OF_LIGHT

__all__ = ["SPEED_OF_LIGHT"]
