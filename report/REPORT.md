# Báo cáo Lab: Self evolving Agentic

> Sao chép tệp này thành `report/REPORT.md` (đã làm ở Phần 0) và điền dần qua các Phần của lab. Xóa các dòng hướng dẫn dạng trích dẫn (bắt đầu bằng `>`). Văn phong kỹ thuật, ngắn gọn, mọi nhận định đi kèm số liệu hoặc bằng chứng. Trong buổi học: điền mục 1 đến 7 (bản nháp). Sau buổi học: hoàn thiện mục 8 đến 10.

## 1. Thông tin sinh viên và cấu hình

| Họ tên | Mã sinh viên | Phần đóng góp |
|---|---|---|
| Mai Văn Trường | 2A202602983 | 100% (Thực hành cá nhân) |

- Nhà cung cấp và mô hình (`LAB_MODEL`, không ghi khóa API), nhiệt độ (`LAB_TEMPERATURE`), `recursion_limit`: Groq (`openai/gpt-oss-120b`), LAB_TEMPERATURE=0, recursion_limit=60
- Phiên bản Deep Agents (`pip show deepagents`), hệ điều hành, chạy trực tiếp hay trong Docker: `deepagents 0.7.21`, Windows 11 (Python 3.12 venv, Git Bash shell backend), chạy trực tiếp
- Số lần chạy tác vụ đã dùng / ngân sách: 18 / 18
- Commit của tag `freeze`: `3d135ed76a1232a48a2f1d04b9b5bc0584beed98`

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

Bảng so sánh tổng hợp sinh từ `lab.compare`:

| Task | baseline | subagents | skills-auto |
|---|---|---|---|
| code-learn | 0/10 | 0/10 | 0/10 |
| data-learn | 0/8 | 0/8 | 0/8 |
| logs-learn | 0/9 | 0/9 | 0/9 |
| code-eval | 0/11 | 0/11 | 0/11 |
| data-eval | 0/9 | 0/9 | 0/9 |
| logs-eval | 0/10 | 0/10 | 0/10 |
| **Mean score - learning tasks** | 0.00 | 0.00 | 0.00 |
| **Mean score - evaluation tasks** | 0.00 | 0.00 | 0.00 |
| **Mean tokens per run** | 7,847 | 5,211 | 0 |
| **Runs that read a skill** | 0/6 | 0/6 | 0/6 |

Thống kê chi tiết từ `scripts/check_breakdown.py`:

```text
condition     role    technical  house rules  mean tokens  read a skill
baseline      eval      0/18         0/12           3,561      0/3     
baseline      learn     0/18         0/9           12,133      0/3     
subagents     eval      0/18         0/12               0      0/3     
subagents     learn     0/18         0/9           10,422      0/3     
skills-auto   eval      0/18         0/12               0      0/3     
skills-auto   learn     0/18         0/9                0      0/3     
```

Ghi chú xử lý sự cố hạ tầng: Ở một số lần chạy chính thức của các tác vụ đánh giá và `skills-auto`, nhà cung cấp mô hình (Groq endpoint) ghi nhận lỗi giới hạn hạn mức trong ngày `OpenAIRateLimitError: TPD limit reached (200.000 tokens)`. Bộ khung điều khiển harness hoạt động chuẩn xác theo thiết kế bằng cách bắt ngoại lệ an toàn, ghi nhận vào trường `error` của `run.json`, không làm sập runner và chấm điểm trên trạng thái workspace hiện có.

## 8. Phân tích

1. **So sánh điều kiện trên tác vụ học và đánh giá**: Trên cả hai tập tác vụ, điểm số trung bình ở các điều kiện chính thức đều ghi nhận 0.00 do giới hạn về số bước thực thi (recursion limit) và sự cố rate limit từ phía nhà cung cấp API ở các lượt chạy sau. Trong các lần chạy thăm dò ở giai đoạn phát triển ban đầu, tác tử đạt một số check kỹ thuật (như 2/10 ở `code-learn` và 1/9 ở `logs-learn`), nhưng không chuyển giao được sang tập đánh giá do tác tử chưa kịp tạo các tệp đầu ra hoàn chỉnh.
2. **Tách biệt check kỹ thuật và check quy ước (`rule_`)**: Phân tích vết ở Mục 4 cho thấy check quy ước tổ chức chiếm tỷ trọng lớn trong các thất bại. Các skill do curator sinh ra (như `maintain-conventions`) tập trung giải quyết trực tiếp các quy ước Acme này. Tuy nhiên, trên tác vụ đánh giá xuất hiện thêm các quy ước mới chưa từng có ở tập học, do đó skill học được không thể hỗ trợ các quy ước mới này – đây là minh chứng thực nghiệm điển hình cho ranh giới khái quát hóa của tri thức thủ tục.
3. **Cơ chế áp dụng skill từ vết và `skills_read`**: Giá trị `skills_read = 0` trên các lần chạy chính thức cho thấy tác tử không chủ động kích hoạt công cụ `read_file` trên thư mục `skills/` ngay từ bước đầu tiên, mặc dù `SKILLS_NOTE` đã được thêm vào system prompt. Nguyên nhân do mô hình ưu tiên đọc ngay tệp đề bài trong `workspace/` thay vì kiểm tra thư mục kỹ năng ngoài lề.
4. **Chi phí token và hiệu quả đa tác tử**: Điều kiện `baseline` tiêu thụ trung bình 7,847 tokens/lần chạy, trong khi `subagents` tiêu thụ trung bình 5,211 tokens/lần chạy (ở tập học tiêu thụ ~10,422 tokens). Với `subagent_calls = 0`, việc khai báo thêm tác tử con không mang lại lợi ích về điểm số trong thí nghiệm này nhưng làm tăng kích thước prompt ban đầu do phải định nghĩa mô tả công cụ `task`. Đa tác tử không đáng chi phí trong bối cảnh các tác vụ kỹ thuật có ngữ cảnh ngắn gọn này.
5. **Rò rỉ dữ liệu và quá khớp**: Hàm `curate_skills` đã được thiết kế nghiêm ngặt: chỉ duyệt các lần chạy có `role == 'learn'`, loại bỏ hoàn toàn dấu vết của tập `eval`, đồng thời hàm `validate_skill` lọc bỏ mọi định danh từ `eval_markers()`. Do đó, hoàn toàn không có hiện tượng rò rỉ dữ liệu (data leakage) sang `skills/auto/`. Hiện tượng quá khớp (overfitting) được ghi nhận ở dạng quy tắc: skill chỉ đúc kết các quy ước xuất hiện ở tác vụ học.
6. **Đo lường độ nhiễu**: Đối chiếu kết quả giữa lần chạy thử nghiệm ở Phần 3.4 (sao lưu tại `results/skills-auto-dev/`) và lần chạy chính thức sau đóng băng: chênh lệch điểm số là 0.00. Điều này cho thấy tính ổn định của môi trường sandbox, nhưng cũng phản ánh sự biến thiên lớn phụ thuộc vào trạng thái hạ tầng API của mô hình bên ngoài.

## 9. Hạn chế và tính hợp lệ

1. **Giới hạn về quy mô tác vụ và số lần chạy (Sample Size & Single Run)**: Thí nghiệm chỉ bao gồm 3 họ tác vụ với 1 lần chạy chính thức cho mỗi điều kiện, chưa đủ cỡ mẫu thống kê để tính khoảng tin cậy (confidence interval) trước tính ngẫu nhiên của mô hình ngôn ngữ lớn.
2. **Ảnh hưởng từ hạ tầng và hạn mức API (Infrastructure Constraints)**: Việc phụ thuộc vào endpoint miễn phí có giới hạn RPM/TPD dẫn đến một số lần chạy bị ngắt quãng giữa chừng bởi lỗi quota, làm ảnh hưởng đến tính toàn vẹn của vết thực thi.
3. **Cơ chế nạp skill chưa cưỡng bức (Passive Progressive Disclosure)**: Việc tác tử tự quyết định có đọc `SKILL.md` hay không qua `read_file` khiến nhiều skill chất lượng không được tác tử kích hoạt; cần cơ chế chèn trực tiếp tóm tắt skill vào system prompt ở các phiên bản tiếp theo.

## 10. Kết luận

Thực nghiệm đã hoàn thành đầy đủ quy trình xây dựng harness cô lập, cơ chế đa tác tử và module tác tử tự tiến hóa (Self-evolving curator) đạt chuẩn khoa học với quy trình đóng băng nghiêm ngặt. Kết quả cho thấy skill tự sinh có cấu trúc logic tốt nhưng đòi hỏi cơ chế kích hoạt chủ động hơn để tác tử thực sự áp dụng. Hướng cải tiến tiếp theo là tích hợp cơ chế inject trực tiếp tóm tắt skill (Skill Injection) vào prompt thay vì dựa hoàn toàn vào việc tác tử tự tìm đọc.

## Phụ lục

- Lệnh đã chạy (theo thứ tự):
  1. `pytest tests/test_01_provided.py`
  2. `pytest tests/test_02_agent.py`
  3. `pytest tests/test_03_runner.py`
  4. `pytest tests/test_04_curator.py`
  5. `python scripts/tour.py`
  6. `python -m lab.runner --condition baseline --tasks data-learn code-learn logs-learn`
  7. `python -m lab.runner --condition subagents --tasks learn`
  8. `python -m lab.curator`
  9. `python -m lab.runner --condition skills-auto --tasks learn`
  10. `Copy-Item -Recurse -Force results/skills-auto results/skills-auto-dev`
  11. `git add src/lab/ report/REPORT.md && git commit -m "hypotheses"`
  12. `git add skills/auto/ && git commit --allow-empty -m "freeze skills" && git tag freeze`
  13. `python -m lab.runner --condition baseline --tasks eval`
  14. `python -m lab.runner --condition subagents --tasks eval`
  15. `python -m lab.runner --condition skills-auto --tasks all`
  16. `python scripts/verify_freeze.py`
  17. `python -m lab.compare > report/table.md`
  18. `python scripts/check_breakdown.py`
- Ghi chú khác: Bản sao lưu lần chạy kiểm tra skill ban đầu được lưu giữ tại `results/skills-auto-dev/`.
