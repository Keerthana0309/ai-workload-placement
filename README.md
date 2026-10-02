# AI Workload Placement — Decision Engine

**Core question:** Given an AI workload, where should it run — device, edge, or cloud — and which model should it use to meet quality, privacy, latency, cost, energy, and hardware requirements?

This isn't a claim to have invented edge/cloud AI — that space is mature, with solid tools like RunAnywhere, AWS Greengrass, and Azure IoT Edge already solving deployment and fleet management. What's missing is a **fast, no-commitment decision layer**: something that tells you where a workload *should* run before you commit to any SDK, platform, or hardware. That's the gap this project explores.

## What's here

- **`decide.py`** — a CLI decision engine. Answer 5 quick questions about your workload (task type, privacy, latency tolerance, connectivity, budget) and get a recommendation (local/device vs. cloud) with reasoning grounded in real benchmark data.
- **`app.py`** — the same decision engine as a simple Streamlit web app, for easier demoing.
- **`benchmark.py`** — the script used to generate the benchmark data below. Runs the same summarization task through a local model (via Ollama), an edge-simulated run (thread-limited, as a rough stand-in for weaker hardware), and a cloud model (via AWS Bedrock).
- **`placement_benchmark_results.xlsx`** — full results from the benchmark run.

## What I found (first benchmark, Oct 2026)

Task: summarize 5 short news-style paragraphs.
- **Local** (llama3.2:1b, laptop, full power): ~2.9–5.3s per request, $0 cost.
- **Edge-simulated** (same model, 1 CPU thread): ~3.5–4.7s per request, $0 cost.
- **Cloud** (Claude Haiku 4.5 via Bedrock): ~1.1–1.5s per request, ~$0.0001–0.00015 per request.

**The surprising part:** cloud was consistently *faster* than local for this task — not the "local always wins on latency" assumption I went in with. Cost was also trivially small at this scale. The real tradeoff in this data wasn't latency or cost — it was privacy and offline capability, which only local/edge can offer.

**Caveat on the edge numbers:** "edge-simulated" limits CPU threads on a laptop to approximate weaker hardware — it is *not* a real test on constrained-memory/constrained-power edge hardware like a Raspberry Pi. That's a planned next step (I have a Pi from earlier research I need to dig out).

## How to run it

### Decision engine (CLI)
```bash
python3 decide.py
```

### Decision engine (web UI)
```bash
pip install streamlit
streamlit run app.py
```

### Benchmark (reproduce the results yourself)
Requires [Ollama](https://ollama.com) with `llama3.2:1b` pulled, and AWS credentials with Bedrock access.
```bash
ollama pull llama3.2:1b
pip install requests boto3
python3 benchmark.py
```

## Why I'm building this

I did research on edge/cloud workload placement back in 2017 (Raspberry Pi, networking, device control), and now work in cloud/infrastructure engineering with hands-on AWS/Azure/Bedrock experience. This project uses that background as a starting point for exploring how AI workloads specifically should be placed — not a rehash of the old research, but a current take on the same underlying question.

This is an early-stage exploration, not a finished product. Feedback, questions, and pushback are welcome.

## What's next

- Real edge hardware testing (Raspberry Pi, not just simulated)
- Expand model/task coverage beyond summarization
- Possibly: cost/latency estimation before you even run anything, based on workload description alone
