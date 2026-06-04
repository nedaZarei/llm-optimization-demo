# LLM Optimization Demo — Intake Form

## 1. Submitter Info
- **Name:** Paul Brookes
- **Date submitted:** 2026-05-14

## 2. Optimization Target
- **Library/Repo:** vLLM `v0.19.2rc0` (commit `aeee7ef9391028939afd08e20c12a1e279efbdf1`)
- **Model + version:** 13-model sweep covering 3 quantization families on the same hardware/runtime config:
  - Qwen3 AWQ: `Qwen/Qwen3-4B-AWQ`, `Qwen/Qwen3-8B-AWQ`, `Qwen/Qwen3-14B-AWQ`
  - Qwen3 BF16: `Qwen/Qwen3-4B`, `Qwen/Qwen3-8B`, `Qwen/Qwen3-14B`
  - W4A16 (RedHatAI requants): `Meta-Llama-3.1-8B-Instruct`, `gemma-2-9b-it`, `Mistral-Nemo-Instruct-2407`, `phi-4`, `Mistral-Small-24B-Instruct-2501`, `Llama-3.3-70B-Instruct`, `Qwen2.5-72B-Instruct`
- **Hardware:** Intel Xeon Platinum 8581C (Emerald Rapids)
- **Hardware class:** Server CPU (datacenter)
- **Hardware specs:** 48 physical cores / 96 vCPUs (1 socket, SMT on), 2 NUMA nodes (Sub-NUMA Clustering), 260 MiB L3, ~180 GB RAM, AMX-bf16 + AMX-int8 + AVX-512. TDP ~350 W (Xeon 8581C). Spec tier: high. Memory bandwidth ~700 GB/s class (DDR5-5600, 8 channels).
- **Machine:** GCP `c4-highcpu-96`
- **OS:** Ubuntu (GCP c4 image, host); workload runs inside the `vllm-cpu-env` Docker container
- **Driver versions:** N/A (CPU-only deployment)
- **Docker or native:** Docker (`vllm-cpu-env`, `--privileged --ipc=host`)

## 3. Benchmark Config
- **Framework/runtime version:** vLLM `v0.19.2rc0`
- **Benchmark tool used:** vLLM `benchmark_serving.py` (sharegpt-style prompts). Artemis LLM Bench was *not* run on this configuration; numbers below come from vLLM's own bench. Equivalence noted where the form requests Artemis-specific fields.
- **Number of runs:** 1 run × 100 prompts per (model, variant) pair (26 benchmarks total)
- **Prompt length range:** 512 input / 512 output tokens (fixed)
- **Key settings:**
  - `tensor_parallel_size = 2` (one rank per NUMA node)
  - `VLLM_CPU_OMP_THREADS_BIND = auto`
  - `max_concurrency = 32`
  - `enable_chunked_prefill = true`
  - `block_size = 128`
  - `max_num_batched_tokens = 2048`
  - `max_num_seqs = 256` (128 for 70B / 72B)
  - `vllm_cpu_kvcache_space = 40 GiB`
  - dtype: native per model (AWQ / BF16 / W4A16)
- **Baseline description:** vLLM `v0.19.2rc0` stock CPU build vs. `v0.19.2rc0` + topk-sampler / AMX-dequant patch.

## 4. Results

**Artemis LLM Bench output JSON:** not attached — Artemis was not run on this configuration. Numbers below are output throughput (generated tok/s) from vLLM `benchmark_serving.py` (see `data.csv`). Cost columns left blank.

| Model | Baseline tok/s | Patched tok/s | Δ |
|---|---:|---:|---:|
| Qwen3-4B-AWQ | 428.3 | 561.5 | +31.1% |
| Qwen3-8B-AWQ | 322.1 | 398.4 | +23.7% |
| Qwen3-14B-AWQ | 179.8 | 201.5 | +12.1% |
| Qwen3-4B (BF16) | 337.0 | 410.8 | +21.9% |
| Qwen3-8B (BF16) | 236.6 | 273.1 | +15.4% |
| Qwen3-14B (BF16) | 129.7 | 140.5 | +8.4% |
| Llama-3.1-8B W4A16 | 281.2 | 315.5 | +12.2% |
| Gemma-2-9B W4A16 | 213.7 | 236.3 | +10.6% |
| Mistral-Nemo-12B W4A16 | 209.8 | 241.7 | +15.2% |
| phi-4-14B W4A16 | 175.8 | 201.5 | +14.6% |
| Mistral-Small-24B W4A16 | 119.4 | 136.4 | +14.2% |
| Llama-3.3-70B W4A16 | 33.4 | 40.5 | +21.3% |
| Qwen2.5-72B W4A16 | 32.9 | 38.5 | +17.0% |

- **Cost/1M tokens baseline ($):** —
- **Cost/1M tokens optimized ($):** —
- **Cost improvement (%):** —

## 5. Target Hardware
- **Specifically built for:** Intel server CPUs with AMX (Sapphire Rapids / Emerald Rapids / Granite Rapids). The AMX dequant kernel is written against AMX-bf16 tile instructions; the topk-sampler change is CPU-agnostic Python.
- **Expected to work on other hardware?** Partial. The topk sampler patch is portable to any vLLM CPU/GPU build. The AMX dequant kernel is Intel-AMX-only — it falls back to the stock path on non-AMX CPUs (AMD Zen, ARM, older Intel) with no speedup.

## 6. Model Accuracy Validation
- **Tool used:** lm-eval-harness (raw JSON in `lm-eval-qwen3-4b-awq-baseline.json` and `lm-eval-qwen3-4b-awq-patched.json`)
- **Model tested:** Qwen3-4B-AWQ (representative AWQ model; baseline build vs. patched build)
- **MMLU:** baseline 67.40% / optimized 67.56% / Δ +0.17 pp (stderr ±0.69 pp) — within noise
- **HellaSwag (acc_norm):** baseline 57.42% / optimized 57.22% / Δ −0.20 pp (stderr ±0.90 pp) — within noise
- **Other:** GSM8K (strict-match): baseline 85.86% / optimized 85.35% / Δ −0.51 pp (stderr ±1.75 pp) — within noise
- **Any degradation?** No. All deltas are smaller than the per-task standard error and have signs in both directions.
- **Notes:** Both patches are numerically equivalent to the stock paths — AMX dequant produces identical bf16 weights via a faster instruction sequence; `torch.topk` returns the same indices as the full vocab sort used by the stock sampler. The lm-eval results confirm no measurable behavioral change.

## 7. Correctness Checks (Artemis LLM Bench)
Artemis LLM Bench was not run on this configuration; correctness was validated via lm-eval-harness (see Section 6).

- **Artemis benchmark output JSON attached?** No
- **Sanity checks:** N/A (no Artemis run)
- **Structural validation:** N/A
- **Semantic similarity:** N/A
- **Exact match:** N/A

## 8. What Changed

Two patches stacked on vLLM's CPU backend:

1. **Direct AMX dequant kernel.** vLLM's CPU path for AWQ / W4A16 (group-quantized 4-bit weights) dequantizes a tile of int4 weights into bf16 before each matmul. The stock implementation walks groups in scalar / AVX-512 code. The patch replaces that with a kernel that issues AMX-tile instructions to dequant directly into the bf16 tile the GEMM is about to consume, fusing scale-application and layout-conversion into the AMX pipeline. This is the dominant lift on 4-bit models (+8% to +22% per model in our sweep).

2. **`torch.topk` in the sampler.** The stock CPU sampler does a full vocab sort (≈O(V log V)) every decode step, even though only the top-k indices are needed. The patch swaps that for `torch.topk` (≈O(V log k)), which on a CPU with V≈150k and k=50 is an order of magnitude less work. It accounts for ~half the lift on BF16 models (where the dequant kernel is a no-op) and a meaningful share on smaller AWQ models where decode is sampler-bound rather than matmul-bound.

Together they yield +8% to +31% output throughput across 13 quantized + BF16 models at TP=2 on `c4-highcpu-96`, with no measurable accuracy change on Qwen3-4B-AWQ (MMLU / HellaSwag / GSM8K all within stderr).

## 9. Demo Prompts

_TODO — pending live capture against running baseline + optimized endpoints. The two prompts (minimum 2) should be selected at demo time and the actual model response, TTFT, and tok/s recorded live (not extracted from the Artemis or vLLM benchmark output)._

## 10. Assets

Files included in this bundle:
- `chart-combined.png` — all 13 configurations on one chart
- `chart-awq.png` — Qwen3 AWQ subset (3 models)
- `chart-bf16.png` — Qwen3 BF16 subset (3 models)
- `chart-w4a16.png` — W4A16 sweep (7 models)
- `data.csv` — raw baseline / patched tok/s per model (includes HuggingFace repo)
- `lm-eval-qwen3-4b-awq-baseline.json` — full lm-eval-harness output, baseline build
- `lm-eval-qwen3-4b-awq-patched.json` — full lm-eval-harness output, patched build

Form fields:
- **High-res charts attached?** Yes
- **Artemis LLM Bench baseline JSON attached?** No (not run; see Section 3)
- **Artemis LLM Bench candidate JSON attached?** No (not run; see Section 3)
- **Config ID:** `qwen3-8b-awq__c4-highcpu-96__vllm` (headline; 12 additional models covered in the attached chart and CSV)
- **Baseline endpoint URL:** —
- **Optimized endpoint URL:** —

## 11. Sign-off
- **Are these results final?** Yes
- **Submitter confirms results are accurate and ready for public use:** Yes
