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
    // Touchstone cross-compare: parse each shared sample and dump the S
    // master data (interleaved f64), z0, and version. The same files are
    // read by every end; native ends must match core bit-exact, wasm within
    // relative tolerance.
    use netwave::touchstone::Touchstone;
    for case in ["s1p", "s2p", "s4p"] {
        let p = format!("testdata/touchstone/dut.{case}");
        let text = std::fs::read_to_string(&p).unwrap();
        let ts = Touchstone::from_text(&text, None, Some(&p)).unwrap();
        let sbytes: &[u8] =
            unsafe { std::slice::from_raw_parts(ts.s().as_ptr() as *const u8, ts.s().len() * 8) };
        std::fs::File::create(std::path::Path::new(&out).join(format!("core_ts_{case}.bin")))?
            .write_all(sbytes)?;
        let zbytes: &[u8] =
            unsafe { std::slice::from_raw_parts(ts.z0().as_ptr() as *const u8, ts.z0().len() * 8) };
        std::fs::File::create(std::path::Path::new(&out).join(format!("core_ts_{case}_z0.bin")))?
            .write_all(zbytes)?;
        std::fs::write(
            std::path::Path::new(&out).join(format!("core_ts_{case}_version.txt")),
            ts.version(),
        )?;
    }
    println!(
        "dumped {} {}",
        std::fs::canonicalize(&path)?.display(),
        std::fs::canonicalize(&fpath)?.display()
    );
    Ok(())
}
