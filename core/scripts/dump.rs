//! cross-binding dump (core side): emit the λ↔f axis and the Touchstone
//! S master data per sample to <out>/core/freq.bin and
//! <out>/core/<sample>/s.bin|z0.bin|version.txt — raw little-endian f64
//! bytes, re/im interleaved. Binary rather than JSON: JSON writes -0 as 0
//! and loses the sign bit.
//! Usage: cargo run -p netwave --example dump <out_dir> (declared in
//! core/Cargo.toml [[example]] with path = "scripts/dump.rs")
use std::io::Write;

fn main() -> std::io::Result<()> {
    let out = std::env::args().nth(1).expect("usage: dump <out_dir>");
    std::fs::create_dir_all(&out)?;
    // λ↔f round-trip axis: f -> wavelength -> f,
    // dumped so the four ends compare (native bit-exact, wasm within tol).
    use netwave::frequency::{Frequency, FrequencyUnit, WavelengthUnit};
    let f0 = Frequency::from_f(vec![1.0, 2.0, 5.0], FrequencyUnit::GHz);
    let wl = f0.wavelength(WavelengthUnit::mm, 2.2).unwrap();
    let back = Frequency::from_wavelength(wl, WavelengthUnit::mm, 2.2);
    let axis = back.f().unwrap();
    let fbytes: &[u8] =
        unsafe { std::slice::from_raw_parts(axis.as_ptr() as *const u8, axis.len() * 8) };
    let core_dir = std::path::Path::new(&out).join("core");
    std::fs::create_dir_all(&core_dir)?;
    let fpath = core_dir.join("freq.bin");
    std::fs::File::create(&fpath)?.write_all(fbytes)?;
    // Touchstone cross-compare: parse each shared sample and dump the S
    // master data (interleaved f64), z0, and version. The same files are
    // read by every end; native ends must match core bit-exact, wasm within
    // relative tolerance.
    use netwave::touchstone::Touchstone;
    for case in ["s1p", "s2p", "s4p"] {
        let p = format!("oracle/samples/dut.{case}");
        let text = std::fs::read_to_string(&p).unwrap();
        let ts = Touchstone::from_text(&text, None, Some(&p)).unwrap();
        let sample_dir = core_dir.join(format!("dut.{case}"));
        std::fs::create_dir_all(&sample_dir)?;
        let sbytes: &[u8] =
            unsafe { std::slice::from_raw_parts(ts.s().as_ptr() as *const u8, ts.s().len() * 8) };
        std::fs::File::create(sample_dir.join("s.bin"))?.write_all(sbytes)?;
        let zbytes: &[u8] =
            unsafe { std::slice::from_raw_parts(ts.z0().as_ptr() as *const u8, ts.z0().len() * 8) };
        std::fs::File::create(sample_dir.join("z0.bin"))?.write_all(zbytes)?;
        std::fs::write(sample_dir.join("version.txt"), ts.version())?;
    }
    println!("dumped {}", std::fs::canonicalize(&fpath)?.display());
    Ok(())
}
