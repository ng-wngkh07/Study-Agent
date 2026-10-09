# Lịch sử thay đổi ứng dụng Agent Học Tập

<!-- PROJECT_HISTORY_SCHEMA: 3 -->
- File chung duy nhất: `LICH_SU_DU_AN.md` ở gốc, push cùng mã nguồn.
- Cập nhật: 09/10/2026 11:13 (Asia/Ho_Chi_Minh, UTC+07); ISO: 2026-10-09T11:13:38.451245+07:00.
- Mục mới nhất: **[YC-170](#yc-170)**.
- Nhật ký chung có **4 mục**: 2 môi trường/chức năng (YC-167/170), 1 tổ chức/tài liệu (YC-168), 1 phát hành GitHub (YC-169).
- [Quy tắc](README_QUY_TAC.md), [phân công 6 người](docs/team/PHAN_CONG_6_NGUOI.md),
  [quy trình PR](CONTRIBUTING.md), [Windows](README_WINDOWS.md).

## Cách dùng

Đọc log liên quan lỗi/file/chức năng và main trước mọi thay đổi. Giữ sửa lỗi/tính năng
đã nghiệm thu; nếu thay quyết định, dẫn ID cũ và lý do. Mỗi PR thêm mục, tác giả ghi
ý chính của lỗi và phần sửa, **không copy prompt hoặc hội thoại**. Không tạo log riêng
cho mỗi người. Giải quyết xung đột bằng giữ cả mục hợp lệ, không ghi đè công việc khác.

Giữ ID/ngày cũ. Hiệu chỉnh thông tin bằng lý do và thời gian sửa; không xóa lịch sử.
YC-168 biên tập YC-167 theo yêu cầu mới; bản trước hiệu chỉnh và 166 mục hội thoại cũ
được bảo toàn local để truy nguyên, không phải các mục cần sao chép vào Git.

## Quyết định đang áp dụng

| Mốc | Quyết định | Trạng thái |
| --- | --- | --- |
| YC-168 thay phân công nhóm ở YC-167 | 3 chủ trì chức năng + huấn luyện + giao diện/môi trường + kiểm thử/tài liệu | Phương án 6 người đã lập để nhóm chốt. |
| YC-168 hiệu chỉnh cách ghi YC-154/167 | Nhật ký tóm tắt lỗi/thay đổi sản phẩm; không lưu prompt; đọc log trước sửa | Đã áp dụng cho file chung và quy tắc. |
| YC-164/167, YC-168 bổ sung PDF | Mã/UI/test/config/docs/log/metadata/PDF phân công qua Git; dữ liệu/model thật riêng | YC-169 cho phép đưa mã lên repo Study-Agent; dữ liệu thật giữ riêng. |
| Cổng nguồn/model hiện có | Một writer chính; toàn nguồn review, audit live complete: true và đánh giá độc lập trước kích hoạt | Giữ nguyên; lượt YC-168 không index/train. |

## Mẫu mục mới

```markdown
<a id="log-ID"></a>
### <ID duy nhất, ví dụ LOG-YYYYMMDD-chucnang-maviec-ten> - DD/MM/YYYY HH:mm (UTC+07)
- Người thực hiện / loại thay đổi:
- Lỗi hoặc mục tiêu (ý chính):
- Trước / sau thay đổi:
- Phần/file sửa và cách xử lý:
- Log/phiên bản liên quan; lý do thay quyết định nếu có:
- Ảnh hưởng/phối hợp với phần còn lại:
- Kiểm thử: môi trường/model/data version, ca tái hiện/hồi quy, kết quả:
- Trạng thái: PASS / FAIL / đang làm / NOT_RUN / N/A có lý do:
- Giới hạn, lỗi còn lại, rollback/bước tiếp:
```

## Nhật ký chung

<a id="yc-167"></a>
### YC-167 - 09/10/2026 10:02 (UTC+07)

- Người thực hiện: Codex; loại: môi trường phát triển và sửa tích hợp model.
- Lỗi/mục tiêu: mã web có phụ thuộc Unix, đường dẫn cố định và UI/health/summary
  giả định MLX; cần môi trường Windows cho các chủ trì chức năng, Mac giữ training.
- Trước/sau: trước khó nhập/chạy trên Windows và chọn sai backend; sau có launcher,
  demo độc lập, khóa file native, đường dẫn cấu hình và model UI/health theo môi trường.
- Phần sửa: config/server/dialogue/gpu_lock/trained_client/topic_summarizer/timetable_store;
  file_lock mới; UI model; run.py guard training; dev/PowerShell, requirements/pytest,
  fixtures, CI và các README/quy tắc. scripts/service.sh bỏ PLIST_SRC không dùng.
- Kiểm thử tại mốc 09/10/2026: 109 test feature và 20 test Mac đạt (hai tập có phần trùng),
  dependency/parse/link/57 ca Git boundary đạt; demo HTTP/UI 2 nguồn tổng hợp, 5 đoạn,
  0 vector. Windows native/PowerShell/CI và QA/VLM thật NOT_RUN, không coi đã nghiệm thu.
- Ảnh hưởng: giữ mặc định MLX Mac, corpus/index/model thật không được ghi bởi việc này;
  Ollama Windows là bản phát triển, chất lượng không đồng nhất adapter Mac.
- Trạng thái: đã tích hợp local bộ chuẩn bị; chưa tạo repo/commit/push, không train/restart dịch vụ.
- Liên quan: YC-164/166 về Git; phân công 4 người và cách lưu prompt được YC-168 thay thế.
- Hiệu chỉnh 09/10/2026 10:28 (UTC+07), theo YC-168: tóm tắt thành lịch sử sản phẩm, bỏ phần
  prompt và metadata vận chuyển khỏi file chung; giữ ID/ngày, nội dung sửa/kiểm thử và
  bản trước hiệu chỉnh local. Đây không phải lần chạy lại các test nói trên.

<a id="yc-168"></a>
### YC-168 - 09/10/2026 10:28 (UTC+07)

- Người thực hiện: Codex; loại: tổ chức nhóm, tài liệu và quy tắc nhật ký.
- Mục tiêu: nhóm mở rộng 4 lên 6; chỉ một người huấn luyện; giao việc rõ trên ba chức
  năng hiện có, bảo vệ phần chung và đổi log từ lịch sử prompt sang lịch sử ứng dụng.
- Trước/sau: trước 3 chủ trì + Khải và log còn chứa prompt; sau giữ 4 nhiệm vụ gốc,
  thêm giao diện/môi trường và kiểm thử/nghiệm thu/tài liệu, log tóm tắt ý chính lỗi/sửa.
- Phần sửa: PDF phân công 8 trang, docs/team/PHAN_CONG_6_NGUOI.md, README_QUY_TAC,
  CONTRIBUTING, README/Windows, template PR, AGENTS local, .gitignore và file log này.
  Bảng 4 người được đánh dấu mốc cũ, liên kết chuyển sang bảng 6 người.
- Quy tắc bổ sung: đọc log trước sửa; chỉ sửa đúng phạm vi; báo/phối hợp khi chạm phần
  chung hoặc cần chỉnh local; giữ tương thích và kiểm các chức năng ảnh hưởng; tên branch
  theo loại/phạm vi/mã việc/người; review chéo rồi Khải merge; một nhật ký chung có ngày giờ.
- Đề xuất: đánh dấu trang cục bộ và sao chép trích dẫn có nguồn; chưa chốt triển khai.
  .ics/xung đột lịch/hội thoại/tóm tắt đã có, không xem là tính năng mới.
- Ảnh hưởng: chỉ tài liệu/quy tắc; không đổi mã sản phẩm, corpus/model, không chạy training.
- Kiểm chứng/trạng thái: PASS PDF 8 trang, đã render và xem đủ 8 trang, chữ tiếng Việt/
  bố cục rõ; link tài liệu, ID log và 12 ca ranh giới Git đạt. Mã app/static/scripts và
  archive 166 mục không đổi theo SHA256. Hồ sơ kiểm chứng: docs/project/team-six-2026-10-09/.
  RED/test sản phẩm/handoff/training N/A vì chỉ sửa tài liệu, không đổi hành vi mã.
- Hoàn tất kiểm chứng: 09/10/2026 10:34 (UTC+07). Phương án và PDF đã tạo; hai cải tiến chưa triển khai.
- Giới hạn: phân công mới là phương án đề xuất; GitHub protection chưa cấu hình,
  không commit/push. Những check Windows/model thật cần nghiệm thu riêng.

<a id="yc-169"></a>
### YC-169 - 09/10/2026 11:03 (UTC+07)

- Người thực hiện: Codex; loại: phát hành mã nguồn để làm nhóm.
- Mục tiêu: đưa tài sản dùng chung lên ng-wngkh07/Study-Agent theo phạm vi YC-164/167/168.
- Trước/sau: repo chỉ có LICENSE; bản chuẩn bị bổ sung mã app/UI, scripts chung, tests/demo,
  dependency, cấu hình/CI, tài liệu 6 người, PDF và nhật ký chung. Giữ LICENSE gốc.
- Phần sửa: .gitignore loại ba script thử nghiệm/review/monitor cá nhân; README biên tập
  cho clone sạch, bỏ hướng dẫn chat cá nhân và cấu hình thử nghiệm cũ. Không xóa các file local.
- Ảnh hưởng: nguồn thật src, data/DB/vector/model, .env, hồ sơ docs/project, cache và tích hợp
  cá nhân không đi vào commit. Lần đưa mã đầu tiên được yêu cầu rõ; sau đó dùng branch/PR.
- Kiểm chứng: snapshot riêng, allow/deny và rà bí mật trước push; Python 3.12 feature 109 PASS,
  demo 2 nguồn/5 đoạn/0 vector. Readback commit đầu xác nhận đủ 189 blob khớp GitHub.
- Trạng thái: đã push 189 file lên main (446b829, bản sửa 13771b5); CI Windows/Mac PASS. Không train,
  restart dịch vụ Mac hoặc ghi corpus chính; dữ liệu do bên đang giữ quyền ghi quản lý.

<a id="yc-170"></a>
### YC-170 - 09/10/2026 11:03 (UTC+07)

- Người thực hiện: Codex; loại: bộ cài Windows và sửa lỗi tương thích Python.
- Mục tiêu: thành viên chỉ làm theo README, không phải tự tìm bản cài phần mềm/model.
- Trước/sau: setup đòi Python cài trước và Ollama/model tải thủ công; sau đọc danh sách
  requirements-windows-tools.json, cài phần thiếu bằng WinGet, tạo venv, cài requirements,
  chuẩn bị model QA/embedding/VLM. DemoOnly bỏ model; giữ .env và phần mềm đã có.
- Phần sửa: setup_windows.ps1, scripts/windows_setup.ps1, manifest, README Windows, CI
  và tests/windows_setup_contract.ps1. Python dependency tiếp tục trong requirements*.txt.
- Lỗi phát hiện: import app.training_data trên Python 3.12 lỗi NameError Optional; thêm
  Dict/Optional từ typing để web nạp được. Tái hiện trước sửa; import web và 109 feature
  test sau sửa PASS trên Python 3.12. Không đổi logic training hoặc mẫu nguồn.
- Kiểm chứng: PowerShell parse và 8 hợp đồng offline PASS (reuse/install/failure/unresolved/
  native error/model alias/model sai). CI Windows thêm setup DemoOnly và các check này.
- Giới hạn: full install trên máy Windows trắng, bootstrap WinGet, tải model/QA/ảnh thật
  chưa chạy; CI demo không thay nghiệm thu full. .exe/model không push; manifest tải từ
  nguồn đã chỉ định. Mac không cài tool Windows và không bị đổi provider/model.
- Chẩn đoán CI lần đầu: Mac PASS, Windows 92 PASS/17 FAIL do flock nhận đối tượng
  file nhưng Windows CRT đòi descriptor int. Bộ cài DemoOnly/PowerShell trên Windows
  đã PASS; lỗi nằm ở lớp khóa, không phải tải dependency.
- Sửa sau CI: app/file_lock chuyển file object sang fileno ở nhánh Windows; thêm ca
  regression tái hiện FAIL trước sửa rồi GREEN, feature 110 PASS trên Mac/Python3.12.
  Bộ cài còn xử lý launcher có sẵn nhưng chưa có 3.12, bỏ alias Microsoft Store;
  có kiểm hợp đồng fallback. tests/test_platform_support và Windows setup contract bổ sung.
- Kiểm chứng sau sửa 09/10/2026 11:13 (UTC+07): commit 13771b5,
  [GitHub Actions](https://github.com/ng-wngkh07/Study-Agent/actions/runs/37882594844) PASS:
  Windows 110 test/1 warning; Mac 110 test/6 warning. Windows PowerShell native parse,
  8 hợp đồng và setup DemoOnly đạt. Warning thư viện không phải test lỗi.
- Trạng thái: hoàn tất mã/bộ cài và xuất bản GitHub trong cùng đợt khởi tạo; bản cập nhật
  README/log ghi lại kết quả đã chạy. Full install trên máy Windows mới, model inference
  và MLX training NOT_RUN; không suy rộng CI demo thành nghiệm thu các phần này.
