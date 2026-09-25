//! cross-binding dump (core side): emit the (2,2) roundtrip values to
//! <out>/core.bin — raw little-endian f64 bytes, re/im interleaved.
//! Binary rather than JSON: JSON writes -0 as 0 and loses the sign bit.
//! Usage: cargo run -p netwave --example dump <out_dir>
use std::io::Write;

fn main() -> std::io::Result<()> {
    let out = std::env::args().nth(1).expect("usage: dump <out_dir>");
    std::fs::create_dir_all(&out)?;
    let v = netwave::fill_pattern(2, 2);
    // Complex64 = #[repr(C)] {re: f64, im: f64}; write the whole block as
    // a little-endian f64 sequence.
    let bytes: &[u8] = unsafe { std::slice::from_raw_parts(v.as_ptr() as *const u8, v.len() * 16) };
    let mut f = std::fs::File::create(format!("{out}/core.bin"))?;
    f.write_all(bytes)?;
    println!("dumped core.bin");
    Ok(())
}
