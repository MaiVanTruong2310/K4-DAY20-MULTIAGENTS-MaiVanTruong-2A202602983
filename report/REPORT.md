# Báo cáo Lab: Self evolving Agentic

> Sao chép tệp này thành `report/REPORT.md` (đã làm ở Phần 0) và điền dần qua các Phần của lab. Xóa các dòng hướng dẫn dạng trích dẫn (bắt đầu bằng `>`). Văn phong kỹ thuật, ngắn gọn, mọi nhận định đi kèm số liệu hoặc bằng chứng. Trong buổi học: điền mục 1 đến 7 (bản nháp). Sau buổi học: hoàn thiện mục 8 đến 10.

## 1. Thông tin sinh viên và cấu hình

| Họ tên | Mã sinh viên | Phần đóng góp |
|---|---|---|
| Mai Văn Trường | 2A202602983 | 100% (Thực hành cá nhân) |

- Nhà cung cấp và mô hình (`LAB_MODEL`, không ghi khóa API), nhiệt độ (`LAB_TEMPERATURE`), `recursion_limit`: Groq (`openai/gpt-oss-120b`), LAB_TEMPERATURE=0, recursion_limit=60
- Phiên bản Deep Agents (`pip show deepagents`), hệ điều hành, chạy trực tiếp hay trong Docker: `deepagents 0.7.21`, Windows 11 (Python 3.12 venv, Git Bash shell backend), chạy trực tiếp
- Số lần chạy tác vụ đã dùng / ngân sách: 0 / 18
- Commit của tag `freeze`:

## 2. Giả thuyết (commit TRƯỚC tag `freeze`, Phần 4.0)

- H1 (subagents so với baseline): Dự đoán điều kiện subagents sẽ tiêu tốn nhiều token hơn đáng kể so với baseline (theo nghiên cứu đa tác tử của Anthropic), nhưng điểm số trên tác vụ đánh giá khó cải thiện vượt trội nếu tác tử chính ít giao việc hoặc không truyền đủ toàn bộ ngữ cảnh nhiệm vụ sang tác tử con.
- H2 (skills-auto so với baseline): Dự đoán điều kiện skills-auto sẽ cải thiện các check quy ước và định dạng chung (type hints, changelog, xử lý file) so với baseline; tuy nhiên theo kết quả từ SkillsBench và SkillEvolBench, skill do mô hình tự sinh có nguy cơ quá khớp (overfitting) với tác vụ học và khó giải quyết các quy ước mới chưa từng thấy trên tác vụ đánh giá.
- H3 (tác vụ học so với tác vụ đánh giá): Dự đoán điểm trung bình trên tác vụ đánh giá sẽ thấp hơn tác vụ học ở tất cả các điều kiện, vì tập đánh giá sử dụng dữ liệu mới và bổ sung thêm các quy tắc kiểm tra mới mà tác tử chưa được tiếp xúc trong vết phản hồi ban đầu.

## 3. Làm quen Deep Agents (Phần 0.3)

1. Tác tử mặc định có 9 công cụ:
   - Công cụ thao tác tệp: `ls`, `read_file`, `write_file`, `edit_file`, `delete`, `glob`, `grep`.
   - Công cụ shell chạy lệnh: `execute`.
   - Công cụ điều phối tác tử con: `task`.
   Công cụ cho phép chạy lệnh là `execute`.

2. Mô tả công cụ `task` nêu rõ:
   - Subagent `general-purpose` là tác tử đa năng dùng để nghiên cứu các câu hỏi phức tạp, tìm kiếm file/nội dung và thực thi các tác vụ nhiều bước; có toàn quyền truy cập các công cụ như tác tử chính.
   - Về ngữ cảnh: Subagent có tính chất phi trạng thái (stateless by default), nó chỉ nhìn thấy nội dung prompt do tác tử chính gửi trực tiếp sang mà không thấy toàn bộ lịch sử ngữ cảnh trước đó của tác tử chính, và chỉ trả về một báo cáo cuối cùng.

3. Trích dẫn câu hướng dẫn hành vi:
   - Từ mô tả công cụ `task`: *"Each invocation is stateless by default: the agent sees only the prompt you give it and returns a single final report. Put full detail in the prompt and state exactly what it should return."*
   - Từ mô tả công cụ `execute`: *"You MUST avoid using search commands like find and grep. Instead use the grep, glob tools to search. Use read_file rather than cat/head/tail."*

## 4. Đường cơ sở và phân loại lỗi (Phần 2.2)

| Tác vụ | Check thất bại | Nhóm lỗi (A-G) | Bằng chứng (trích ngắn từ `detail` hoặc vết) |
|---|---|---|---|
| `code-learn` | `rule_type_hints` | E (Vi phạm quy ước tổ chức) | `RULE: every public function (name not starting with '_') in the package has type annotations on all parameters and on the return value.` |
| `code-learn` | `rule_regression_tests` | E (Vi phạm quy ước tổ chức) | `RULE: add tests/test_regressions.py with one test function per bug you fixed (at least 3); the file must pass.` |
| `code-learn` | `rule_changelog` | E (Vi phạm quy ước tổ chức) | `RULE: record each fix in CHANGELOG.md under the heading '## Unreleased' as a bullet '- fix(<function name>): <short description>' (at least 3 bullets).` |
| `code-learn` | `parse_price_all_formats` | D (Bỏ sót định dạng dữ liệu) | `wrong for: ['$1,299.50', '(12.00)', '$1,000,000.00']` (chưa xử lý số âm trong ngoặc đơn và dấu phẩy ngăn cách hàng nghìn) |
| `code-learn` | `csv_quoting_follows_docstring` | A (Bỏ qua đặc tả) | `to_csv_row returned 'Desk, large "oak",10.00,2'` (không tuân thủ quy tắc quote escape của docstring) |
| `data-learn` | `rule_clean_csv` | E (Vi phạm quy ước tổ chức) | `RULE: write workspace/clean.csv with the header order_id,timestamp_utc,region,amount_cents; one row per distinct order...` |

Nhận xét: Phần lớn các lỗi thất bại rơi vào **Nhóm E (Vi phạm quy ước tổ chức)** do các quy tắc này không nằm trong đề bài thông thường mà thuộc về chuẩn mực nội bộ của tổ chức (Acme conventions) được review bot kiểm tra. Tác tử mặc định không thể đoán trước các quy tắc này nếu không có chỉ dẫn. Tác tử tự tiến hóa (Self-evolving) thông qua module curator có khả năng phòng ngừa rất tốt nhóm lỗi E này bằng cách đúc kết các phản hồi `RULE:` thành các skill thủ tục (như `maintain-conventions`).

## 5. Điều kiện `subagents` (Phần 2.3)

- Các subagent đã định nghĩa (tên, vai trò, lý do thiết kế):
  1. `explorer`: Đóng vai trò khảo sát, đọc README, kiểm tra schema tệp dữ liệu, docstring và cấu trúc log để lập danh sách ràng buộc thực tế mà không chỉnh sửa tệp; giúp tránh việc tác tử chính thao tác vội vàng dẫn đến lỗi.
  2. `reviewer`: Đóng vai trò kiểm thử và đánh giá độc lập; chạy lại test runner, đối chiếu đầu ra với các quy ước và trường hợp biên của đề bài trước khi kết thúc tác vụ.
- `subagent_calls` ở từng tác vụ và nhận xét (kể cả trường hợp bằng 0): Trong cả 3 tác vụ học, `subagent_calls = 0`. Tác tử chính lựa chọn trực tiếp sử dụng các công cụ `read_file` và `execute` thay vì phân rã công việc cho subagent, phản ánh việc tác tử ưu tiên tự thực thi khi bài toán có phạm vi vừa phải.
- Thông tin thiếu hoặc thừa khi giao việc (nếu có giao việc): Không có giao việc diễn ra do tác tử chính không gọi công cụ `task`.
- Ảnh hưởng đến token và thời gian: Số lượng token tiêu thụ ở điều kiện `subagents` tương đương với `baseline` (khoảng 12k - 13k token) do tác tử chính không phát sinh thêm các chuỗi đối thoại trung gian của tác tử con.

## 6. Self-evolving: skill do curator sinh (Phần 3)

- Số lần chạy curator, số skill bị xóa và lý do: Chạy curator 1 lần, sinh ra 3 skill hợp lệ, 0 skill bị xóa vì toàn bộ 3 skill đều đạt chuẩn định dạng và có giá trị thủ tục cao.

| Skill | Tổng quát hay riêng cho tác vụ học? | Đúng hay sai (nêu chỗ sai nếu có) | Độ dài, `description` và `skills_read` ở Phần 3.4 |
|---|---|---|---|
| `follow-docstring-spec` | Tổng quát cho việc đọc hiểu docstring, xử lý Decimal và CSV quoting | Đúng, đưa ra hướng dẫn chuẩn RFC 4180 và Decimal | 15 dòng; description rõ ràng về tình huống áp dụng; skills_read = 0 ở dev run |
| `maintain-conventions` | Tổng quát cho các quy ước Acme (type hints, regression tests, changelog) | Đúng, bám sát các yêu cầu từ review bot | 12 dòng; description chỉ định khi cần tuân thủ quy ước nhóm; skills_read = 0 |
| `handle-file-io-correctly` | Tổng quát cho các thao tác đọc ghi file an toàn, json indent và csv | Đúng, hướng dẫn đảm bảo thư mục tồn tại và encoding utf-8 | 13 dòng; description nêu rõ phòng ngừa lỗi thiếu file; skills_read = 0 |

## 7. Kết quả so sánh (Phần 4.3, 4.4)

> Dán nội dung `report/table.md` và kết quả `python scripts/check_breakdown.py`. Nêu các lần chạy có `error` hoặc `skills_modified = true` (nếu có) và cách xử lý.

```text
(dán bảng ở đây)
```

## 8. Phân tích

> Trả lời từng câu bằng số liệu từ mục 7 và bằng chứng từ vết. Kết quả âm hoặc không có khác biệt vẫn hợp lệ nếu được phân tích tốt.

1. So với `baseline`, điều kiện nào cải thiện điểm tác vụ **học**? Điều kiện nào cải thiện điểm tác vụ **đánh giá**? Có điều kiện nào cải thiện tác vụ học nhưng không cải thiện tác vụ đánh giá? Nếu có, đó là dấu hiệu gì?
2. Tách điểm thành check kỹ thuật và check quy ước (`rule_`). Skill do curator sinh giúp nhóm check nào? Check quy ước **mới** của tác vụ đánh giá có được skill giúp không, và vì sao?
3. Dựa vào vết và `skills_read`, giải thích một check mà skill giúp đạt và một check mà skill không giúp (skill chưa được đọc, đọc nhưng không làm theo, skill thiếu hoặc sai).
4. Chi phí: so sánh số token trung bình giữa các điều kiện. Điều kiện nào có hiệu quả tốt nhất theo điểm trên mỗi token? Đa tác tử có đáng chi phí trong thí nghiệm này không?
5. Có dấu hiệu rò rỉ dữ liệu hoặc quá khớp nào trong skill sinh ra không? Nhóm đã phòng tránh như thế nào?
6. Nhiễu: so sánh điểm tác vụ học của cùng bộ skill ở Phần 3.4 (đã sao lưu) và sau đóng băng. Chênh lệch bao nhiêu? Nó cho biết điều gì về độ tin cậy của các chênh lệch trong bảng ở mục 7?

## 9. Hạn chế và tính hợp lệ

> Nêu ít nhất 3 hạn chế và ảnh hưởng của từng hạn chế đến kết luận (ví dụ: chỉ 3 tác vụ mỗi vai trò, mỗi cấu hình chạy một lần, nhiễu của mô hình, tác vụ do giảng viên thiết kế sẵn quy ước, chỉ một mô hình).

1.
2.
3.

## 10. Kết luận

> Tối đa 5 câu. Chỉ khẳng định điều số liệu hỗ trợ. Nêu một đề xuất cải tiến tiếp theo.

## Phụ lục

- Lệnh đã chạy (theo thứ tự):
- Thử thách mở rộng (nếu có): hướng chọn, kết quả, nhận xét.
- Ghi chú khác:
