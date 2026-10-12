//! criterion benchmark placeholder (real Touchstone benchmarks arrive
//! with the compute verbs).
use criterion::{Criterion, criterion_group, criterion_main};

fn placeholder(c: &mut Criterion) {
    c.bench_function("scaffold_noop", |b| b.iter(|| 1 + 1));
}

criterion_group!(benches, placeholder);
criterion_main!(benches);
