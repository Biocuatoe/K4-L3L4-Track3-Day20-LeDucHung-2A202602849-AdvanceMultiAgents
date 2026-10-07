"""GUIDE Phần 3 - Người tuyển chọn skill (skill curator): tự viết skill từ các lần chạy thất bại.   >>> SINH VIÊN CÀI ĐẶT curate_skills <<<

Pseudo-code: guides/pseudocode/04_curator.md
Kiểm tra:    pytest tests/test_04_curator.py
Chạy thật:   python -m lab.curator
"""
import json
import re
from pathlib import Path

from .model import make_model
from .tasks import ROOT, eval_markers   # có sẵn: định danh của tác vụ đánh giá, tính lúc chạy

# ---- CÓ SẴN, KHÔNG SỬA: kiểm tra và tách khối skill (phần dễ sai và liên quan bảo mật) ----------------
SAFE_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def validate_skill(text: str, expected_name: str | None = None) -> list[str]:
    """Kiểm tra nội dung một SKILL.md. Trả về danh sách vấn đề (rỗng = hợp lệ).

    Quy tắc: có khối YAML frontmatter; `name` chữ thường/số/gạch ngang (tối đa 64 ký tự) và bằng `expected_name`
    nếu được truyền; có `description` (tối đa 1024 ký tự); phần thân tối đa 80 dòng; không chứa chuỗi nào của
    `eval_markers()`. Quy tắc về `name` cũng là biện pháp bảo mật: tên khối do LLM sinh ra được dùng để tạo
    đường dẫn, nên `../evil` không được lọt qua.
    """
    problems = []
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text.strip() + "\n", re.S)
    if not m:
        return ["missing YAML frontmatter"]
    front, body = m.groups()
    name = re.search(r"^name:\s*(.+)$", front, re.M)
    desc = re.search(r"^description:\s*(.+)$", front, re.M)
    n = name.group(1).strip() if name else ""
    if not SAFE_NAME.fullmatch(n) or len(n) > 64:
        problems.append("invalid name")
    elif expected_name is not None and n != expected_name:
        problems.append("name differs from the block name")
    if not desc or len(desc.group(1).strip()) > 1024:
        problems.append("missing or too long description")
    if len(body.strip().splitlines()) > 80:
        problems.append("body longer than 80 lines")
    low = text.lower()
    for marker in eval_markers():
        if marker in low:
            problems.append(f"mentions evaluation material: {marker}")
    return problems


def parse_skill_blocks(reply: str) -> list[tuple[str, str]]:
    """Tách câu trả lời của LLM thành danh sách (name, nội dung SKILL.md).

    Khuôn dạng: `=== SKILL: <name> ===` ... `=== END ===`. Một khối kết thúc ở điểm nào đến trước trong ba điểm:
    `=== END ===`, tiêu đề `=== SKILL:` kế tiếp, hoặc cuối văn bản (LLM đôi khi quên dòng END).
    """
    pattern = re.compile(r"^=== SKILL: (\S+) ===[ \t]*\n(.*?)(?=^=== END ===|^=== SKILL: |\Z)", re.S | re.M)
    return [(name, text.strip()) for name, text in pattern.findall(str(reply))]
# --------------------------------------------------------------------------------------------------


# Tail of each trace that we send to the model. Long traces would blow the context window.
TRACE_TAIL_CHARS = 6000

PROMPT_TEMPLATE = """You write Agent Skills (SKILL.md files) for an engineering/data-analysis agent.

You are given failed checks from LEARNING runs of a coding + data analysis lab. Each failed check shows
the rule that was violated (in the "RULE:" line) and the agent's last actions (in the trace). Your job
is to infer GENERAL PROCEDURAL KNOWLEDGE that will help the agent do better on NEW, similar tasks.

Hard rules you must follow:
- Produce at most {max_skills} skill(s).
- Each skill must be GENERAL PROCEDURAL KNOWLEDGE. NEVER mention a specific task id, a specific input
  filename, a specific column, a specific function, or any expected value. If a rule is tied to a
  particular value or filename, generalize it to a procedure instead.
- Each skill must be valid Agent Skills frontmatter:
    === SKILL: <name> ===
    ---
    name: <name>
    description: <one sentence: USE WHEN ...>
    ---
    <procedural body, imperative, short checklist of at most ~40 lines>
    === END ===
- `name` is lowercase, digits and hyphens only (no spaces, no `/`, no `..`, no uppercase).
- `description` MUST start with "Use when" and clearly state the triggering situation.
- The body MUST be short, imperative, and actionable. A numbered checklist works best.
- Do NOT mention evaluation tasks or evaluation material. Do NOT include code that references a
  specific value (e.g. "the answer is 42").
- Reply with ONLY the skill blocks. No prose before or after.

Below are the failed checks of the LEARNING runs (task, check name, review-bot feedback) and the tail
of each run's trace.

{runs}
"""


def _load_runs(results_dir: Path, source_condition: str) -> list[dict]:
    """Read every LEARNING run of `source_condition` and extract failed checks + trace tail."""
    runs: list[dict] = []
    src = results_dir / source_condition
    if not src.exists():
        return runs
    for run_path in sorted(src.glob("*/run.json")):
        try:
            data = json.loads(run_path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        if data.get("role") != "learn":
            continue
        failed: list[tuple[str, str]] = []
        for c in data.get("checks", []) or []:
            if not c.get("passed"):
                failed.append((c.get("name", "?"), c.get("detail", "")))
        if not failed:
            continue
        trace = ""
        trace_path = run_path.parent / "trace.md"
        if trace_path.exists():
            text = trace_path.read_text(encoding="utf-8", errors="replace")
            if len(text) > TRACE_TAIL_CHARS:
                trace = "...[trace truncated]...\n" + text[-TRACE_TAIL_CHARS:]
            else:
                trace = text
        runs.append({
            "task": data.get("task"),
            "failed": failed,
            "trace": trace,
        })
    return runs


def curate_skills(results_dir="results", source_condition="baseline", out_dir=None, model=None, max_skills: int = 3) -> list[Path]:
    """Đọc các lần chạy của TÁC VỤ HỌC (role == "learn") trong `source_condition`, nhờ LLM viết skill, ghi file.

    Các bước: nạp run.json + trace.md -> (nếu không có check nào thất bại: in cảnh báo và trả về [] mà KHÔNG gọi LLM)
    -> dựng prompt -> model.invoke(prompt) -> parse_skill_blocks -> validate_skill(text, expected_name=name)
    -> ghi `<out_dir>/<name>/SKILL.md`. Mặc định `out_dir` = <gốc lab>/skills/auto (dùng `ROOT` từ lab.tasks).
    Giữ tối đa `max_skills` skill hợp lệ; skill không hợp lệ bị bỏ qua.
    Prompt chứa, với mỗi check thất bại, TÊN và trường `detail` (lời nhận xét của bot đánh giá: phát biểu quy tắc bị vi phạm)
    cùng phần cuối của vết (trace). Với tác vụ học, `detail` chỉ phát biểu quy tắc, không chứa đáp án.
    Tuyệt đối KHÔNG đưa dữ liệu của tác vụ đánh giá (role == "eval") vào prompt.
    model mặc định: make_model() (lab.model).
    Trả về: danh sách đường dẫn SKILL.md đã ghi.
    """
    if out_dir is None:
        out_dir = ROOT / "skills" / "auto"
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    runs = _load_runs(Path(results_dir), source_condition)
    runs = [r for r in runs if r["failed"]]

    if not runs:
        print("[curator] no failed checks in any learning run of", source_condition, "- skipping model call")
        return []

    if model is None:
        model = make_model()

    runs_text_parts = []
    for r in runs:
        checks_text = "\n".join(f"- {name}: {detail}" for name, detail in r["failed"])
        runs_text_parts.append(
            f"### Run: {r['task']} (learning)\n"
            f"Failed checks (name: feedback):\n{checks_text}\n\n"
            f"Trace tail (last {TRACE_TAIL_CHARS} chars):\n```\n{r['trace']}\n```\n"
        )
    runs_text = "\n\n".join(runs_text_parts)
    prompt = PROMPT_TEMPLATE.format(max_skills=max_skills, runs=runs_text)

    reply = model.invoke(prompt).content
    blocks = parse_skill_blocks(reply)

    written: list[Path] = []
    for name, text in blocks:
        if len(written) >= max_skills:
            break
        problems = validate_skill(text, expected_name=name)
        if problems:
            # Skip invalid blocks silently - the security boundary is the validator.
            continue
        # Defence in depth: the validator already enforces the regex, but we double-check before
        # using the model-supplied name as a path component.
        if not SAFE_NAME.fullmatch(name) or len(name) > 64 or "/" in name or ".." in name:
            continue
        target_dir = out_dir / name
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            target = target_dir / "SKILL.md"
            target.write_text(text, encoding="utf-8")
            written.append(target)
        except OSError:
            continue
    return written


if __name__ == "__main__":
    for p in curate_skills():
        print("wrote", p)
