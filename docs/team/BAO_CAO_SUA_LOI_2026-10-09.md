# Báo cáo sửa lỗi và kiểm chứng dự án

**Dự án:** Agent Học Tập. **Ngày báo cáo:** 09/10/2026.
**Phạm vi:** tài sản GitHub, hướng dẫn/dependency và các lỗi sản phẩm đã xác nhận.

Báo cáo tổng hợp thay đổi, bằng chứng nghiệm thu và vấn đề còn mở. Các mốc chi tiết giữ trong [nhật ký](../../LICH_SU_DU_AN.md). PR #1 và PR #2 đã được chủ repo merge; kết quả test dưới đây gắn với phiên bản được nêu, không thay nghiệm thu model/dữ liệu thật.

## 1. Kết quả xử lý

| Nhóm/mã lỗi | Trước sửa | Sau sửa/kiểm chứng |
| --- | --- | --- |
| GitHub F01 - mở nguồn | Nguồn Markdown có nút PDF không tồn tại | Nguồn văn bản mở đúng phần/trích đoạn; PDF giữ ảnh gốc và mở đúng trang. RED 2/3; GREEN 3 UI |
| GitHub F02 - giấy phép | LICENSE thiếu | Khôi phục MIT gốc; thông báo bản quyền được giữ nguyên |
| GitHub F03 - nhánh chính | Main chưa có bảo vệ | Bảo vệ CI Windows/Mac/history, nhánh cập nhật, hội thoại, áp dụng admin, cấm force-push/xóa. Chính sách approval hiện hành ở mục 3 |
| GitHub F04 - bằng chứng CI | Link run cũ trả 404 | Hướng dẫn dẫn workflow hiện hành; giữ mốc lịch sử và ghi rõ không xác định nguyên nhân run cũ mất |
| Dependency | Một số phiên bản được cho phép không khớp import/Pydantic/TestClient | PyMuPDF>=1.24.3, FastAPI>=0.110.1, Pydantic2; constraints và profile web/dev/MLX riêng |
| Hướng dẫn | Thiếu dựng/sử dụng Mac, test UI và quy trình đóng góp | README chính/Windows/Mac, CONTRIBUTING, corpus/fixture và hướng dẫn test được bổ sung |
| Sản phẩm F-01 - QA | Nhận câu có ID nguồn sai lẫn đúng hoặc không citation | Từ chối an toàn; nguồn hợp lệ vẫn hiển thị, marker ẩn trong câu |
| Sản phẩm F-02 - chỉ mục | Lỗi đọc nguồn/vector/SQL có thể làm mất chỉ mục cũ | Chuẩn bị vector trước; metadata/chunks/FTS cùng transaction; lỗi giữ hash/chunks/vector cũ, retry được; chặn batch thiếu vector |
| Sản phẩm F-03 - ICS thời gian | DTSTAMP sai định dạng | DTSTAMP UTC YYYYMMDDTHHMMSSZ |
| Sản phẩm F-04 - ICS văn bản | Ký tự/xuống dòng có thể phá cấu trúc lịch | Escape TEXT, fold 75 byte UTF8; giữ Unicode và không chèn thuộc tính mới |
| Sản phẩm F-05 - giờ OCR | So sánh chuỗi nhận/bỏ khoảng giờ sai | So sánh theo phút, chuẩn hóa 9:00/09:00, chặn cùng/đảo/ngoài miền |

Các mã GitHub F01-F04 và sản phẩm F-01-F-05 thuộc hai bộ phát hiện riêng.

## 2. Bằng chứng kiểm chứng

| Mốc | Kết quả | Bằng chứng |
| --- | --- | --- |
| YC-173 | Windows/Mac mỗi OS 110 feature +3 UI; history/PowerShell/demo đạt | [PR #1](https://github.com/ng-wngkh07/Study-Agent/pull/1), [CI 37904316913](https://github.com/ng-wngkh07/Study-Agent/actions/runs/37904316913), mã a6ca7ee |
| YC-175 | Profile mới cài trong môi trường riêng, pip check và 3 probe PDF/Pydantic/TestClient đạt; CI Windows/Mac 110 feature +3 UI mỗi OS/history đạt | [PR #2](https://github.com/ng-wngkh07/Study-Agent/pull/2), [CI 37911184856](https://github.com/ng-wngkh07/Study-Agent/actions/runs/37911184856), mã c879d02 |
| YC-175 MLX | Mac/Python3.13 cài profile và 34 dependency, pip check đạt; không inference/training | Nhật ký YC-175; profile/constraints MLX riêng |
| YC-177 local | RED 8/16; vector thiếu/lỗi đọc nguồn có RED riêng. Sau sửa: 128 feature gồm 18 ca mới, 14 ca index/retention/backfill, 3 UI đạt | Nhật ký YC-177; tests/test_audit_regressions.py |
| YC-177 ICS | Bộ đọc độc lập icalendar7.3.0 kiểm UTC/múi giờ/TEXT/Unicode/fold/không chèn thuộc tính đạt | Nhật ký YC-177; bộ đọc chỉ dùng để kiểm, không thêm dependency runtime |
| YC-177 CI cuối | Windows/Mac mỗi OS 128 feature +3 UI Node22; pip/demo, Windows PowerShell hợp đồng/DemoOnly, history đạt | [CI 37914078360](https://github.com/ng-wngkh07/Study-Agent/actions/runs/37914078360), mã 4430377 |
| YC-178 bảo mật | 196 file, 12 commit/237 blob, 2 PDF/ảnh demo, nội dung PR và 19 log CI: không phát hiện secret; không có tài sản nguồn/data riêng trong refs | Gitleaks8.30.1 và rà nội dung/metadata; nhật ký YC-178 |

Dependency runtime/dev/MLX được tách theo Python3.12/3.13; runtime không kéo test hoặc MLX trên Windows. Constraints hỗ trợ tái lập môi trường, không chứng nhận mọi OS/Python hoặc chất lượng model.

## 3. Review, quyền và phối hợp

Chính sách GitHub đọc lại ngày 09/10/2026: required approvals=0, last-push approval tắt; CI, nhánh cập nhật, hội thoại, admin và cấm force-push/xóa giữ. Người có quyền ghi có thể merge khi thỏa bảo vệ. Nhóm vẫn review chéo; TV4 điều phối merge/phát hành, TV6 kiểm tích hợp. Quy trình nhóm không tự tạo giới hạn quyền GitHub.

Mỗi PR ghi phạm vi, trước/sau, ảnh hưởng, log và kiểm đã/chưa chạy. Nguồn/index/model chính có một writer; sửa mã hoặc tài liệu không tự cấp quyền training hay phát hành candidate.

## 4. Thông tin chia sẻ và chất lượng tài liệu

Theo quyết định YC-179, giữ tên/email tác giả trong giấy phép và attribution Git. Nội dung phân công/giao việc dùng mã TV1-TV6; bảng ánh xạ và thông tin liên hệ thành viên quản lý riêng. Không công khai khóa/token, dữ liệu/lịch/hội thoại hoặc hồ sơ nội bộ.

Bản phân công 1.1 quy định vai trò, phạm vi, đầu ra, tiêu chí, review, bàn giao và điều kiện phát hành. Markdown và PDF được cập nhật cùng nhau; ví dụ branch/log dùng mã vai trò. Hồ sơ lịch sử giữ ID/ngày/kết quả cũ; việc biên tập không phải chạy lại các test lịch sử.

## 5. Vấn đề còn mở và giới hạn

- Q-01: câu trả lời model thiếu điều kiện dù trang nguồn đúng; citation ID hợp lệ không chứng minh nội dung đúng. Cần đánh giá theo đáp án chuẩn và nguồn.
- Full installer trên Windows mới, QA/VLM/MLX thật, toàn suite phụ thuộc dữ liệu riêng, corpus readiness và training chưa được nghiệm thu trong các mốc trên.
- P-01-P-03 hiệu năng: cần đo riêng truy xuất vector, nạp/sinh model và trạng thái dưới tải trước chọn thay đổi engine/worker. Chưa có kết quả cải thiện thực tế.
- Gói nguồn/model, manifest/approval/importer và release thật cần bàn giao/kiểm chứng riêng; không tạo metadata giả để công nhận hoàn tất.
- Run/SHA cũ không lấy được không bảo đảm đã purge mọi cache; không suy nguyên nhân mất hoặc suy CI hiện tại lỗi từ 404.

## 6. Tham chiếu vận hành

[README](../../README.md), [Windows](../../README_WINDOWS.md), [Mac](../../README_MAC.md), [CONTRIBUTING](../../CONTRIBUTING.md), [quy tắc](../../README_QUY_TAC.md), [phân công](PHAN_CONG_6_NGUOI.md).

Kết quả mới nhất xem [Team feature checks](https://github.com/ng-wngkh07/Study-Agent/actions/workflows/team-checks.yml) và checks của PR tương ứng. Báo cáo chỉ công nhận phạm vi đã có bằng chứng; các mục còn mở giữ đến khi có nghiệm thu riêng.
