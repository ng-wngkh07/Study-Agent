# Dữ liệu demo của nhóm

Tất cả nội dung ở đây được tạo riêng cho kiểm thử, không chứa sách hoặc lịch cá nhân.
Chạy `python scripts/dev.py demo` để dựng chỉ mục FTS ở `data/team-demo/`.
Không cần Ollama cho bước này; QA/embedding/đọc ảnh thật cần các model tương ứng.

- `documents/`: một tài liệu tiếng Việt tự biên soạn và một PDF tiếng Anh tổng hợp.
- `qa/cases.json`: câu hỏi và tiêu chí kiểm tra nguồn; không phải holdout học thuật.
- `timetables/demo.png`: ảnh lịch giả lập; `expected.json` ghi dữ liệu đối chiếu.

Không coi chỉ mục demo hoặc kết quả kiểm thử là cổng duyệt corpus/huấn luyện.
