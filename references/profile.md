# Jun profile

Use this profile when the user asks for daily/weekly paper scouting tailored to Jun.

## Core interest buckets

1. Systems and storage — highest priority
   - FAST / OSDI / USENIX ATC / EuroSys flavor
   - SSD, NVMe, file systems, KV stores, LSM-trees, disaggregated storage, persistent memory
2. Computer architecture — high priority
   - HPCA-style work
   - memory systems, cache/prefetch/TLB, CXL, chiplets, accelerators
3. Hardware design automation — medium priority
   - DAC / ICCAD adjacent work when it overlaps systems/architecture/runtime
4. AI infrastructure — selective, not dominant
   - only keep when the paper is clearly about systems/runtime/serving/training infra
   - avoid generic model papers and avoid AI infra overwhelming the digest

## Retrieval policy

Prefer already-published papers from these venues when available:
- FAST
- HPCA
- DAC
- EuroSys
- OSDI
- ICCAD
- USENIX ATC

If mixing published papers with arXiv candidates:
- published venue papers should have priority lanes
- storage / FAST-flavor work gets extra weight
- AI infra should be capped to a minority share unless the user explicitly asks for more

## Ranking heuristics

Favor papers that are system-building, performance-driven, hardware/software co-design, storage/runtime, or practical infra.

Down-rank papers that are purely biomedical, generic vision, or broad surveys unless they have obvious systems relevance.

## Cost policy

For simple retrieval, filtering, ranking, formatting, and dashboard generation:
- prefer local scripts / deterministic logic
- avoid expensive model calls
- use model-based summarization only for deep paper reading when necessary

## Output style

Keep the digest sharp:
- 5-15 papers max by default
- each item should include: why it matters, likely venue-fit, and one-line take
- do not dump giant abstracts unless asked
