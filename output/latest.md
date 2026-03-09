# Paper Radar Digest

- window: last 7 days
- shown: 12

## 精读样板

- WiscKey 精读样板：见 `wisckey-analysis.html`

## 顶会 / 经典白名单池

### 白名单-1. WiscKey: Separating Keys from Values in SSD-Conscious Storage
- venue: FAST 2016；storage, kv, lsm
- tags: FAST-style
- take: 键值分离的代表作，LSM/SSD 方向绕不过去。

### 白名单-2. Monkey: Optimal Navigable Key-Value Store
- venue: SIGMOD 2017；storage, lsm, filters
- tags: FAST-style
- take: LSM 读放大与布隆过滤器分配的经典工作。

### 白名单-3. PebblesDB: Building Key-Value Stores using Fragmented Log-Structured Merge Trees
- venue: SOSP 2017；storage, kv, lsm
- tags: FAST-style
- take: LSM 结构改造的代表作，适合和 WiscKey 对照着看。

### 白名单-4. Titan: A High-Performance Remote-Swap System
- venue: FAST 2020；storage, memory, systems
- tags: FAST-style, HPCA-style, OSDI/ATC/EuroSys-style
- take: FAST 味很正，系统与存储交叉。

### 白名单-5. Design Tradeoffs for SSD Performance
- venue: USENIX ATC 2008；storage, ssd
- tags: FAST-style
- take: SSD 设计空间的老经典。

### 白名单-6. Learned Cache Replacement for Datacenter Storage Systems
- venue: OSDI 2020；storage, systems, cache
- tags: FAST-style, OSDI/ATC/EuroSys-style
- take: 系统味较强，数据中心存储方向。

### 白名单-7. The Tail at Scale
- venue: CACM 2013；systems, datacenter, latency
- tags: OSDI/ATC/EuroSys-style
- take: 系统性能分析与延迟思维的必读经典。

### 白名单-8. A Case for Tiny Tasks in Compute Clusters
- venue: HotOS 2013；systems, datacenter
- tags: OSDI/ATC/EuroSys-style
- take: 系统基础设施调度思路的经典小文。

### 白名单-9. Optimizing Datacenter Performance via CXL-Aware Memory Tiering
- venue: HPCA 2024；architecture, memory, cxl
- tags: HPCA-style
- take: 偏你感兴趣的内存/架构/CXL 路线。

### 白名单-10. BetrFS: A Right-Optimized Write-Optimized File System
- venue: FAST 2015；storage, filesystem
- tags: FAST-style
- take: 写优化文件系统的代表性工作。

### 白名单-11. SILK: Preventing Latency Spikes in Log-Structured Merge Key-Value Stores
- venue: FAST 2019；storage, kv, lsm
- tags: FAST-style
- take: LSM 延迟毛刺问题，非常贴近工程痛点。

### 白名单-12. LOCATOR: A Key-Value Store for Hybrid-Cloud Workloads
- venue: FAST 2023；storage, systems, kv
- tags: FAST-style, OSDI/ATC/EuroSys-style
- take: 更现代的存储系统视角。

### 白名单-13. Tpp: Transparent Page Placement for CXL-Enabled Tiered-Memory
- venue: HPCA 2024；architecture, memory, cxl
- tags: HPCA-style
- take: CXL 分层内存方向，挺对你胃口。

### 白名单-14. RowClone: Fast and Energy-Efficient In-DRAM Bulk Data Copy and Initialization
- venue: MICRO 2013；architecture, memory
- tags: HPCA-style
- take: 内存系统经典，适合和现代 memory tiering 一起看。

### 白名单-15. SoftMC: A Flexible and Practical Open-Source Infrastructure for Enabling Experimental DRAM Studies
- venue: HPCA 2017；architecture, memory
- tags: HPCA-style
- take: 偏架构实验基础设施，味道很正。

## Zotero 经典相关论文

### 经典-1. WiscKey: Separating Keys from Values in SSD-Conscious Storage
- score: 35
- tags: FAST-style
- why: FAST-style；来自 Zotero 现有论文池
- take: 这类更像你的长期主线，适合精读和做研究借鉴。

### 经典-2. HotRAP: Hot Record Retention and Promotion for LSM-trees with Tiered Storage
- score: 31
- tags: FAST-style, HPCA-style
- why: FAST-style；HPCA-style；来自 Zotero 现有论文池
- take: 这类更像你的长期主线，适合精读和做研究借鉴。

### 经典-3. SimpleSSD: Modeling Solid State Drives for Holistic System Simulation
- score: 30
- tags: FAST-style, HPCA-style, Systems
- why: FAST-style；HPCA-style；Systems；来自 Zotero 现有论文池
- take: 这类更像你的长期主线，适合精读和做研究借鉴。

## 必看

### 必看-1. MoEless: Efficient MoE LLM Serving via Serverless Computing
- score: 50
- tags: OSDI/ATC/EuroSys-style, DAC/ICCAD-style, AI Infra
- why: +5 latency；+8 serving；+7 inference；+10 llm serving；+6 moe；+3 recent；canon:Titan: A High-Performance Remote-Swap System / The Tail at Scale / BetrFS: A Right-Optimized Write-Optimized File System
- take: 算是 AI infra 里比较像系统活的，能看。
- link: https://arxiv.org/abs/2603.06350v1

### 必看-2. Tiny, Hardware-Independent, Compression-based Classification
- score: 38
- tags: FAST-style, OSDI/ATC/EuroSys-style, AI Infra
- why: +8 storage；+4 zotero:storage；+3 recent；canon:PebblesDB: Building Key-Value Stores using Fragmented Log-Structured Merge Trees / Titan: A High-Performance Remote-Swap System / A Case for Tiny Tasks in Compute Clusters
- take: 存储味比较正，先看 bottleneck 有没有抓对。
- link: https://arxiv.org/abs/2603.06359v1

## 可扫

### 可扫-1. Semantics-Aware Caching for Concept Learning
- score: 24
- tags: HPCA-style, OSDI/ATC/EuroSys-style
- why: +5 cache；+3 recent
- take: 偏内存/架构味，值得看是不是有真货而不是只会画图。
- link: https://arxiv.org/abs/2603.06506v1

### 可扫-2. FlashPrefill: Instantaneous Pattern Discovery and Thresholding for Ultra-Fast Long-Context Prefilling
- score: 24
- tags: FAST-style
- why: +5 latency；+3 recent；canon:The Tail at Scale / SoftMC: A Flexible and Practical Open-Source Infrastructure for Enabling Experimental DRAM Studies
- take: 先扫摘要和实验，别被标题党骗了。
- link: https://arxiv.org/abs/2603.06199v1

### 可扫-3. Provuse: Platform-Side Function Fusion for Performance and Efficiency in FaaS Environments
- score: 22
- tags: OSDI/ATC/EuroSys-style
- why: +5 latency；+3 recent；+2 cat:cs.DC；canon:Titan: A High-Performance Remote-Swap System / The Tail at Scale / A Case for Tiny Tasks in Compute Clusters
- take: 先扫摘要和实验，别被标题党骗了。
- link: https://arxiv.org/abs/2603.06170v1

### 可扫-4. Efficient Vector Search in the Wild: One Model for Multi-K Queries
- score: 18
- tags: AI Infra
- why: +5 latency；+8 serving；+3 recent；canon:Monkey: Optimal Navigable Key-Value Store / Titan: A High-Performance Remote-Swap System / Learned Cache Replacement for Datacenter Storage Systems
- take: AI infra 方向，但得警惕是不是只是模型套壳。
- link: https://arxiv.org/abs/2603.06159v1

### 可扫-5. CLoPA: Continual Low Parameter Adaptation of Interactive Segmentation for Medical Image Annotation
- score: 16
- tags: HPCA-style, AI Infra
- why: +5 cache；+7 inference；-8 medical image；+3 recent
- take: 偏内存/架构味，值得看是不是有真货而不是只会画图。
- link: https://arxiv.org/abs/2603.06426v1

### 可扫-6. Adapter-Augmented Bandits for Online Multi-Constrained Multi-Modal Inference Scheduling
- score: 15
- tags: OSDI/ATC/EuroSys-style, AI Infra
- why: +7 inference；+3 recent；canon:Titan: A High-Performance Remote-Swap System / SoftMC: A Flexible and Practical Open-Source Infrastructure for Enabling Experimental DRAM Studies
- take: AI infra 方向，但得警惕是不是只是模型套壳。
- link: https://arxiv.org/abs/2603.06403v1

### 可扫-7. EvoESAP: Non-Uniform Expert Pruning for Sparse MoE
- score: 14
- tags: AI Infra
- why: +5 throughput；+6 moe；+3 recent；canon:Titan: A High-Performance Remote-Swap System / Optimizing Datacenter Performance via CXL-Aware Memory Tiering / SoftMC: A Flexible and Practical Open-Source Infrastructure for Enabling Experimental DRAM Studies
- take: 偏内存/架构味，值得看是不是有真货而不是只会画图。
- link: https://arxiv.org/abs/2603.06003v1

## 先别看

### 先别看-1. Whisper-CD: Accurate Long-Form Speech Recognition using Multi-Negative Contrastive Decoding
- score: 10
- tags: DAC/ICCAD-style, AI Infra
- why: +5 throughput；+7 inference；+3 recent；canon:PebblesDB: Building Key-Value Stores using Fragmented Log-Structured Merge Trees / Titan: A High-Performance Remote-Swap System / Learned Cache Replacement for Datacenter Storage Systems
- take: AI infra 方向，但得警惕是不是只是模型套壳。
- link: https://arxiv.org/abs/2603.06193v1

### 先别看-2. COLD-Steer: Steering Large Language Models via In-Context One-step Learning Dynamics
- score: 10
- tags: OSDI/ATC/EuroSys-style, AI Infra
- why: +7 inference；+3 recent；canon:RowClone: Fast and Energy-Efficient In-DRAM Bulk Data Copy and Initialization
- take: AI infra 方向，但得警惕是不是只是模型套壳。
- link: https://arxiv.org/abs/2603.06495v1

### 先别看-3. An Integrated Failure and Threat Mode and Effect Analysis (FTMEA) Framework with Quantified Cross-Domain Correlation Factors for Automotive Semiconductors
- score: 9
- tags: General Systems
- why: +3 recent；+2 cat:cs.AR；canon:WiscKey: Separating Keys from Values in SSD-Conscious Storage / PebblesDB: Building Key-Value Stores using Fragmented Log-Structured Merge Trees / Titan: A High-Performance Remote-Swap System
- take: 先扫摘要和实验，别被标题党骗了。
- link: https://arxiv.org/abs/2603.06299v1
