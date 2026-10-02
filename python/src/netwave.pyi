"""Type stubs for the netwave extension module."""

import numpy as np
import numpy.typing as npt

def fill_pattern(nfreq: int, nports: int) -> npt.NDArray[np.complex128]: ...
def read_element(arr: npt.NDArray[np.complex128], idx: int) -> tuple[float, float]: ...
