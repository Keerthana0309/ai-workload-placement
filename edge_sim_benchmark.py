"""
Local vs Cloud Benchmark — Workload Placement Decision Tool
=============================================================
Compares a small local model (via Ollama) against a cloud model (via AWS
Bedrock) on a simple summarization task. Logs latency, a rough quality
rating (you fill this in after reading the outputs), and cost.

SETUP (one-time):
------------------
1. Install Ollama:        https://ollama.com (or `brew install ollama` on Mac)
2. Start it:               ollama serve   (often runs automatically after install)
3. Pull a small model:     ollama pull llama3.2:1b
4. Install Python deps:    pip install requests boto3 --break-system-packages
5. Make sure your AWS credentials are configured (same creds you use for
   Bedrock at work) — e.g. via `aws configure` or environment variables.
6. Confirm you have model access enabled for a Bedrock model in your AWS
   account (e.g. Anthropic Claude Haiku) — check the Bedrock console >
   Model access.

HOW TO RUN:
-----------
1. Edit the TEXTS list below — paste in your 5 short paragraphs.
2. Edit BEDROCK_MODEL_ID if you're using a different model than the default.
3. Run:   python3 benchmark.py
4. Read the printed table + full outputs, and fill in your own "quality"
   judgment (good/ok/bad) for each — the script can't judge quality for you.
5. Copy the results into your Notion Day-9/10 experiment log.
"""

import time
import json
import requests
import boto3

# ---------------------------------------------------------------------------
# 1. EDIT THIS: paste 5 short paragraphs (news snippets, emails, anything)
# ---------------------------------------------------------------------------
TEXTS = [
    """NASA's Artemis II mission, set to carry four astronauts around the Moon,
    completed a major pre-launch milestone this week as engineers finished
    stacking the core stage of the Space Launch System rocket. The mission
    will be the first crewed flight to the Moon since Apollo 17 in 1972.
    Officials said the flight is on track for a launch window early next
    year, pending final safety reviews. The crew has spent the past several
    months training in simulators that replicate the spacecraft's systems
    and emergency procedures.""",

    """A new study published this week found that cities investing in
    protected bike lanes saw a 40 percent increase in cycling commuters
    within two years of construction. Researchers tracked traffic patterns
    across twelve mid-sized American cities and found that physically
    separated lanes, rather than painted lines alone, were the strongest
    predictor of increased ridership. The study's authors noted that safety
    perception, not just actual safety, played a major role in whether
    residents chose to bike to work.""",

    """The Federal Reserve held interest rates steady at its latest meeting,
    citing mixed signals in the labor market and continued progress on
    inflation. Officials indicated they would closely monitor upcoming
    economic data before making further moves. Markets had largely
    anticipated the decision, though some analysts had expected hints of a
    rate cut later this year. The Fed chair reiterated that future policy
    would remain data-dependent rather than following a preset path.""",

    """A small coastal town in Maine has become an unlikely hub for oyster
    farming startups, with three new aquaculture companies launching in the
    past year alone. Local fishermen, facing declining lobster catches due
    to warming waters, have increasingly turned to oyster cultivation as a
    more stable source of income. The town's harbor now hosts over a dozen
    floating oyster cages, and nearby restaurants have begun featuring
    locally farmed oysters on their menus.""",

    """Researchers at a university robotics lab unveiled a new type of soft
    robotic gripper this week, designed to handle fragile objects like fruit
    and glassware without causing damage. The gripper uses flexible silicone
    fingers combined with pressure sensors that adjust grip strength in
    real time. The team says the technology could be especially useful in
    warehouse automation and food packaging, where current rigid robotic
    arms often struggle with delicate items.""",
]

PROMPT_TEMPLATE = "Summarize the following text in 1-2 sentences:\n\n{text}"

# ---------------------------------------------------------------------------
# Config — adjust if needed
# ---------------------------------------------------------------------------
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:1b"

BEDROCK_MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"  # confirmed inference profile ID
BEDROCK_REGION = "us-east-1"  # adjust to your region
AWS_PROFILE = "workload-placement"  # named profile created via `aws configure --profile workload-placement`


# ---------------------------------------------------------------------------
# Local model call (Ollama)
# ---------------------------------------------------------------------------
def run_local(text: str, simulate_edge: bool = False) -> dict:
    """
    simulate_edge=True constrains the model to fewer CPU threads, as a rough
    (not rigorous) stand-in for weaker edge-class hardware like a Raspberry
    Pi, when real edge hardware isn't available to test on yet.
    """
    prompt = PROMPT_TEMPLATE.format(text=text)
    start = time.time()
    try:
        payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
        if simulate_edge:
            # Limit threads to approximate constrained edge hardware.
            payload["options"] = {"num_thread": 1}
        resp = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        elapsed = time.time() - start
        return {
            "output": data.get("response", "").strip(),
            "latency_sec": round(elapsed, 2),
            "cost_usd": 0.0,  # local inference — no per-request API cost
            "error": None,
        }
    except Exception as e:
        return {"output": None, "latency_sec": None, "cost_usd": 0.0, "error": str(e)}


# ---------------------------------------------------------------------------
# Cloud model call (AWS Bedrock)
# ---------------------------------------------------------------------------
def run_cloud(text: str) -> dict:
    prompt = PROMPT_TEMPLATE.format(text=text)
    session = boto3.Session(profile_name=AWS_PROFILE)
    client = session.client("bedrock-runtime", region_name=BEDROCK_REGION)

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 150,
        "messages": [{"role": "user", "content": prompt}],
    }

    start = time.time()
    try:
        resp = client.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps(body),
        )
        elapsed = time.time() - start
        result = json.loads(resp["body"].read())
        output_text = result["content"][0]["text"].strip()

        # Rough cost estimate for Claude Haiku-class pricing (approx,
        # check current AWS Bedrock pricing page for exact numbers):
        # ~$0.25 / 1M input tokens, ~$1.25 / 1M output tokens
        input_tokens = result.get("usage", {}).get("input_tokens", 0)
        output_tokens = result.get("usage", {}).get("output_tokens", 0)
        est_cost = (input_tokens * 0.25 + output_tokens * 1.25) / 1_000_000

        return {
            "output": output_text,
            "latency_sec": round(elapsed, 2),
            "cost_usd": round(est_cost, 6),
            "error": None,
        }
    except Exception as e:
        return {"output": None, "latency_sec": None, "cost_usd": None, "error": str(e)}


# ---------------------------------------------------------------------------
# Run the benchmark
# ---------------------------------------------------------------------------
def main():
    results = []

    for i, text in enumerate(TEXTS, start=1):
        print(f"\n=== Example {i} ===")
        print("Running local model (full power)...")
        local = run_local(text, simulate_edge=False)
        print("Running local model (edge-simulated, 1 thread)...")
        edge = run_local(text, simulate_edge=True)
        print("Running cloud model...")
        cloud = run_cloud(text)

        results.append({"example": i, "local": local, "edge": edge, "cloud": cloud})

        print(f"\n--- Local/Device ({OLLAMA_MODEL}, full power) ---")
        if local["error"]:
            print(f"ERROR: {local['error']}")
        else:
            print(f"Latency: {local['latency_sec']}s | Cost: ${local['cost_usd']}")
            print(f"Output: {local['output']}")

        print(f"\n--- Edge-simulated ({OLLAMA_MODEL}, 1 thread) ---")
        if edge["error"]:
            print(f"ERROR: {edge['error']}")
        else:
            print(f"Latency: {edge['latency_sec']}s | Cost: ${edge['cost_usd']}")
            print(f"Output: {edge['output']}")

        print(f"\n--- Cloud ({BEDROCK_MODEL_ID}) ---")
        if cloud["error"]:
            print(f"ERROR: {cloud['error']}")
        else:
            print(f"Latency: {cloud['latency_sec']}s | Cost: ${cloud['cost_usd']}")
            print(f"Output: {cloud['output']}")

    # Summary table
    print("\n\n=== SUMMARY TABLE (Local / Edge-simulated / Cloud) ===")
    print(f"{'#':<3} {'Local':<10} {'Edge(sim)':<12} {'Cloud':<10} {'Local $':<10} {'Cloud $':<10}")
    for r in results:
        l, e, c = r["local"], r["edge"], r["cloud"]
        print(
            f"{r['example']:<3} "
            f"{str(l['latency_sec']) + 's':<10} "
            f"{str(e['latency_sec']) + 's':<12} "
            f"{str(c['latency_sec']) + 's':<10} "
            f"${l['cost_usd']:<9} "
            f"${c['cost_usd']}"
        )
    print(
        "\nNote: 'Edge(sim)' approximates weaker edge-class hardware by "
        "limiting the local model to 1 CPU thread — a rough stand-in, not "
        "real edge hardware (e.g. Raspberry Pi) testing."
    )

    print(
        "\nNext: read the full outputs above and rate quality yourself "
        "(good/ok/bad) for each — paste all of this into your Notion "
        "Day-9/10 experiment log."
    )

    # Save raw results to a file too, for reference
    with open("benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nFull results also saved to benchmark_results.json")


if __name__ == "__main__":
    main()
