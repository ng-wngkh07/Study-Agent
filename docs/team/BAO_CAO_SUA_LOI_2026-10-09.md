# Kết quả sửa lỗi từ báo cáo kiểm tra GitHub — YC-173

Ngày: 09/10/2026. Baseline: main `871d4dc`. Phạm vi: F01–F04 của YC-171.

| Mục | Bản sửa và kiểm chứng |
| --- | --- |
| F01 | Tra cứu nguồn văn bản dùng nhãn phần, mở sẵn trích đoạn, không tạo nút PDF khi API không có PDF. PDF vẫn giữ ảnh gốc và mở đúng trang bằng ID số. RED 2/3 lỗi trên baseline; GREEN 3/3 kiểm giao diện sau sửa. |
| F02 | Khôi phục LICENSE MIT gốc, khớp từng byte với bản xuất bản được giữ. |
| F03 | Đã bật bảo vệ main cho cả admin: 1 approval khác tác giả, duyệt lại sau push, 3 check GitHub Actions (`features (windows-latest)`, `features (macos-latest)`, `history`), nhánh cập nhật và giải quyết hội thoại. Cấm force-push/xóa main. Đã đọc lại API. |
| F04 | README_WINDOWS dẫn trang workflow đang dùng và run 37887196815. Ghi rõ run cũ 37882594844 trả 404, không suy là CI thất bại. Giữ lịch sử cũ. |

Kiểm local: Python 3.12 feature 110 PASS; Node 3 kiểm giao diện PASS. Browser đã kiểm Markdown và PDF, chuyển sang QA và lịch, không lỗi console. CI chạy lại các kiểm Python/UI trên Windows và Mac; history check chạy trên PR. Xem [CI hiện hành](https://github.com/ng-wngkh07/Study-Agent/actions/workflows/team-checks.yml).

Bản sửa được đưa lên nhánh `fix/shared/yc173-khai` và PR, cần review của người khác trước merge main. Không thay quyền ghi corpus/model hay chạy huấn luyện.

Các phần chưa nghiệm thu vẫn giữ rõ: cài đầy đủ trên Windows mới, chất lượng QA/ảnh/model thật, bàn giao dữ liệu/importer/release, training và toàn bộ 476 ca phụ thuộc dữ liệu riêng. Không tạo gói/release giả hoặc dùng test mock để công nhận chất lượng model. Run/commit cũ không được phục hồi và nguyên nhân mất vẫn chưa xác minh.

## Kết quả CI và xuất bản

[PR #1](https://github.com/ng-wngkh07/Study-Agent/pull/1), bản mã `a6ca7ee`: [CI 37904316913](https://github.com/ng-wngkh07/Study-Agent/actions/runs/37904316913) PASS. Windows và Mac đạt 110 feature + 3 kiểm giao diện mỗi hệ điều hành; history PR, PowerShell và demo Windows đều đạt. GitHub readback khớp toàn bộ 190 blob; không có dữ liệu/hồ sơ riêng.

Main được bảo vệ và PR chờ reviewer khác tác giả; chưa merge. Kết quả trên thuộc SHA nêu rõ; cập nhật tài liệu sau đó không thay mã sản phẩm/test.


## Bổ sung YC-175 — README, dependency và CONTRIBUTING

Đối chiếu phát hiện YC-174; giữ nguyên kết quả sửa UI/giấy phép/CI của YC-173 ở trên.

| Phát hiện | Thay đổi |
| --- | --- |
| PyMuPDF minimum chưa có module pymupdf | Minimum 1.24.3 và constraints dùng bộ đã kiểm |
| Mã dùng Pydantic2 nhưng dependency chưa yêu cầu | Khai pydantic>=2,<3 trực tiếp |
| FastAPI/Starlette cũ với HTTPX mới hỏng TestClient | Minimum FastAPI0.110.1, cố định dependency graph tương thích |
| Thiếu phân biệt web/test/MLX | requirements runtime/dev, Windows wrapper và MLX Mac riêng; constraints Python3.12/3.13 |
| README chưa đủ dựng/sử dụng dự án | Main có kiến trúc/profile/cấu hình/test/API/license; Mac guide mới, Windows thêm nguồn→index→dùng, quy tắc main được cập nhật |
| CONTRIBUTING thiếu bước thực hành | Bổ sung Issue, onboarding, branch, test, log, commit/PR, reviewer đủ quyền, xử lý xung đột và tài sản |

`CONTRIBUTING.md` giữ đúng vai trò hướng dẫn đóng góp, dẫn README cho cài/sử dụng
và quy tắc dự án cho trách nhiệm. Corpus README/fixture README giữ đúng vai trò;
không mô tả importer chưa có thành tính năng đã hoàn thành. File tools Windows hiện
khớp installer/model nên không đổi; Node cho test UI được hướng dẫn cài riêng, không
bắt người chạy web cài Node. `.gitignore` chỉ thêm ngoại lệ 5 file hướng dẫn/dependency mới.

Kiểm chứng trước push: môi trường Python3.12 mới cài profile Windows/dev, pip check
và ba ca import/Pydantic/API TestClient PASS; ba phiên bản lỗi cũ bị từ chối; runtime
không kéo pytest/httpx/MLX. 110 feature PASS (6 cảnh báo dependency), 3 UI PASS trên
Node24 local; CI chạy Node22 Windows/Mac. Venv Mac3.13 riêng cài 34 dependency của
MLX0.32.2/MLX-LM0.31.3/Transformers5.17.0, pip check PASS, chỉ đọc metadata.
Kiểm marker không cài MLX trên Windows và Git allow/deny PASS. Không sửa mã app/UI,
không ghi corpus/model/adapter hoặc khởi chạy inference/training.

Profile MLX theo JSONL local đã duyệt mà pipeline dùng; không kéo optional dataset-loader
và gói phụ ngoài phạm vi. Constraints cố định phiên bản, không phải giấy chứng nhận chất
lượng model hay bảo đảm mọi OS/Python khác. Nâng thư viện cần kiểm và cập nhật cùng profile.

Giới hạn vẫn giữ: model thật, full installer máy Windows mới, toàn suite, corpus readiness
và training chưa được nghiệm thu trong đợt này. CI hiện hành xem
[Team feature checks](https://github.com/ng-wngkh07/Study-Agent/actions/workflows/team-checks.yml).

## Làm rõ quyền merge — YC-176

Tại bản kiểm YC-173/174 trước readback bên dưới, cần một approval từ người khác có quyền ghi; tác giả không tự duyệt.
Nếu bỏ approval và yêu cầu duyệt push cuối, PR đạt CI có thể merge bởi người có quyền ghi.
Quy định Khải merge trong tài liệu là quy trình nhóm, chưa là giới hạn quyền được GitHub
cưỡng chế. Hiện chưa thay protection/quyền/reviewer theo các câu hỏi làm rõ này.

### Readback chính sách mới — 2026-10-09T16:24:45.490701+07:00

PR #1 đã được chủ repo merge lúc 16:10:20 UTC+07, main fdd9adf. Required approvals đã
về 0, last-push approval tắt; CI/nhánh cập nhật/hội thoại/admin/cấm force-push/xóa còn giữ.
Đã có hai collaborator ngoài chủ có quyền ghi, có thể merge khi điều kiện đạt.
Codex không đổi policy/quyền hoặc tự merge; bản README/dependency/CONTRIBUTING mới
chuyển sang nhánh codex/fix-project-guides để mở PR riêng. Trạng thái review bắt buộc
trong các mục YC-173/174 là lịch sử trước lần thay đổi này.

### Kết quả phát hành YC-175 — 2026-10-09T16:28:28.217575+07:00

Đã đẩy bản sửa lên [PR #2](https://github.com/ng-wngkh07/Study-Agent/pull/2),
nhánh codex/fix-project-guides đồng bộ main fdd9adf.
[CI PR 37911184856](https://github.com/ng-wngkh07/Study-Agent/actions/runs/37911184856)
trên c879d02 PASS: Windows/Mac mỗi OS 110 feature và 3 UI trên Node22; pip check/demo
PASS, Windows PowerShell parse/contract và installer DemoOnly PASS, history PASS.
Giữ chính sách/quyền được đọc lại ở trên; không tự merge. File phân công nhóm cũng
được cập nhật câu trạng thái bảo vệ nhánh; PDF phân công là bản chụp tại lần xuất cũ.
Các giới hạn model/full installer/corpus/training vẫn NOT_RUN như đã nêu.

## Tiếp tục sửa lỗi sản phẩm — YC-177 (2026-10-09T16:49:15.112561+07:00)

Các mã dưới đây thuộc audit sản phẩm 08/10, khác F01–F04 GitHub ở đầu báo cáo.

| Mục | Kết quả sửa |
| --- | --- |
| F-01 QA attribution | Chặn toàn bộ đáp án nếu lẫn ID không truy xuất hoặc thiếu citation; giữ nguồn hợp lệ và từ chối an toàn |
| F-02 reindex | Chuẩn bị vector trước, metadata/chunks/FTS trong transaction; rollback giữ chỉ mục/hash/vector cũ, retry thay được; lỗi đọc nguồn không xóa chỉ mục cũ; batch thiếu vector không được commit |
| F-03 ICS timestamp | DTSTAMP UTC dạng YYYYMMDDTHHMMSSZ |
| F-04 ICS TEXT | Escape newline/backslash/comma/semicolon, fold theo 75 UTF8 octet; không thêm property từ nội dung |
| F-05 giờ OCR | So sánh giờ theo phút, nhận 9:00/09:00, không nhận cùng/đảo/ngoài miền |

RED 8/16 ca thất bại trên baseline; vector thiếu và lỗi extraction tái hiện riêng trước sửa. Sau sửa, 18 ca hồi quy mới được đưa vào feature
suite: local 128 PASS, thêm 14 ca index/retention/backfill PASS và 3 UI PASS. Parser
độc lập icalendar7.3.0 xác nhận timestamp/timezone/Unicode/TEXT roundtrip và không có
property được chèn. Parser chỉ cài tmp, không đổi profile dependencies. CI chạy các
ca mới trên Windows/Mac. CI 37913090332/e6d8425 đã PASS 127 feature +3 UI mỗi OS/history; phần bổ sung extraction (128 feature) tiếp tục kiểm trên PR2/checks.

Q-01 về nội dung model và các giới hạn full installer/model/corpus/training chưa
nghiệm thu; ID nguồn hợp lệ chưa chứng minh câu đúng ngữ nghĩa. Không chạm dữ liệu
riêng/job corpus hoặc sửa mốc audit 08/10 đã đóng. Không tự merge.
