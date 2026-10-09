# Lịch sử thay đổi ứng dụng Agent Học Tập

<!-- PROJECT_HISTORY_SCHEMA: 3 -->
- File chung duy nhất: `LICH_SU_DU_AN.md` ở gốc, push cùng mã nguồn.
- Cập nhật: 09/10/2026 17:34 (Asia/Ho_Chi_Minh, UTC+07); ISO: 2026-10-09T17:34:05.950966+07:00.
- Mục mới nhất: **[YC-179](#yc-179)**.
- Nhật ký chung có **13 mục**: 5 môi trường/chức năng (YC-167/170/173/175/177), 3 tổ chức/tài liệu (YC-168/172/179), 1 phát hành GitHub (YC-169), 3 rà soát/nghiệm thu (YC-171/174/178), 1 làm rõ quyền/quy trình (YC-176).
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

| YC-179 làm rõ YC-178 | Giữ tên/email tác giả và attribution Git; phân công/giao việc dùng TV1-TV6; bảng ánh xạ quản lý riêng | Đã áp dụng; thay đề xuất ẩn toàn bộ danh tính ở YC-178, không đổi lịch sử Git. |

  ## Mẫu mục mới

  ```markdown
  <a id="log-ID"></a>
  ### <ID duy nhất, ví dụ LOG-YYYYMMDD-chucnang-maviec-tvN> - DD/MM/YYYY HH:mm (UTC+07)
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
- Trước/sau: trước 3 chủ trì + TV4 và log còn chứa prompt; sau giữ 4 nhiệm vụ gốc,
  thêm giao diện/môi trường và kiểm thử/nghiệm thu/tài liệu, log tóm tắt ý chính lỗi/sửa.
- Phần sửa: PDF phân công 8 trang, docs/team/PHAN_CONG_6_NGUOI.md, README_QUY_TAC,
  CONTRIBUTING, README/Windows, template PR, AGENTS local, .gitignore và file log này.
  Bảng 4 người được đánh dấu mốc cũ, liên kết chuyển sang bảng 6 người.
- Quy tắc bổ sung: đọc log trước sửa; chỉ sửa đúng phạm vi; báo/phối hợp khi chạm phần
  chung hoặc cần chỉnh local; giữ tương thích và kiểm các chức năng ảnh hưởng; tên branch
  theo loại/phạm vi/mã việc/người; review chéo rồi TV4 điều phối merge; một nhật ký chung có ngày giờ.
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

<a id="yc-171"></a>
### YC-171 - 09/10/2026 15:04 (UTC+07)

- Người thực hiện: Codex; loại: rà soát và nghiệm thu tài sản GitHub.
- Mục tiêu: đối chiếu các thư mục Study-Agent đã upload với phạm vi/yêu cầu YC-164–170
  và phân công 6 người; phân biệt có mã, test demo đạt và nghiệm thu sản phẩm thật.
- Trước/sau: trước checkpoint dựa mốc e0aac7a; kiểm trực tiếp xác nhận main hiện tại
  871d4dc37f17e293b0dda54c017d579f84b5ade1 có 187 file. Không sửa mã sản phẩm;
  bổ sung kết quả kiểm tra, các thiếu sót và giới hạn. Không suy nguyên nhân thay lịch sử remote.
- Phần đọc: tree toàn repo, README/quy tắc/log/phân công, app server/config/lookup/lịch/
  cổng corpus-training, static/document-lookup, scripts/dev/installer/CI và tests liên quan.
- Kiểm chứng: clone riêng; Python3.12 110 feature + 29 corpus/provenance/adapter/balance PASS;
  Python3.14 110 feature PASS (trùng ca, không cộng lại). CI run 37887196815 đúng SHA hiện tại
  Windows/Mac 110 PASS mỗi hệ; Windows parse/8 hợp đồng/setup DemoOnly PASS. Toàn tập collect
  476 ca, không chạy toàn bộ. Cú pháp 148 Python, shell, 24 ca Git boundary, links local PASS.
  Demo 2 nguồn/5 đoạn/0 vector; browser nạp và chuyển ba chế độ, FTS hoạt động khi model bị cô lập.
- Lỗi còn lại: UI tạo nút PDF cho study_demo.md dù API pdf_url=null, mở trả 404
  (static/document-lookup.js:116–122/136); LICENSE gốc thiếu; main protected=false/rulesets rỗng.
  Link CI cũ 37882594844 trả 404; checkpoint commit cũ không tìm được trên repo hiện tại.
- Kết luận: phần chia sẻ mã/demo phần lớn đạt; chưa công nhận toàn ứng dụng/quy trình dữ liệu
  hoàn tất. corpus mới README, chưa gói/manifest/importer giao nhận; full Windows install,
  QA/VLM thật, corpus readiness live/training/release NOT_RUN hoặc chưa xác minh.
  Thiếu src/data/DB/vector/model/.env/hồ sơ cá nhân trong Git là đúng ranh giới tài sản.
- Ảnh hưởng: chỉ báo cáo/lịch sử/checkpoint local; không ghi corpus chính, dùng GPU thật,
  thay provider/model, commit/push hoặc cấu hình quyền GitHub. Triển khai/sửa/handoff N/A vì audit.
- Trạng thái: hoàn tất lượt kiểm tra; các thiếu sót đã ghi, chưa sửa. Hồ sơ local:
  docs/project/github-audit-2026-10-09/BAO_CAO.md và verification.json.
- Bằng chứng CI hiện hành: https://github.com/ng-wngkh07/Study-Agent/actions/runs/37887196815.
- Cập nhật kết quả: 2026-10-09T15:04:58.296591+07:00. Cần sửa UI/khôi phục LICENSE/cập nhật link và áp dụng bảo vệ main,
  sau đó nghiệm thu installer/model/dữ liệu theo tiêu chí; không coi test mock là chất lượng model.

<a id="yc-172"></a>
### YC-172 - 09/10/2026 15:10 (UTC+07)

- Người thực hiện: Codex; loại: kiểm tra CI và sửa liên kết bằng chứng trong tài liệu.
- Mục tiêu: kiểm lỗi CI; làm rõ liên kết CI cũ trả 404 theo phát hiện YC-171.
- Chẩn đoán: workflow Team feature checks đang active; run 37887196815 trên main
  871d4dc hoàn tất success, Windows/Mac 110 test đạt. Run 37882594844 trả 404:
  GitHub không tìm thấy lần chạy được dẫn, chưa xác định nguyên nhân mất run;
  không suy là CI/test hiện tại thất bại. History job skipped đúng điều kiện vì event push.
- Trước/sau: README_WINDOWS dẫn run cũ không còn truy cập; sau dùng trang workflow
  cho kết quả mới nhất, kèm run/SHA hiện hành đã kiểm và ghi chú về liên kết cũ.
- Phần/file sửa: README_WINDOWS.md; bổ sung mục lịch sử này và checkpoint local.
  Giữ nguyên YC-170 và kết quả lịch sử tại ngày cũ; không thay link cũ trong archive.
- Kiểm chứng: API đọc runs/jobs/workflow và run cũ; trang workflow và run hiện tại truy cập được;
  kiểm link, diff và bảo toàn mục cũ. Test sản phẩm/RED–GREEN/handoff N/A vì chỉ tài liệu,
  không có CI đang đỏ cần sửa mã. Cảnh báo dependency không được báo thành test lỗi.
- Ảnh hưởng/trạng thái: sửa tài liệu local hoàn tất; workflow/mã/model/corpus không đổi,
  chưa commit/push. Cập nhật kết quả 2026-10-09T15:10:46.016993+07:00; hồ sơ local ci-link-repair-2026-10-09/.
- Giới hạn: không tuyên bố đã phục hồi run cũ; có thể xem bằng chứng của run hiện tại tại
  https://github.com/ng-wngkh07/Study-Agent/actions/runs/37887196815.

<a id="yc-173"></a>
### YC-173 - 09/10/2026 15:18 (UTC+07)

- Người thực hiện: Codex; loại: sửa lỗi tra cứu, tài liệu/giấy phép và bảo vệ GitHub.
- Mục tiêu/log liên quan: xử lý F01–F04 trong báo cáo YC-171, đưa bản sửa lên GitHub;
  tiếp nối sửa link YC-172. Baseline main 871d4dc; triển khai trên bản sao cách ly.
- Trước/sau: nguồn Markdown từng tạo nút PDF trả 404; sau chỉ tạo link khi có PDF,
  nguồn văn bản hiện phần/trích đoạn mở sẵn và câu hỏi đúng đơn vị. PDF vẫn mở đúng trang,
  link được tạo từ ID số để không dùng URL tùy ý trả về.
- Phần sửa: static/document-lookup.js, tests/document_lookup_ui.test.cjs, CI bổ sung 3 kiểm
  giao diện Windows/Mac; khôi phục LICENSE MIT gốc từ bản xuất bản đã giữ, byte khớp.
  README_WINDOWS dùng trang workflow/link hiện hành; không thay kết quả lịch sử YC-170.
- GitHub: main được bảo vệ, áp dụng cả admin; cần 1 approval khác tác giả, duyệt lại khi có
  push mới, 3 check features Windows/Mac/history đúng GitHub Actions, nhánh cập nhật và
  hội thoại đã giải quyết. Cấm force-push/xóa main; không cấp quyền người/app mới.
- Kiểm chứng: RED trên mã gốc 2/3 kiểm giao diện thất bại đúng lỗi; GREEN 3/3 sau sửa.
  Python 3.12 feature 110 PASS; UI browser kiểm Markdown/PDF, chuyển QA và lịch, không lỗi
  console; API PDF/ảnh nguồn và readback protection. CI PR 37904316913 trên a6ca7ee
  PASS Windows/Mac 110 feature + 3 UI mỗi OS và history; PowerShell/demo Windows PASS.
- Review: Codex đọc diff/caller và kiểm riêng sau triển khai; không gọi là review độc lập
  của thành viên. Codex thực hiện trên bản sao độc quyền; corpus/model/GPU không đổi.
- Trạng thái/phát hành: bản sửa qua nhánh fix/shared/yc173-khai và PR; main chờ reviewer
  theo quy tắc nhóm, không tự merge. PR: https://github.com/ng-wngkh07/Study-Agent/pull/1.
  Readback 190 blob khớp commit a6ca7ee; nhật ký/báo cáo chung đi cùng mã, bằng chứng local giữ riêng.
- Giới hạn: không khôi phục run/commit cũ đã mất. Full Windows install/model thật/476 ca/
  gói dữ liệu thật/training vẫn NOT_RUN hoặc chưa nghiệm thu; đây là giới hạn kiểm chứng,
  không có bằng chứng cho phép huấn luyện. Cập nhật kết quả: 2026-10-09T15:23:47.104446+07:00.


<a id="yc-174"></a>
### YC-174 - 09/10/2026 15:54 (UTC+07)

- Người thực hiện: Codex; loại: rà soát merge, tài liệu và dependency.
- Mục tiêu/log liên quan: giải thích PR YC-173 bị chặn merge; đối chiếu toàn bộ README
  và requirements đã upload với mã/cách cài thực tế. Không mở yêu cầu huấn luyện.
- Trước/sau: CI bản a893eb3 đạt, nhưng PR chưa review; API xác nhận bảo vệ main yêu cầu
  một approval khác tác giả/người push, áp dụng admin; repo chỉ có tài khoản tác giả có
  quyền ghi. Đã hướng dẫn mời thành viên, review Approve sau push cuối rồi merge.
  Không thay protection/quyền người dùng hoặc tự merge; thiếu review không phải lỗi CI.
- File/module đã đọc: 5 README, 3 requirements, CONTRIBUTING/log, app/server/config/
  pdf_extractor/trained_client/mlx_infer/fine_tune/token_auditor/vision_ocr, scripts/dev,
  run.py, installer Windows, workflow và test API. README đủ nền demo/quy tắc nhưng
  còn thiếu dựng Mac/local/MLX, nguồn→index→dùng, test Node; quy tắc main chưa cập nhật.
- Chẩn đoán: requirements cho phép PyMuPDF1.24.0 thiếu module pymupdf; chưa khai Pydantic2
  dù dùng field_validator; FastAPI0.110.0/Starlette0.36.3 với HTTPX0.28.1 hỏng TestClient.
  Cài nguyên requirements với constraints hợp lệ và pip check PASS vẫn tái hiện 3 FAIL.
- Kiểm chứng phương án riêng: Python3.12/Mac, FastAPI0.110.1/Pydantic2.7.4/PyMuPDF1.24.3/
  Starlette0.37.2/HTTPX0.28.1: 3 ca tương thích + pip check PASS; 110 feature PASS/1 warning
  trên snapshot a893eb3, nguồn/data tạm, không endpoint model thật. Chưa áp dụng dependency.
- Ảnh hưởng thiết kế: cần yêu cầu API/version trực tiếp, bộ constraints đã kiểm và
  profile MLX Mac tái tạo runtime; giữ Windows không MLX và ranh giới dữ liệu/model.
  README thư mục corpus/fixture phù hợp vai trò, không coi cấu trúc quy ước là importer đã có.
- Phần sửa: chỉ báo cáo local docs/project/readme-requirements-audit-2026-10-09/BAO_CAO.md,
  nhật ký/checkpoint. Triển khai sản phẩm/RED–GREEN/handoff N/A vì kiểm tra; không đổi code,
  corpus/GPU/provider/model, không push thêm. Windows candidate/full install/model thật/
  full suite/readiness/training NOT_RUN; các hướng sửa tài liệu/dependency là đề xuất.
- Trạng thái: hoàn tất kiểm tra; PR vẫn chờ reviewer hợp lệ, các thiếu sót mới chưa sửa.
  Cập nhật kết quả: 2026-10-09T15:54:56.958075+07:00; bằng chứng runtime/API/CI và inventory trong cùng thư mục báo cáo.


<a id="yc-175"></a>
### YC-175 - 09/10/2026 16:16 (UTC+07)

- Người thực hiện: Codex; loại: sửa dependency và hướng dẫn dự án/đóng góp.
- Mục tiêu/log liên quan: xử lý các phát hiện YC-174, review CONTRIBUTING đúng vai trò
  hướng dẫn đóng góp và đẩy bản sửa GitHub. Baseline PR a893eb3; giữ bản sửa YC-173.
- Trước/sau: requirements từng cho phép 3 tổ hợp hỏng import/API test; sau khai Pydantic2,
  nâng minimum PyMuPDF/FastAPI và cố định phiên bản/dependency graph. Tách runtime web,
  dev/test và runtime MLX Mac; Windows wrapper vẫn cài đủ feature-test như trước.
- File sửa: requirements.txt, requirements-dev.txt, requirements-windows.txt,
  requirements-mlx.txt, constraints-web-py312.txt, constraints-mlx-py313.txt;
  workflow thêm pip check/cache các file cấu hình; .gitignore chỉ cho phép 5 file mới.
- Tài liệu: README chính thêm kiến trúc/sử dụng/profile/test/API/giấy phép; README_MAC
  mới hướng dẫn Python3.12/Ollama/.env/local-index/MLX3.13/OCR/troubleshooting; Windows
  thêm nguồn→index→dùng và test Node; quy tắc/phân công phản ánh main đã bảo vệ và policy mới; corpus/fixture
  giữ đúng vai trò, dẫn thao tác nguồn riêng. CONTRIBUTING trước đúng quy trình nhóm
  nhưng thiếu onboarding/Issue/test/PR/review cụ thể; sau đủ các bước và ranh giới tài sản.
- Kiểm chứng local: venv mới Python3.12 cài profile Windows/dev thành công, pip check
  và 3 ca PDF/Pydantic/TestClient PASS; 110 feature PASS (6 cảnh báo dependency),
  3 UI PASS trên Node24; CI dùng Node22 để kiểm Windows/Mac. Venv riêng Mac3.13
  cài MLX0.32.2/MLX-LM0.31.3/Transformers5.17.0 và 34 phụ thuộc thành công,
  pip check PASS; chỉ đọc metadata, không model inference hoặc training.
- Review/ảnh hưởng: Codex triển khai trên checkout cách ly độc quyền và review diff/
  producer-consumer riêng; không gọi đây là review độc lập bởi thành viên. Profile MLX
  theo JSONL local đã duyệt mà pipeline dùng; không kéo extra dataset loader ngoài phạm vi.
  Constraints phiên bản tách 3.12/3.13; không đổi app/backend/model đang hoạt động.
- CI: PR run 37911184856 trên c879d02 PASS: Windows/Mac mỗi OS 110 feature +
  3 UI Node22; pip check/demo, PowerShell parse/contract và installer DemoOnly Windows
  PASS; history PASS. Link: https://github.com/ng-wngkh07/Study-Agent/actions/runs/37911184856.
- Phát hành: PR #1 được chủ repo merge trong lúc tác vụ đang chạy; chuyển bản mới sang
  codex/fix-project-guides, đồng bộ origin/main fdd9adf; kết quả CI/commit cập nhật
  trong báo cáo dùng chung và evidence. PR #2: https://github.com/ng-wngkh07/Study-Agent/pull/2. Không tự merge hoặc thay protection/reviewer.
- Giới hạn: full installer Windows mới, model QA/VLM/MLX thật, toàn suite/corpus
  readiness/training NOT_RUN; cài profile và test mock không nghiệm thu các phần này.
- Trạng thái tại cập nhật 2026-10-09T16:28:28.217575+07:00: hoàn tất sửa và xuất bản PR #2; hồ sơ local
  docs/project/documentation-fixes-2026-10-09/; báo cáo chung docs/team/BAO_CAO_SUA_LOI_2026-10-09.md.

<a id="yc-176"></a>
### YC-176 - 09/10/2026 16:16 (UTC+07)

- Người thực hiện: Codex; loại: làm rõ chính sách review và quyền merge.
- Mục tiêu: phân biệt một người phê duyệt, không cần người khác duyệt và chỉ chủ repo
  được merge; liên quan bảo vệ main YC-173/174 và hướng dẫn đóng góp YC-175.
- Giải thích theo bản kiểm YC-173/174: cần 1 approval từ người khác tác giả/người push cuối có
  quyền ghi. Điều phối viên duyệt PR thành viên được; tác giả không tự Approve PR. Nếu chủ repo
  quyết định cho tự merge PR của mình, cần bỏ Require approvals và Require approval
  of the most recent reviewable push, giữ PR/CI. Chỉ hướng dẫn, chưa chọn áp dụng.
- Quyền merge: người có quyền ghi có thể merge khi thỏa bảo vệ nhánh; bỏ review không
  tự giới hạn merge cho chủ dự án. Repo hiện chỉ tài khoản chủ có quyền ghi; collaborator
  được cấp quyền ghi sau này cũng có khả năng merge. Quy tắc điều phối viên merge trong tài liệu
  là phối hợp nhóm, chưa là giới hạn quyền được GitHub cưỡng chế.
- Phần đọc/bằng chứng: API protection/collaborators/PR hiện hành, CONTRIBUTING,
  README_QUY_TAC và GitHub Docs về required reviews. Ảnh hưởng thiết kế: nếu sau này
  muốn chỉ chủ repo merge cần cơ chế quyền/gate riêng; chưa có yêu cầu triển khai đó.
- Trước/sau/file sửa: ghi lời giải thích và giới hạn vào log; bổ sung phân biệt quyền
  với quy trình trong CONTRIBUTING. Không đổi GitHub policy/quyền hay mời tài khoản.
- Kiểm thử triển khai/RED–GREEN/handoff N/A vì giải thích; API readback được kiểm.
  Trạng thái: hoàn tất làm rõ; cập nhật 2026-10-09T16:16:00.615613+07:00. Không tự coi câu hỏi là lệnh tắt review.

- Readback bổ sung 2026-10-09T16:24:45.490701+07:00: PR #1 đã merge lúc 16:10:20 UTC+07 bởi chủ repo,
  main fdd9adf. Approval count=0, last-push approval=false; CI/strict/conversation/admin
  và cấm force-push/xóa giữ. Có hai collaborator ngoài chủ có quyền ghi, có thể merge
  khi checks đạt. Thay đổi GitHub do chủ repo thực hiện trong lúc tác vụ này chạy;
  Codex chỉ đọc lại/cập nhật hướng dẫn, không tự đổi policy hoặc merge. Mô tả ở trên
  về thiếu review/duy nhất tác giả là trạng thái cũ YC-173/174, đã được thay thế bởi readback này.

<a id="yc-177"></a>
### YC-177 - 09/10/2026 16:42 (UTC+07)

- Người thực hiện: Codex; loại: tiếp tục sửa lỗi sản phẩm từ rà soát.
- Mục tiêu/log liên quan: tiếp nối bản sửa YC-173/175 và các lỗi phần mềm F-01–F-05
  của audit ngày 08/10 (khác F01–F04 GitHub); PR2/2eae3af vẫn OPEN, CI đạt.
- Chẩn đoán/RED: 8/16 ca mới thất bại đúng hành vi: QA nhận ID nguồn sai lẫn đúng
  hoặc không citation; reindex mất metadata/chunks khi lỗi embedding/SQL; timestamp ICS
  sai, TEXT không escape/fold, giờ chuỗi một chữ số bị loại hoặc nhận khoảng đảo.
  Harness cũ QA bị gate cấu hình trước khi sinh; test mới dùng stub theo hợp đồng suite.
- Trước/sau: câu trả lời có ID sai hoặc không citation chuyển sang từ chối an toàn;
  vẫn bỏ marker khi hiển thị nguồn đúng. Chuẩn bị vector trước khi ghi; thay metadata/
  chunks/FTS chung transaction, rollback giữ cả vector cũ và retry được; batch thiếu
  vector bị chặn; lỗi đọc lại tài liệu giữ chỉ mục cũ và hash cũ để retry. ICS dùng DTSTAMP UTC đúng, escape TEXT và fold 75 UTF8 octet;
  giờ OCR so sánh theo phút rồi zero-pad, giữ giờ ngoài miền/đảo/cùng giờ unresolved.
- File sửa: app/rag_agent.py, app/indexer.py, app/timetable_ics.py, app/timetable_table.py;
  tests/test_audit_regressions.py (18 ca tổng hợp), pytest.windows.ini thêm ca vào CI;
  nhật ký/báo cáo chung. Không thêm dependency runtime/dev; parser độc lập cài vào tmp.
- Kiểm chứng local: 128 feature PASS/6 warning, 14 regression index/retention/backfill
  PASS, 3 UI PASS. Parser độc lập icalendar7.3.0 PASS UTC/timezone/TEXT roundtrip/
  Unicode/fold/no injected property. Codex review diff/caller riêng; không gọi là review
  độc lập của thành viên. Vector rỗng và lỗi extraction tái hiện riêng rồi GREEN sau sửa.
- Kiểm soát tích hợp: triển khai trong môi trường cô lập; đối chiếu hash phiên bản nền
  trước tích hợp. Dữ liệu, chỉ mục và model chính giữ nguyên; không gián đoạn tác vụ dữ liệu.
- Phát hành: tiếp tục nhánh codex/fix-project-guides và PR2 theo quyền push đã giao;
  giữ sửa YC-175, không tự merge/chỉnh protection/quyền. CI 37913747551 trên commit 37849e3 PASS: Windows/Mac mỗi OS 128 feature +3 UI Node22; pip/demo/Windows PowerShell hợp đồng/DemoOnly và history PASS. Link: https://github.com/ng-wngkh07/Study-Agent/actions/runs/37913747551.
- Giới hạn: Q-01 nội dung model thiếu điều kiện chưa nghiệm thu; citation ID đúng không
  chứng minh mệnh đề đúng nguồn. Full installer Windows mới/model thật/full suite/
  corpus readiness/training NOT_RUN; các gate giữ. Không sửa báo cáo audit 08/10 đã đóng.
- Trạng thái: hoàn tất sửa, xuất bản PR #2 và CI kiểm chứng; cập nhật 2026-10-09T16:52:32.261905+07:00; bằng chứng
  local docs/project/product-fixes-2026-10-09/.

<a id="yc-178"></a>
### YC-178 - 09/10/2026 17:13 (UTC+07)

- Người thực hiện: Codex; loại: rà soát bảo mật/thông tin riêng trước chia sẻ.
- Mục tiêu: kiểm nội dung GitHub, toàn lịch sử reachable, PR/CI và artifact; liên quan ranh giới Git YC-169/171/175 và phát hành YC-177.
- Baseline: main da566c4, PR2 đã được chủ repo merge lúc16:58:13; audit chỉ đọc, không sửa nguồn/quyền hoặc đẩy lại lịch sử.
- Kiểm chứng: 196 file main, 3 branch/2 PR refs, 12 commit/237 blob; Gitleaks8.30.1 quét main/patch lịch sử/PR/log CI/text PDF không phát hiện secret; 19 log CI đọc được. Hai PDF và ảnh demo được xem metadata/nội dung; không .env/DB/vector/model/corpus/hồ sơ cá nhân trong refs.
- Phát hiện còn mở: attribution tên thật trong11 file và email local-machine trong9 commit. Chưa đáp ứng yêu cầu ẩn toàn bộ danh tính; không nhầm metadata với API key. Không chép giá trị email/khóa vào nhật ký.
- Trước/sau: hoàn tất audit và phương án duyệt; checkout xuất bản riêng dùng GitHub+noreply cho commit sau. Không đổi config global/.git gốc, không rewrite/force-push; nội dung công khai chưa ẩn danh.
- Review/giới hạn: scanner + review scope không chứng minh tuyệt đối; SHA cũ không truy xuất được không bảo đảm purge cache. Rewrite có thể đổi SHA/mở force-push tạm/ảnh hưởng hai PR và bản clone; cần xác nhận trước bước này. Giấy phép/attribution cần xử lý có chủ đích.
- Thực thi hành vi/RED–GREEN/handoff/training N/A do audit; không chạm writer corpus. File sửa local: hồ sơ này, STATE, báo cáo/scan evidence docs/project/security-audit-2026-10-09/ (giữ local).
- Trạng thái: audit hoàn tất; privacy cleanup OPEN, chưa thực hiện rewrite/publish; cập nhật 2026-10-09T17:13:51.059577+07:00.


<a id="yc-179"></a>
### YC-179 - 09/10/2026 17:34 (UTC+07)

- Người thực hiện: Codex; loại: tổ chức nhóm và chuẩn hóa tài liệu nghiệp vụ.
- Mục tiêu: giữ tên/email tác giả phục vụ bản quyền; dùng mã vai trò trong phân công,
  giao việc và ví dụ; hoàn thiện tài liệu theo phạm vi, đầu ra và tiêu chí nghiệm thu.
- Trước/sau: tài liệu còn tên điều phối viên trong phần giao việc, mô tả trùng lặp
  và nội dung bàn giao nội bộ; sau thống nhất TV1-TV6, trách nhiệm/review/nghiệm thu,
  quy trình thay đổi, ranh giới tài sản, kế hoạch và điều kiện phát hành.
- File sửa: README chính/Windows/Mac/quy tắc, CONTRIBUTING, corpus/README, mẫu PR,
  phân công Markdown và PDF bản 1.1, báo cáo sửa lỗi, nhật ký chung.
- Quyết định: thay đề xuất ẩn mọi danh tính ở YC-178 bằng giữ nguyên LICENSE và
  metadata tác giả trong Git; bảng ánh xạ thành viên quản lý riêng. Không rewrite lịch sử.
- Hiệu chỉnh các mục cũ theo YC-179: thay tên trong trách nhiệm vận hành bằng vai trò,
  bỏ đường dẫn máy/metadata bàn giao khỏi YC-177; giữ ID, ngày và kết quả kiểm chứng cũ.
- Kiểm chứng: PDF 5 trang đã render và xem đủ; tiếng Việt/bảng/phân trang đạt.
  58 liên kết nội bộ và 13 ID lịch sử đạt; 196 file Git cùng văn bản PDF được quét
  bằng Gitleaks 8.30.1: 0 phát hiện bí mật; ranh giới tài sản đạt.
  LICENSE giữ nguyên byte; không đổi mã/app/test/dependency hoặc commit lịch sử.
- Ảnh hưởng: chỉ tài liệu; sáu vai trò, ba chức năng và cổng nguồn/model giữ nguyên.
  Test hành vi/RED-GREEN/huấn luyện N/A vì không sửa thực thi; CI kiểm trên PR xuất bản.
- Trạng thái: hoàn tất tài liệu và kiểm tra cục bộ; xuất bản qua branch/PR riêng,
  không tự merge hoặc đổi bảo vệ nhánh. Cập nhật 2026-10-09T17:34:05.950966+07:00.
- Giới hạn: nghiệm thu model thật/Windows full installer/corpus và hiệu năng còn mở
  theo YC-175/177; tài liệu không tự xác nhận các phần đó đã hoàn thành.

<a id="yc-174"></a>
### YC-174 - 09/10/2026 21:38 (UTC+07)

- Người thực hiện: mtrstapcode; loại: tài liệu phương án cải tiến và tài sản dự án.
- Lỗi/mục tiêu: bổ sung tài liệu đề xuất 8 phương án cải tiến chức năng QA (Improvement_QA_Study_Agent.docx) nhằm nâng cao độ tin cậy, khả năng kiểm chứng bằng chứng và trải nghiệm tự học cho sinh viên.
- Trước/sau: trước chưa có tài liệu tổng hợp đánh giá công sức, rủi ro và các chỉ số đo lường gợi ý cho các phương án QA; sau có báo cáo phân tích chi tiết 8 phương án (A đến H) phục vụ định hướng phát triển và nghiệm thu.
- Phần sửa: thêm mới file Improvement_QA_Study_Agent.docx vào thư mục gốc dự án, dùng git add -f để vượt qua chặn gitignore.
- Kiểm thử tại mốc 09/10/2026: đã kiểm tra tính toàn vẹn của file .docx, xác nhận Git tracking đúng nhánh docs-qa-improvements và không ảnh hưởng tới các file mã nguồn hiện có.
- Ảnh hưởng: thuần tài liệu tài sản, không can thiệp luồng runtime hay thay đổi mã nguồn hệ thống.
- Trạng thái: PASS (đã push nhánh docs-qa-improvements và cập nhật nhật ký cho PR #4).
- Liên quan: YC-173; PR #4 trên GitHub repo ng-wngkh07/Study-Agent.