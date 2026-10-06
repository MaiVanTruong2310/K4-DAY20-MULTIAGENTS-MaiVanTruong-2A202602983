"""GUIDE Phần 3 - Người tuyển chọn skill (skill curator): tự viết skill từ các lần chạy thất bại.   >>> SINH VIÊN CÀI ĐẶT curate_skills <<<

Pseudo-code: guides/pseudocode/04_curator.md
Kiểm tra:    pytest tests/test_04_curator.py
Chạy thật:   python -m lab.curator
"""
import re
from pathlib import Path

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


def curate_skills(results_dir="results", source_condition="baseline", out_dir=None, model=None, max_skills: int = 3) -> list[Path]:
    """Đọc các lần chạy của TÁC VỤ HỌC (role == "learn") trong `source_condition`, nhờ LLM viết skill, ghi file."""
    if out_dir is None:
        out_dir = ROOT / "skills" / "auto"
    else:
        out_dir = Path(out_dir)

    source_dir = Path(results_dir) / source_condition
    if not source_dir.exists():
        print(f"Cảnh báo: thư mục kết quả {source_dir} không tồn tại")
        return []

    runs = []
    for run_file in sorted(source_dir.glob("*/run.json")):
        try:
            r = json.loads(run_file.read_text(encoding="utf-8"))
        except Exception:
            continue

        if r.get("role") != "learn":
            continue

        failed = [
            (c.get("name", ""), c.get("detail", ""))
            for c in r.get("checks", [])
            if not c.get("passed", False)
        ]
        trace_file = run_file.parent / "trace.md"
        trace_text = ""
        if trace_file.exists():
            try:
                trace_text = trace_file.read_text(encoding="utf-8")
                if len(trace_text) > 6000:
                    trace_text = trace_text[-6000:]
            except Exception:
                trace_text = ""

        runs.append({
            "task": r.get("task", run_file.parent.name),
            "failed": failed,
            "trace": trace_text,
        })

    # Nếu không có check nào thất bại ở tác vụ học: in cảnh báo và trả về [] mà KHÔNG gọi mô hình
    has_any_failed = any(bool(run["failed"]) for run in runs)
    if not has_any_failed:
        print("Cảnh báo: không có check thất bại ở tác vụ học")
        return []

    runs_summary = []
    for run in runs:
        if not run["failed"]:
            continue
        lines = [f"Task: {run['task']}"]
        lines.append("Failed checks:")
        for name, detail in run["failed"]:
            lines.append(f"  - Check: {name}")
            if detail:
                lines.append(f"    Feedback/Rule detail: {detail}")
        if run["trace"]:
            lines.append("Execution trace excerpt:")
            lines.append(run["trace"])
        runs_summary.append("\n".join(lines))

    prompt = (
        "You are an expert engineer curating procedural skills for an AI coding and data agent.\n"
        "Below are the failed checks (check names and evaluation feedback notes) and execution traces "
        "from learning tasks.\n"
        "Identify general procedural mistakes and conventions (not specific hardcoded task answers). "
        f"Write at most {max_skills} concise, general skills that will prevent these errors in future tasks of the same kind.\n\n"
        "Rules:\n"
        "- Skills must be generic and actionable: do not hardcode specific task IDs, exact numbers, or task-specific file names unless required as a global organizational standard.\n"
        "- Each skill MUST have YAML frontmatter with 'name' (lowercase letters, digits, and hyphens) and 'description' (one sentence: WHEN TO USE),\n"
        "  followed by concise, step-by-step imperative guidelines (at most 40 lines).\n"
        "- Output format MUST follow this exact delimiter block:\n"
        "=== SKILL: <name> ===\n"
        "---\n"
        "name: <name>\n"
        "description: <when to use this skill>\n"
        "---\n"
        "<imperative rules and guidelines>\n"
        "=== END ===\n\n"
        + "\n\n---\n\n".join(runs_summary)
    )

    llm = model or make_model()
    response = llm.invoke(prompt)
    reply_content = response.content
    if isinstance(reply_content, list):
        reply_content = str(reply_content)

    blocks = parse_skill_blocks(reply_content)
    written = []
    out_dir.mkdir(parents=True, exist_ok=True)

    for name, text in blocks:
        if len(written) >= max_skills:
            break
        problems = validate_skill(text, expected_name=name)
        if problems:
            continue
        skill_dir = out_dir / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_path = skill_dir / "SKILL.md"
        skill_path.write_text(text.strip() + "\n", encoding="utf-8")
        written.append(skill_path)

    return written


if __name__ == "__main__":
    for p in curate_skills():
        print("wrote", p)
