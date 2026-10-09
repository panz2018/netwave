//! Physical constants: the single definition site, shared by every binding.
//!
//! Bindings re-export these names (Python `netwave.constants`, TS named
//! export) and MUST NOT copy the numeric literals (ironclad rules 11/12:
//! one definition, one name).

/// Speed of light in vacuum, metres per second.
///
/// Exact by SI definition: the metre is defined by fixing the speed of
/// light at exactly 299 792 458 m/s (SI Brochure, 9th edition). Being an
/// integer below 2^53, the value is representable bit-exactly in f64, so
/// every cross-end comparison of this constant is `==`, never a tolerance
/// (ironclad rule 3).
pub const SPEED_OF_LIGHT: f64 = 299_792_458.0;
