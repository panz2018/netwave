//! Build step: generate the Python-side `#[pyclass]` unit enums from core's
//! enum definitions. Core is the single vocabulary source (workspace-layout
//! spec); this is a mechanical extraction at build time, never a hand-copied
//! table — the same pattern as `browser/scripts/gen_values.mjs`. The generated
//! enums live in this crate (the orphan rule forbids attaching `#[pyclass]` to
//! core's types from here), and the binding converts between them and core's
//! enums through the infallible `to_core`/`From` mappings emitted here.

use std::path::{Path, PathBuf};
use std::{env, fs};

/// Read the variant names (declaration order) of a `pub enum NAME { … }` block.
/// Only bare `Variant,` lines count: doc comments and attributes are skipped,
/// so the list tracks the enum body exactly as core declares it.
fn read_variants(src: &str, name: &str) -> Vec<String> {
    let open = format!("pub enum {name} {{");
    let start = src
        .find(&open)
        .unwrap_or_else(|| panic!("build.rs: enum {name} not found in core/src/frequency.rs"));
    let body = &src[start + open.len()..];
    let close = body.find('}').expect("build.rs: unterminated enum body");
    let block = &body[..close];
    let variants: Vec<String> = block
        .lines()
        .map(|line| line.trim())
        .filter_map(|line| {
            let head = line.trim_end_matches(',').trim();
            let is_ident = !head.is_empty()
                && head != line.trim_start_matches('/')
                && head.chars().all(|c| c.is_alphanumeric() || c == '_')
                && !head.starts_with('#')
                && !head.starts_with('/');
            if is_ident {
                Some(head.to_owned())
            } else {
                None
            }
        })
        .collect();
    assert!(
        !variants.is_empty(),
        "build.rs: enum {name} has no variants"
    );
    variants
}

/// Emit one `#[pyclass]` enum plus infallible, exhaustive variant-to-variant
/// conversions between core's enum and this Python pyclass. No strings, no
/// Result: the two enums share the same variants (extracted from core), so
/// every arm maps and there is no error path to reach. The only fallible step
/// in the binding is parsing a user-supplied string, which goes straight to
/// core's `FromStr` in lib.rs (covered by a bad-string test).
fn emit_enum(name: &str, variants: &[String]) -> String {
    let decl = variants
        .iter()
        .map(|v| format!("    {v},"))
        .collect::<Vec<_>>()
        .join("\n");
    let to_core_arms = variants
        .iter()
        .map(|v| format!("            Self::{v} => Core{name}::{v},"))
        .collect::<Vec<_>>()
        .join("\n");
    let from_core_arms = variants
        .iter()
        .map(|v| format!("            Core{name}::{v} => Self::{v},"))
        .collect::<Vec<_>>()
        .join("\n");
    format!(
        "#[cfg_attr(feature = \"stub-gen\", \
         gen_stub_pyclass_enum(module = \"netwave._netwave\"))]\n\
         #[pyclass]\n\
         #[derive(Debug, Clone, Copy, PartialEq, Eq)]\n\
         #[allow(non_camel_case_types)]\n\
         pub enum {name} {{\n{decl}\n}}\n\n\
         impl {name} {{\n\
         \x20   /// Map to core's enum (exhaustive, infallible).\n\
         \x20   pub(crate) fn to_core(self) -> Core{name} {{\n\
         \x20       match self {{\n{to_core_arms}\n\x20       }}\n\
         \x20   }}\n\
         }}\n\n\
         impl From<Core{name}> for {name} {{\n\
         \x20   /// Map from core's enum (exhaustive, infallible).\n\
         \x20   fn from(value: Core{name}) -> Self {{\n\
         \x20       match value {{\n{from_core_arms}\n\x20       }}\n\
         \x20   }}\n\
         }}\n"
    )
}

fn main() {
    println!("cargo:rerun-if-changed=../core/src/frequency.rs");
    let core_src = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../core/src/frequency.rs");
    let core_src = Path::new(&core_src);
    let src = fs::read_to_string(core_src)
        .unwrap_or_else(|e| panic!("build.rs: cannot read {}: {e}", core_src.display()));

    let frequency = emit_enum("FrequencyUnit", &read_variants(&src, "FrequencyUnit"));
    let wavelength = emit_enum("WavelengthUnit", &read_variants(&src, "WavelengthUnit"));

    let out = PathBuf::from(env::var_os("OUT_DIR").expect("OUT_DIR")).join("enums.rs");
    fs::write(
        &out,
        format!(
            "// GENERATED at build time from core/src/frequency.rs — do not edit.\n\
             // Included by `src/enums.rs`, which provides the imports.\n\n\
             {frequency}\n{wavelength}"
        ),
    )
    .expect("build.rs: cannot write enums.rs");
}
