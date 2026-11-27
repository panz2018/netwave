//! Python-side unit enums, mechanically generated at build time from core's
//! enum definitions by `build.rs` (core is the single vocabulary source — never
//! a hand-copied table). The generated bodies live in `OUT_DIR/enums.rs` and
//! are included here; this module owns the imports they reference.

use netwave::frequency::FrequencyUnit as CoreFrequencyUnit;
use netwave::frequency::WavelengthUnit as CoreWavelengthUnit;
use pyo3::prelude::pyclass;

#[cfg(feature = "stub-gen")]
use pyo3_stub_gen::derive::gen_stub_pyclass_enum;

include!(concat!(env!("OUT_DIR"), "/enums.rs"));
