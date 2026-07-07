#!/usr/bin/env python3
"""Evaluate the RAG layer on a small labelled dataset.

Measures three things, all deterministically (no ROS2 needed):
  - retrieval accuracy: was the expected source document retrieved?
  - keyword recall:     does the answer contain the expected key term(s)?
  - refusal accuracy:   for unanswerable questions, did it refuse (say it
                        doesn't know) instead of hallucinating?

Prerequisites:
    pip install anthropic chromadb
    export ANTHROPIC_API_KEY=sk-ant-...
    # ingest the sample docs first (from the copilot_rag package dir):
    #   python3 -m copilot_rag.ingest data

Run:
    python3 eval/rag_eval.py
    python3 eval/rag_eval.py --judge      # also LLM-grade answer correctness
"""
import argparse
import json
import os
import sys
import time

# Make the standalone copilot_rag package importable without building the WS.
_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO, "ros2_copilot_ws", "src", "copilot_rag"))

from copilot_rag import config          # noqa: E402
from copilot_rag.rag_engine import RagEngine  # noqa: E402
from copilot_rag.store import VectorStore     # noqa: E402

REFUSAL_MARKERS = [
    "don't know", "do not know", "not know", "no relevant", "not contained",
    "not in the", "cannot find", "could not find", "unable to", "no information",
    "not found", "모르", "찾지 못", "없습니다",
]


def looks_like_refusal(answer: str) -> bool:
    a = answer.lower()
    return any(m in a for m in REFUSAL_MARKERS)


def load_dataset(path: str):
    with open(path, "r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Evaluate the RAG layer.")
    ap.add_argument("--dataset",
                    default=os.path.join(_REPO, "eval", "datasets", "rag_eval.jsonl"))
    ap.add_argument("--db", default=config.DEFAULT_DB_PATH)
    ap.add_argument("--collection", default=config.DEFAULT_COLLECTION)
    ap.add_argument("--model", default=config.DEFAULT_MODEL)
    ap.add_argument("--judge", action="store_true",
                    help="also LLM-grade answer correctness")
    args = ap.parse_args(argv)

    store = VectorStore(args.db, args.collection)
    if store.count() == 0:
        print("Vector store is empty. Ingest docs first:\n"
              "  cd ros2_copilot_ws/src/copilot_rag && python3 -m copilot_rag.ingest data")
        return 1
    engine = RagEngine(store, model=args.model)

    items = load_dataset(args.dataset)
    retrieval_hits = retrieval_total = 0
    keyword_hits = keyword_total = 0
    refusal_hits = refusal_total = 0
    judge_hits = judge_total = 0
    latencies = []

    if args.judge:
        from judge import grade  # noqa: E402  (eval/ dir on path)

    print(f"{'Q':<48} {'retr':<5} {'kw':<4} {'refuse':<7}")
    print("-" * 68)
    for it in items:
        t0 = time.perf_counter()
        answer, sources = engine.answer(it["question"])
        latencies.append(time.perf_counter() - t0)

        if it["unanswerable"]:
            ok = looks_like_refusal(answer)
            refusal_total += 1
            refusal_hits += int(ok)
            row_refuse = "OK" if ok else "MISS"
            row_retr = row_kw = "-"
        else:
            retrieval_total += 1
            r_ok = any(it["expected_source"] in s for s in sources)
            retrieval_hits += int(r_ok)
            row_retr = "OK" if r_ok else "MISS"

            keyword_total += 1
            a = answer.lower()
            k_ok = all(kw.lower() in a for kw in it["must_include"])
            keyword_hits += int(k_ok)
            row_kw = "OK" if k_ok else "MISS"
            row_refuse = "-"

            if args.judge:
                judge_total += 1
                passed, _ = grade(it["question"], answer, it["must_include"])
                judge_hits += int(passed)

        print(f"{it['question'][:46]:<48} {row_retr:<5} {row_kw:<4} {row_refuse:<7}")

    print("\n=== Metrics ===")
    if retrieval_total:
        print(f"retrieval accuracy : {retrieval_hits}/{retrieval_total} "
              f"({retrieval_hits / retrieval_total:.0%})")
    if keyword_total:
        print(f"keyword recall     : {keyword_hits}/{keyword_total} "
              f"({keyword_hits / keyword_total:.0%})")
    if refusal_total:
        print(f"refusal accuracy   : {refusal_hits}/{refusal_total} "
              f"({refusal_hits / refusal_total:.0%})")
    if judge_total:
        print(f"LLM-judge correct  : {judge_hits}/{judge_total} "
              f"({judge_hits / judge_total:.0%})")
    if latencies:
        print(f"avg latency        : {sum(latencies) / len(latencies):.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
