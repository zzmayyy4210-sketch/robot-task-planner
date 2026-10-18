"""Offline task interpretation demo. Never controls hardware."""
import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, ValidationError


class Task(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    action: Literal["pick_and_place"] = "pick_and_place"
    object: Literal["red_block", "blue_block", "green_block"] | None = None
    target: Literal["left_box", "right_box"] | None = None


def validate_candidate(raw: str) -> Task:
    """Future model adapters must pass their JSON through this boundary."""
    return Task.model_validate_json(raw)


def mock_parse(text: str) -> Task:
    # Deliberately narrow grammar: reject extra instructions rather than guess.
    match = re.fullmatch(
        r"(?:请)?把(?:桌面上的)?(?P<obj>红色方块|蓝色方块|绿色方块|方块)"
        r"放进(?P<target>左边的盒子|右边的盒子|盒子)[。！!]?", text.strip()
    )
    if not match:
        raise ValueError("unsupported_input")
    objects = {"红色方块": "red_block", "蓝色方块": "blue_block", "绿色方块": "green_block"}
    targets = {"左边的盒子": "left_box", "右边的盒子": "right_box"}
    return validate_candidate(json.dumps({
        "action": "pick_and_place", "object": objects.get(match["obj"]),
        "target": targets.get(match["target"]),
    }))


def plan(text: str) -> dict:
    if not isinstance(text, str) or not text.strip() or len(text) > 500:
        return {"status": "rejected", "error": "invalid_input", "steps": []}
    try:
        task = mock_parse(text)
    except ValidationError:
        return {"status": "rejected", "error": "invalid_model_output", "steps": []}
    except ValueError:
        return {"status": "rejected", "error": "unsupported_input", "steps": [],
                "question": "请只描述一次搬运，例如：把红色方块放进左边的盒子。"}
    questions = []
    if task.object is None:
        questions.append("要搬哪个方块：红色、蓝色还是绿色？")
    if task.target is None:
        questions.append("放进哪个盒子：左边还是右边？")
    return {
        **task.model_dump(), "needs_clarification": bool(questions),
        "status": "clarification" if questions else "ready",
        "error": "missing_fields" if questions else None,
        "questions": questions,
        "steps": [] if questions else [
            f"确认 {task.object} 与 {task.target} 的位置及可达性",
            f"规划到 {task.object} 的抓取路径", f"抓取 {task.object}",
            f"规划到 {task.target} 的搬运路径", "放置并检查结果",
        ],
    }


def evaluate(path: Path) -> dict:
    samples = json.loads(path.read_text(encoding="utf-8"))
    errors, correct, ready = Counter(), 0, 0
    for sample in samples:
        result = plan(sample["input"])
        correct += all(result.get(k) == v for k, v in sample["expected"].items())
        ready += result["status"] == "ready"
        if result.get("error"):
            errors[result["error"]] += 1
    total = len(samples)
    return {"total": total, "expected_behavior_accuracy": correct / total if total else 0,
            "ready_rate": ready / total if total else 0, "error_types": dict(errors)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("text", nargs="?")
    parser.add_argument("--evaluate", type=Path)
    args = parser.parse_args()
    if args.evaluate:
        result = evaluate(args.evaluate)
    else:
        text = args.text if args.text is not None else input("机器人任务：")
        result = plan(text)
        Path("logs").mkdir(exist_ok=True)
        with Path("logs/events.jsonl").open("a", encoding="utf-8") as log:
            log.write(json.dumps({"time": datetime.now(timezone.utc).isoformat(),
                                  "input": text, "result": result}, ensure_ascii=False) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
