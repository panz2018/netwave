//! criterion benchmark placeholder (task 2.3; real fill_pattern benchmarks
//! arrive with the phase-2 data model).
use criterion::{Criterion, criterion_group, criterion_main};

fn placeholder(c: &mut Criterion) {
    c.bench_function("scaffold_noop", |b| b.iter(|| 1 + 1));
}

criterion_group!(benches, placeholder);
criterion_main!(benches);
