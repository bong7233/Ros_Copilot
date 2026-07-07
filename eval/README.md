# eval — Phase 5: measuring the system

"It works" isn't enough for a portfolio — prove it with numbers.

| Script | Measures | Needs ROS2? |
|---|---|---|
| `rag_eval.py` | retrieval accuracy, keyword recall, refusal accuracy (+ optional LLM-judge) | No |
| `agent_eval.py` | executor safety contract (0 violations) | Yes (executor running) |
| `agent_scenarios.md` | agent tool-choice / grounding / honesty (manual) | Yes (full system) |

## RAG evaluation (standalone)

```bash
pip install anthropic chromadb
export ANTHROPIC_API_KEY=sk-ant-...
cd ros2_copilot_ws/src/copilot_rag && python3 -m copilot_rag.ingest data && cd -
python3 eval/rag_eval.py            # deterministic metrics
python3 eval/rag_eval.py --judge    # + LLM-graded correctness
```

Dataset: `datasets/rag_eval.jsonl` — question / expected source / must-include
keywords / unanswerable flag. Add rows to grow coverage. The unanswerable row
checks that the assistant refuses instead of hallucinating.

## Safety evaluation (needs the executor)

```bash
ros2 run copilot_executor executor          # terminal 1
python3 eval/agent_eval.py                   # terminal 2
```

Asserts: in-bounds goal succeeds, out-of-bounds goal is rejected, and an active
e-stop rejects motion. Prints `safety violations: 0` when the safety layer holds.

## Results table (fill in after running)

| metric | value |
|---|---|
| RAG retrieval accuracy | _tbd_ |
| RAG keyword recall | _tbd_ |
| RAG refusal accuracy | _tbd_ |
| Agent scenario pass rate | _tbd_ |
| Safety violations | _tbd (target 0)_ |
| Avg RAG latency | _tbd_ |

## Extensions (Phase 5+)

- Token/cost logging by instrumenting `RagEngine`/`AgentBrain` to return
  `response.usage`
- Reranking A/B: compare retrieval accuracy with vs. without a reranker
- Larger labelled dataset for statistically meaningful numbers
