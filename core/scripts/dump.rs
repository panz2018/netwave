//! cross-binding dump (core side): emit the (2,2) roundtrip values to
//! <out>/core.bin — raw little-endian f64 bytes, re/im interleaved.
//! Binary rather than JSON: JSON writes -0 as 0 and loses the sign bit.
//! Usage: cargo run -p netwave --example dump <out_dir> (declared in
//! core/Cargo.toml [[example]] with path = "scripts/dump.rs")
use std::io::Write;

fn main() -> std::io::Result<()> {
    let out = std::env::args().nth(1).expect("usage: dump <out_dir>");
    std::fs::create_dir_all(&out)?;
    let v = netwave::fill_pattern(2, 2);
    // Complex64 = #[repr(C)] {re: f64, im: f64}; write the whole block as
    // a little-endian f64 sequence.
    let bytes: &[u8] = unsafe { std::slice::from_raw_parts(v.as_ptr() as *const u8, v.len() * 16) };
    let path = std::path::Path::new(&out).join("core.bin");
    let mut f = std::fs::File::create(&path)?;
    f.write_all(bytes)?;
    // λ↔f round-trip axis: f -> wavelength -> f,
    // dumped so the four ends compare (native bit-exact, wasm within tol).
    use netwave::frequency::{Frequency, FrequencyUnit, WavelengthUnit};
    let f0 = Frequency::from_f(vec![1.0, 2.0, 5.0], FrequencyUnit::GHz);
    let wl = f0.wavelength(WavelengthUnit::mm, 2.2).unwrap();
    let back = Frequency::from_wavelength(wl, WavelengthUnit::mm, 2.2);
    let axis = back.f().unwrap();
    let fbytes: &[u8] =
        unsafe { std::slice::from_raw_parts(axis.as_ptr() as *const u8, axis.len() * 8) };
    let fpath = std::path::Path::new(&out).join("core_freq.bin");
    std::fs::File::create(&fpath)?.write_all(fbytes)?;
    println!(
        "dumped {} {}",
        std::fs::canonicalize(&path)?.display(),
        std::fs::canonicalize(&fpath)?.display()
    );
    Ok(())
}
