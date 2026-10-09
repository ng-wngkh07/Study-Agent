"""Run one local MLX inference from JSON stdin (in the Python 3.13 training venv)."""

import json
import sys
from pathlib import Path

from mlx_lm import generate, load
from mlx_lm.sample_utils import make_sampler
import mlx.core as mx


def main():
    request = json.load(sys.stdin)
    model_path = Path(request["model_path"])
    adapter_path = Path(request["adapter_path"]) if request.get("adapter_path") else None
    if not model_path.exists() or (adapter_path and not (adapter_path / "adapters.safetensors").exists()):
        raise FileNotFoundError("Chưa có mô hình hoặc adapter LoRA đã huấn luyện")
    model, tokenizer = load(str(model_path), adapter_path=str(adapter_path) if adapter_path else None)
    prompt = tokenizer.apply_chat_template(
        request["messages"], tokenize=False, add_generation_prompt=True
    )
    max_tokens = int(request.get("max_tokens", 700))

    seed = request.get("seed")
    if seed is not None:
        mx.random.seed(int(seed))

    temperature = request.get("temperature")
    gen_kwargs = {"max_tokens": max_tokens}
    if temperature is not None:
        gen_kwargs["sampler"] = make_sampler(temp=float(temperature))

    answer = generate(
        model, tokenizer, prompt=prompt, **gen_kwargs
    )
    tokens = tokenizer.encode(answer)
    is_truncated = len(tokens) >= max_tokens
    print(json.dumps({"answer": answer, "is_truncated": is_truncated}, ensure_ascii=False))


if __name__ == "__main__":
    main()
