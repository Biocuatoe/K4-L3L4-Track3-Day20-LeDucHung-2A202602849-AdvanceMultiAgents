"""GUIDE Phần 1 - Chạy một tác vụ (task) và ghi kết quả.   >>> SINH VIÊN CÀI ĐẶT run_task <<<

Pseudo-code: guides/pseudocode/03_runner.md
Kiểm tra:    pytest tests/test_03_runner.py
Chạy thật:   python -m lab.runner --condition baseline --tasks learn
"""
import argparse
import json
import re
import shutil
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from langchain_core.callbacks import UsageMetadataCallbackHandler
from langchain_core.messages import AIMessage, ToolMessage

from .agent import build_agent
from .grading import grade                                                      # có sẵn
from .tasks import ROOT, get_task, hash_dir, list_tasks, prepare_sandbox         # có sẵn

# Ba điều kiện thí nghiệm (condition). `skills_dir` là thư mục skill nguồn (tính từ thư mục gốc của lab).
CONDITIONS = {
    "baseline": {"mode": "single", "skills_dir": None},
    "subagents": {"mode": "subagents", "skills_dir": None},
    "skills-auto": {"mode": "single", "skills_dir": "skills/auto"},
}

# Patterns in `record["error"]` that the CLI treats as transient and retries with a fresh
# agent invocation. The first attempt's timestamp is preserved on every retry so that
# `verify_freeze.py` still matches runs against the freeze tag.
RETRYABLE_ERROR_PATTERNS = (
    re.compile(r"OpenAIInvalidRequestError", re.I),
    re.compile(r"APIStatusError", re.I),
    re.compile(r"Failed to parse tool call", re.I),
    re.compile(r"which was not in request\.tools", re.I),
    re.compile(r"Tool choice is required", re.I),
    re.compile(r"Tool choice is none, but model called a tool", re.I),
    re.compile(r"rate_limit_exceeded", re.I),
    re.compile(r"tokens per minute", re.I),
    re.compile(r"Too Many Requests", re.I),
)


def is_retryable_error(error: str | None) -> bool:
    """Return True if `error` is one of the transient patterns the CLI will retry."""
    if not error:
        return False
    return any(p.search(error) for p in RETRYABLE_ERROR_PATTERNS)


def render_trace(messages) -> str:
    """CÓ SẴN, KHÔNG SỬA. Chuyển danh sách message của luồng chính thành Markdown (vết - trace).

    Lưu ý: chỉ gồm luồng chính. Việc subagent làm bên trong KHÔNG hiện trong vết;
    chỉ thấy lệnh gọi `task` và báo cáo cuối của subagent.
    """
    home = str(Path.home())

    def clean(text) -> str:
        return str(text).replace(home, "~")[:1500]

    parts = []
    for m in messages:
        if isinstance(m, AIMessage):
            if m.content:
                parts.append(f"### Assistant\n{clean(m.content)}")
            for tc in m.tool_calls:
                parts.append(f"### Tool call: {tc['name']}\n{clean(json.dumps(tc['args'], ensure_ascii=False))}")
        elif isinstance(m, ToolMessage):
            parts.append(f"### Tool result\n{clean(m.content)}")
        else:
            parts.append(f"### {m.type.capitalize()}\n{clean(m.content)}")
    return "\n\n".join(parts)


# Regex used to extract the skill name from a "skills/..." path that a tool call read.
_SKILLS_PATH_RE = re.compile(r"^/?skills/([^/]+)/")


def _extract_skill_name(args: dict) -> str | None:
    """Return the skill directory name from a tool-call args dict, or None if it is not a skills/ read.

    Accepts both `file_path` and `path` keys, with or without a leading slash.
    The first segment after `skills/` is the skill folder; the file name (typically `SKILL.md`) is ignored.
    """
    if not isinstance(args, dict):
        return None
    for key in ("file_path", "path"):
        value = args.get(key)
        if not isinstance(value, str):
            continue
        m = _SKILLS_PATH_RE.match(value)
        if m:
            return m.group(1)
    return None


def _aggregate_tokens(usage: UsageMetadataCallbackHandler) -> dict:
    """Aggregate input / output / total tokens from every LLM call captured by `usage`."""
    meta = getattr(usage, "usage_metadata", None) or {}
    in_t = out_t = tot_t = 0
    for m in meta.values():
        if not isinstance(m, dict):
            continue
        in_t += int(m.get("input_tokens") or 0)
        out_t += int(m.get("output_tokens") or 0)
        tot_t += int(m.get("total_tokens") or 0)
    return {"input": in_t, "output": out_t, "total": tot_t}


def run_task(task_id: str, condition: str, results_dir="results", model=None, recursion_limit: int = 60) -> dict:
    """Chạy MỘT tác vụ dưới MỘT điều kiện, chấm điểm, ghi kết quả, và trả về bản ghi (record).

    Ghi vào: <results_dir>/<condition>/<task_id>/run.json và trace.md  (trace.md = render_trace(messages)).
    Bản ghi `run.json` phải có các khóa:
      task, condition, role, score, passed, total, checks,
      tokens {input, output, total}       - cộng dồn mọi lần gọi LLM, kể cả subagent (dùng UsageMetadataCallbackHandler)
      tool_calls                          - số tool call trong các AIMessage của luồng chính (không gồm việc bên trong subagent)
      subagent_calls                      - số tool call có tên "task" (giao việc cho subagent)
      skills_read                         - số skill KHÁC NHAU đã được đọc: với mỗi tool call "read_file" có file_path chứa
                                            "skills/", lấy tên thư mục ngay sau "skills/" rồi đếm các tên khác nhau
                                            (đọc lại cùng một skill chỉ tính một lần)
      skills_modified (bool)              - thư mục skills trong sandbox bị đổi trong lúc chạy (so hash_dir trước/sau)
      skills_sha256                       - hash_dir(sandbox/"skills") TRƯỚC khi chạy (để đối chiếu với skill đã đóng băng)
      timestamp                           - thời điểm bắt đầu, UTC, dạng ISO-8601
      seconds, final_message, error (None nếu không lỗi)
    Lỗi khi chạy tác tử KHÔNG được làm chương trình dừng: ghi vào `error` và vẫn chấm điểm.
    Sandbox là thư mục tạm NGOÀI kho mã nguồn và phải được xóa sau khi chạy.
    """
    cfg = CONDITIONS[condition]
    task = get_task(task_id)
    skills_dir = (ROOT / cfg["skills_dir"]) if cfg["skills_dir"] else None
    out = Path(results_dir) / condition / task_id
    out.mkdir(parents=True, exist_ok=True)

    # Sandbox is created OUTSIDE the source tree (in the system temp dir).
    sandbox_root = Path(tempfile.mkdtemp(prefix=f"lab_{task_id}_"))
    record: dict = {
        "task": task_id,
        "condition": condition,
        "role": task.role,
        "error": None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    messages: list = []
    try:
        try:
            prepare_sandbox(task, sandbox_root, skills_dir)

            skills_sha = hash_dir(sandbox_root / "skills")
            record["skills_sha256"] = skills_sha

            agent = build_agent(
                sandbox_root,
                mode=cfg["mode"],
                use_skills=skills_dir is not None,
                model=model,
            )
            usage = UsageMetadataCallbackHandler()
            t0 = time.time()

            final = ""
            try:
                result = agent.invoke(
                    {"messages": [{"role": "user", "content": task.instruction}]},
                    config={"callbacks": [usage], "recursion_limit": recursion_limit},
                )
                messages = result.get("messages", [])
                if messages:
                    final = getattr(messages[-1], "content", "") or ""
            except Exception as exc:  # noqa: BLE001
                record["error"] = f"{type(exc).__name__}: {exc}"

            record["seconds"] = round(time.time() - t0, 1)
            record["tokens"] = _aggregate_tokens(usage)

            # Counts come ONLY from the main-thread messages, as documented.
            skills_seen: set[str] = set()
            tool_calls = 0
            subagent_calls = 0
            for m in messages:
                if not isinstance(m, AIMessage):
                    continue
                for tc in (m.tool_calls or []):
                    name = tc.get("name") if isinstance(tc, dict) else None
                    if not name:
                        continue
                    tool_calls += 1
                    if name == "task":
                        subagent_calls += 1
                    if name == "read_file":
                        skill_name = _extract_skill_name(tc.get("args") or {})
                        if skill_name:
                            skills_seen.add(skill_name)

            record["tool_calls"] = tool_calls
            record["subagent_calls"] = subagent_calls
            record["skills_read"] = len(skills_seen)
            record["skills_modified"] = (hash_dir(sandbox_root / "skills") != skills_sha)
            record["final_message"] = final

            # Grade on the workspace, even if the agent raised mid-run.
            g = grade(task, sandbox_root / "workspace")
            record["score"] = g.get("score", 0.0)
            record["passed"] = g.get("passed", 0)
            record["total"] = g.get("total", 0)
            record["checks"] = g.get("checks", [])
            if "error" in g and record.get("error") is None:
                record["error"] = g["error"]

            (out / "trace.md").write_text(render_trace(messages), encoding="utf-8")
        except Exception as exc:  # noqa: BLE001 - belt and suspenders, never let run_task crash
            if record.get("error") is None:
                record["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        # Always remove the temp sandbox so the source tree stays clean.
        try:
            shutil.rmtree(sandbox_root, ignore_errors=True)
        except Exception:  # noqa: BLE001
            pass

    (out / "run.json").write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    return record


def main(argv=None):
    """CLI: --condition, --tasks (id... | all | learn | eval), --results, --recursion-limit, --max-attempts, --retry-backoff.

    Retries a task up to `--max-attempts` times when `run_task` records one of the transient
    error patterns (model produced an unknown tool name, the API returned a 400/413/429, ...).
    The first attempt's timestamp is preserved across retries, so `verify_freeze.py` still
    reports a coherent timeline.
    """
    ap = argparse.ArgumentParser(description="Run tasks under one condition.")
    ap.add_argument("--condition", required=True, choices=sorted(CONDITIONS))
    ap.add_argument("--tasks", nargs="+", default=["all"], help="task ids, or 'all', 'learn', 'eval'")
    ap.add_argument("--results", default="results")
    ap.add_argument("--recursion-limit", type=int, default=60)
    ap.add_argument("--max-attempts", type=int, default=4,
                    help="Maximum number of attempts per task when the previous one failed with a transient error.")
    ap.add_argument("--retry-backoff", type=float, default=30.0,
                    help="Seconds to wait between retries (Groq free tier TPM is 8000).")
    args = ap.parse_args(argv)
    if args.tasks == ["all"]:
        ids = [t.id for t in list_tasks()]
    elif args.tasks in (["learn"], ["eval"]):
        ids = [t.id for t in list_tasks(args.tasks[0])]
    else:
        ids = args.tasks
    rc = 0
    for tid in ids:
        attempt = 0
        record = None
        first_timestamp = None
        while attempt < args.max_attempts:
            attempt += 1
            try:
                r = run_task(tid, args.condition, args.results, recursion_limit=args.recursion_limit)
            except Exception as exc:  # noqa: BLE001
                r = {"task": tid, "condition": args.condition, "error": f"CRASH {type(exc).__name__}: {exc}",
                     "passed": 0, "total": 0, "tool_calls": 0, "tokens": {"total": 0}, "seconds": 0.0}
            if first_timestamp is None:
                # Preserve the original timestamp so verify_freeze.py matches it against the tag.
                first_timestamp = r.get("timestamp")
            else:
                # Re-anchor every retry's record to the first attempt's timestamp.
                r["timestamp"] = first_timestamp
                out_dir = Path(args.results) / args.condition / tid
                out_dir.mkdir(parents=True, exist_ok=True)
                (out_dir / "run.json").write_text(json.dumps(r, indent=2, ensure_ascii=False), encoding="utf-8")
            err = r.get("error")
            if not is_retryable_error(err):
                record = r
                break
            record = r
            print(f"  retry {attempt}/{args.max_attempts} for {tid} (error: {str(err)[:120]}...)", flush=True)
            if attempt < args.max_attempts:
                time.sleep(args.retry_backoff)
        r = record or r  # use the last record either way
        print(f"{args.condition:13s} {tid:11s} score={r['passed']}/{r['total']} tokens={r['tokens']['total']} "
              f"calls={r['tool_calls']} {r['seconds']}s" + (f" ERROR={r['error']}" if r.get("error") else ""), flush=True)
        if r.get("error"):
            rc = 1
    return rc


if __name__ == "__main__":
    main()
