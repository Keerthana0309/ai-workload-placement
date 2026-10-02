"""
AI Workload Placement — Decision Engine (v1)
==============================================
Asks a few quick questions about your AI workload and recommends where to
run it (device/local vs. cloud) and why — based on real benchmark data
(local llama3.2:1b vs. cloud Claude Haiku 4.5 on summarization) plus
reasonable defaults for other cases.

This is v1: simple rule-based logic, not a model. The goal is a fast,
no-commitment answer — not a platform.

HOW TO RUN:
    python3 decide.py
"""


def ask(prompt, options):
    """Ask a question with a fixed set of valid answers."""
    opts_str = "/".join(options)
    while True:
        answer = input(f"{prompt} ({opts_str}): ").strip().lower()
        if answer in options:
            return answer
        print(f"  Please enter one of: {opts_str}")


def decide(task_type, privacy, latency, connectivity, budget):
    """
    Returns (recommendation, reason).
    Priority order: hard constraints first, then preferences.
    """

    # 1. Hard constraints — no real choice here
    if privacy == "high":
        return (
            "LOCAL / DEVICE",
            "Privacy requirement is high — data can't leave the device/org, "
            "so cloud is off the table regardless of other factors."
        )

    if connectivity == "offline":
        return (
            "LOCAL / DEVICE",
            "Connectivity is unreliable or offline — cloud inference isn't "
            "viable without a stable connection."
        )

    # 2. Complex reasoning tasks generally need a bigger model than
    #    what's practical to run locally on typical hardware
    if task_type == "complex" and budget != "free":
        return (
            "CLOUD",
            "Task requires complex reasoning — small local models "
            "(like llama3.2:1b) aren't strong enough for this yet, and "
            "budget allows for a cloud-hosted model."
        )

    # 3. Strict latency + reliable connection — real data showed cloud
    #    can actually beat local on latency for simple tasks
    if latency == "strict" and connectivity == "reliable":
        return (
            "CLOUD",
            "Latency tolerance is strict and connectivity is reliable. "
            "Benchmark data (local llama3.2:1b vs. cloud Haiku 4.5 on "
            "summarization) showed cloud was actually faster on average "
            "(~1.2s vs ~2.6s) for this kind of simple task — a real, "
            "non-obvious finding worth trusting over the 'local is always "
            "faster' assumption."
        )

    # 4. Free/minimal budget + simple task — local is free and good enough
    if budget == "free" and task_type == "simple":
        return (
            "LOCAL / DEVICE",
            "Task is simple and budget is free/minimal — a small local "
            "model handles this well at zero marginal cost per request."
        )

    # 5. Default — cloud, given comparable latency + trivial cost in testing
    return (
        "CLOUD",
        "No hard constraints pushing toward local, and benchmark data "
        "showed cloud offers comparable or better latency at trivial "
        "cost (~$0.0001/request) for simple tasks. Default to cloud "
        "unless you have a specific reason to stay local."
    )


def main():
    print("=" * 60)
    print("AI Workload Placement — Decision Engine (v1)")
    print("=" * 60)
    print("Answer a few quick questions about your workload.\n")

    task_type = ask("Task type", ["simple", "complex"])
    privacy = ask("Privacy requirement", ["low", "high"])
    latency = ask("Latency tolerance", ["strict", "normal", "relaxed"])
    connectivity = ask("Connectivity", ["reliable", "offline"])
    budget = ask("Budget", ["free", "flexible"])

    recommendation, reason = decide(task_type, privacy, latency, connectivity, budget)

    print("\n" + "=" * 60)
    print(f"RECOMMENDATION: {recommendation}")
    print("=" * 60)
    print(f"\nWhy: {reason}\n")


if __name__ == "__main__":
    main()
