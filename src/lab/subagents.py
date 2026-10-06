"""GUIDE Phần 1 - Định nghĩa subagent (tác tử con).   >>> SINH VIÊN CÀI ĐẶT <<<

Pseudo-code: guides/pseudocode/02_subagents.md
Kiểm tra:    pytest tests/test_02_agent.py
"""


def get_subagents() -> list[dict]:
    """Trả về danh sách subagent (ít nhất 2, tên khác nhau).

    Mỗi phần tử là một dict có các khóa bắt buộc:
      "name":          tên duy nhất (chữ thường, có thể có dấu gạch ngang)
      "description":   khi nào tác tử chính nên giao việc cho subagent này (viết như một hướng dẫn hành động)
      "system_prompt": chỉ dẫn cho subagent
    """
    return [
        {
            "name": "explorer",
            "description": (
                "Use when starting a task or needing deep inspection of the repository structure, "
                "data samples, schema layouts, or log formats. Reads files, identifies edge cases, "
                "and reports structured factual summaries without modifying any files."
            ),
            "system_prompt": (
                "You are an exploratory analysis subagent. Your role is to examine the repository, "
                "read documentation, schema definitions, docstrings, and sample data. "
                "Report precise structural findings, key constraints, and potential edge cases. "
                "Do not create or edit any files."
            ),
        },
        {
            "name": "reviewer",
            "description": (
                "Use when work is implemented or when verifying outputs against all task instructions "
                "and boundary conditions before completing the task. Runs tests, checks data integrity, "
                "and reports discrepancies without modifying any files."
            ),
            "system_prompt": (
                "You are an independent quality assurance and verification subagent. "
                "Your role is to rigorously verify that code changes pass tests, outputs strictly match "
                "expected JSON/CSV schemas and conventions, and boundary conditions are satisfied. "
                "Do not modify files; only report validation results."
            ),
        },
    ]
