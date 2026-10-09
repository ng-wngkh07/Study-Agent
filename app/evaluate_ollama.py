"""Evaluate a local Ollama model on held-out, source-grounded examples."""

import argparse
import hashlib
import json
import re
from pathlib import Path

import requests

from app.config import OLLAMA_BASE_URL
from app.evaluation_metrics import citation_metrics, plain_answer_metrics


def evaluate(data_dir: Path, indices: list[int], output: Path, model: str = "qwen2.5:7b") -> dict:
    approval = json.loads((data_dir / "approval.json").read_text(encoding="utf-8"))
    digest = hashlib.sha256((data_dir / "train.jsonl").read_bytes() + (data_dir / "valid.jsonl").read_bytes()).hexdigest()
    if digest != approval["dataset_sha256"]:
        raise ValueError("Dữ liệu không khớp approval.json")
    summary_path = data_dir / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}
    plain_answer = summary.get("plain_answer") is True
    cases = [json.loads(line) for line in (data_dir / "valid.jsonl").read_text(encoding="utf-8").splitlines() if line]
    if not indices or any(index < 0 or index >= len(cases) for index in indices):
        raise ValueError("Chỉ số ca đánh giá không hợp lệ")
    results = []
    for index in indices:
        messages = cases[index]["messages"]
        if messages[0]["role"] != "system" or messages[1]["role"] != "user":
            raise ValueError(f"Ca {index} không phải câu hỏi đáp")
        source_ids = set(re.findall(r'<document id="(S\d+)"', messages[1]["content"]))
        if not source_ids:
            raise ValueError(f"Ca {index} không có đoạn nguồn")
        response = requests.post(
            OLLAMA_BASE_URL.rstrip("/") + "/api/chat",
            json={"model": model, "stream": False, "think": False,
                  "options": {"temperature": 0, "num_predict": 500, "repeat_penalty": 1.12},
                  "messages": messages[:2]},
            timeout=240,
        )
        response.raise_for_status()
        answer = response.json()["message"]["content"].strip()
        results.append({"valid_index": index, "dataset_sha256": digest,
                        "question": messages[1]["content"].split("Câu hỏi:")[-1].strip(),
                        "reference": messages[2]["content"], "answer": answer,
                        **(plain_answer_metrics(answer) if plain_answer else citation_metrics(answer, source_ids))})
        print(f"[{len(results)}/{len(indices)}] {index}: {sorted(source_ids)}", flush=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"model": model, "cases": len(results), "dataset_sha256": digest,
            "answer_format": "plain" if plain_answer else "cited",
            "format_valid": sum(x.get("format_valid", False) for x in results) if plain_answer else None,
            "valid_citations": None if plain_answer else sum(x["citation_valid"] for x in results), "output": str(output)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--case-indices", type=int, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", default="qwen2.5:7b")
    args = parser.parse_args()
    print(json.dumps(evaluate(args.data, args.case_indices, args.output, args.model), ensure_ascii=False))


if __name__ == "__main__":
    main()
