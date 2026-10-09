# Phân công trách nhiệm và kế hoạch thực hiện

**Dự án:** Agent Học Tập. **Phiên bản:** 1.1 - 09/10/2026.
**Quản lý tài liệu:** TV6. **Điều phối:** TV4.

Tài liệu quy định phạm vi, đầu ra, tiêu chí nghiệm thu và trách nhiệm phối hợp của nhóm sáu thành viên. Mã TV1-TV6 đại diện cho vai trò; bảng ánh xạ với thành viên được quản lý riêng. Tên/email tác giả phục vụ bản quyền và attribution Git được giữ nguyên; tài liệu giao việc dùng mã vai trò.

## 1. Phạm vi nghiệp vụ

| Chức năng | Luồng sử dụng | Kết quả cần đạt |
| --- | --- | --- |
| Tra cứu tài liệu | Nhập từ khóa/chủ đề, chọn tài liệu, đọc trích đoạn, mở nguồn | Kết quả gắn đúng tài liệu, trang hoặc phần văn bản; xử lý nguồn thiếu/kết quả rỗng |
| Hỏi đáp có nguồn | Đặt câu hỏi, hỏi tiếp trong phiên, kiểm tra trích dẫn | Câu trả lời có căn cứ; từ chối khi thiếu nguồn; phiên và liên kết nguồn hoạt động đúng |
| Thời khóa biểu từ ảnh | Tải ảnh, xem/chỉnh bản nháp, xác nhận lưu, xuất lịch | Ô chưa rõ được đánh dấu; chỉ lưu sau xác nhận; phát hiện xung đột và xuất ICS hợp lệ |

Chỉ mục, dữ liệu và huấn luyện phục vụ ba chức năng trên. Giao diện, môi trường, kiểm thử và tài liệu là các công việc hỗ trợ tích hợp.

## 2. Cơ cấu trách nhiệm

| Mã vai trò | Trách nhiệm chính | Môi trường | Phối hợp |
| --- | --- | --- | --- |
| TV1 | Tra cứu tài liệu | Windows | TV2, TV4, TV5, TV6 |
| TV2 | QA và hội thoại | Windows | TV1, TV5, TV6 |
| TV3 | Thời khóa biểu từ ảnh | Windows | TV2, TV5, TV6 |
| TV4 | Dữ liệu, chỉ mục chính, huấn luyện, điều phối phát hành | Mac | TV1-TV3, TV6 |
| TV5 | Giao diện chung, tích hợp, môi trường chạy | Windows | TV1-TV3, TV6 |
| TV6 | Kiểm thử, nghiệm thu độc lập, quản lý tài liệu | Windows | TV1-TV5 |

Chủ trì hoàn thành đầu ra và khắc phục lỗi trong phạm vi được giao. Reviewer kiểm tính đúng, tác động và bằng chứng. TV6 xác nhận nghiệm thu; TV4 điều phối tích hợp và quyết định phát hành. Quyền thao tác GitHub phụ thuộc phân quyền/bảo vệ nhánh, không được suy từ bảng phân công.

## 3. Gói công việc và nghiệm thu

### TV1 - Tra cứu tài liệu

- **Phạm vi:** `app/document_lookup.py`, `static/document-lookup.js`, API và test tra cứu; phần searcher/indexer/API chung phối hợp TV2, TV4, TV5.
- **Đầu ra:** PR theo lỗi/chức năng, ca tái hiện/hồi quy, kết quả có tham chiếu nguồn, mục nhật ký.
- **Nghiệm thu:** tìm từ khóa tiếng Việt/thuật ngữ gốc; bộ lọc đúng; PDF mở đúng trang, văn bản mở đúng phần; xử lý nguồn mất/kết quả rỗng; FTS dùng được khi embedding không khả dụng.
- **Review:** TV2 kiểm truy xuất; TV4 kiểm index/schema; TV6 tái kiểm độc lập.

### TV2 - QA và hội thoại

- **Phạm vi:** `app/rag_agent.py`, `app/dialogue.py`, `app/topic_summarizer.py`, phần QA của `static/app.js` và test liên quan.
- **Đầu ra:** PR, bộ ca QA có nguồn, test phiên/hội thoại, kết quả gắn model/data revision, mục nhật ký.
- **Nghiệm thu:** trích dẫn đúng nguồn và nội dung; từ chối khi thiếu căn cứ; câu nối tiếp giữ ngữ cảnh; lưu/tóm tắt phiên đúng; lỗi model, giới hạn ngữ cảnh và trạng thái bận được thông báo rõ. Test giả lập không thay nghiệm thu model thật.
- **Review:** TV1 kiểm nguồn; TV5 kiểm UI/API; TV6 đánh giá trên bộ ca đã chốt.

### TV3 - Thời khóa biểu từ ảnh

- **Phạm vi:** `app/timetable_*.py`, `static/timetable.js`, OCR/VLM, chuẩn hóa và test lịch.
- **Đầu ra:** ảnh thử tổng hợp, expected, PR, test bản nháp/lưu/xung đột/ICS, mục nhật ký.
- **Nghiệm thu:** không đoán ô mờ; đánh dấu giờ/ngày/phòng chưa rõ; xác nhận trước lưu; phát hiện xung đột; dữ liệu lưu đúng; ICS được đọc độc lập, giữ múi giờ/ký tự tiếng Việt. Ảnh/lịch cá nhân không vào corpus QA hoặc tập học.
- **Review:** TV2 kiểm API; TV5 kiểm UI; TV6 kiểm bằng ảnh/ca độc lập.

### TV4 - Dữ liệu, chỉ mục chính và huấn luyện

- **Phạm vi:** nhận nguồn/review đã duyệt, hợp nhất corpus/index/vector chính, chuẩn bị dataset, chạy trial, quản lý model trên Mac; là đầu mối ghi và huấn luyện duy nhất của bộ dữ liệu chính.
- **Đầu ra:** gói nguồn/model riêng có revision, hash, provenance, run ID, chỉ số và rollback; bản ghi thay đổi dữ liệu/model đã biên tập để chia sẻ.
- **Nghiệm thu trước học:** audit hiện hành `complete: true`; OCR được review đầy đủ; nguồn-trang-chunk-vector có provenance/hash; dedup, tách tập, tokenizer và tài nguyên đạt. Một writer/job mỗi thời điểm; kết thúc và bàn giao trước khi đổi bên ghi, không chạy GPU cạnh tranh.
- **Nghiệm thu phát hành:** TV6 đánh giá độc lập theo nguồn/holdout và ca giữ kiến thức cũ, phối hợp TV1-TV3. Candidate không đạt giữ để phân tích; không kích hoạt chỉ từ số vector, test xanh hoặc loss giảm. Không merge DB/vector/weights qua Git.

### TV5 - Giao diện chung và môi trường chạy

- **Phạm vi:** điều hướng ba chế độ, `static/index.html`, CSS chung, launcher/config mẫu, demo, hướng dẫn Windows/Mac. TV1-TV3 vẫn chủ trì UI nghiệp vụ.
- **Đầu ra:** PR tích hợp, kết quả chạy trên môi trường mục tiêu, checklist ba luồng và hướng dẫn tái hiện lỗi môi trường.
- **Nghiệm thu:** khởi động theo hướng dẫn; cấu hình không gắn máy cá nhân; ba chế độ hoạt động; trạng thái/lỗi rõ; phần chung không mất dữ liệu hoặc phá API. `server.py`, `config.py`, khóa file/API chung thống nhất trước sửa.
- **Review:** chủ trì bị ảnh hưởng và TV6. Không đổi provider/model hoặc cấu hình toàn cục của người khác.

### TV6 - Kiểm thử, nghiệm thu và tài liệu

- **Phạm vi:** hồi quy ba chức năng, test ranh giới, nghiệm thu candidate, quản lý tài liệu nghiệp vụ.
- **Đầu ra:** ma trận test, báo lỗi có bước tái hiện/expected/actual, báo cáo hồi quy/model, vấn đề còn lại, checklist phát hành.
- **Nghiệm thu:** kết quả truy nguyên đến commit, OS, Python, model/data; lỗi được kiểm lại; phân biệt PASS/FAIL/NOT_RUN/N/A; tài liệu khớp thực thi. Mỗi tác giả PR vẫn tự ghi log thay đổi.
- **Phối hợp:** chủ trì sửa lỗi sản phẩm, TV6 kiểm lại độc lập; suy luận Mac thống nhất lịch với TV4, không tự chạy training hoặc ghi corpus chính.

## 4. Quy trình thực hiện và bàn giao

| Bước | Chủ trì | Đầu ra/điều kiện chuyển bước |
| --- | --- | --- |
| Tiếp nhận | Chủ trì chức năng | Issue có mục tiêu/lỗi, phạm vi, mức ảnh hưởng, tiêu chí, log liên quan |
| Chốt phương án | Chủ trì + vai trò bị ảnh hưởng | Phiên bản main, giải pháp, người ghi phần chung, tương thích/rollback |
| Thực hiện | Chủ trì | Branch riêng, ca tái hiện, bản sửa, test phù hợp |
| Review | Vai trò liên quan | Kiểm diff, tiêu chí, tác động, tài sản và nhật ký |
| Nghiệm thu | TV6 + chủ trì | Kết quả đúng phiên bản/môi trường; ghi vấn đề còn lại |
| Tích hợp/phát hành | TV4; TV5/TV6 hỗ trợ | Nhánh cập nhật, CI đạt, hội thoại xử lý, smoke sau merge, rollback |

Một branch/PR xử lý một đầu việc rõ ràng. Tên nhánh dùng `<loai>/<phamvi>/<ma-viec>-<ma-vai-tro>`, ví dụ `fix/lookup/12-sai-trang-tv1`. ID nhật ký thành viên: `LOG-YYYYMMDD-chucnang-maviec-tvN`; giữ ID/ngày cũ. Bảng ánh xạ, tên thật/email/liên hệ của thành viên không ghi trong phân công, Issue, PR hoặc ví dụ giao việc.

Mỗi bàn giao có: mã việc/Issue; chủ trì/reviewer theo vai trò; mục tiêu/đầu vào/đầu ra; phạm vi/file/phiên bản nền; tiêu chí và kết quả trước/sau; test đã/chưa chạy; phụ thuộc/người ghi/rủi ro/rollback; PR/commit/log ID; trạng thái và việc còn lại.

Cài đặt/test/branch/PR theo [CONTRIBUTING](../../CONTRIBUTING.md). Không push trực tiếp main, force-push nhánh chung hoặc ghi đè việc người khác. Nhóm review chéo dù GitHub hiện không bắt buộc approval; kiểm chính sách hiện hành trước merge.

## 5. Kiểm soát chất lượng và thay đổi chung

Thay đổi ngoài phạm vi, API/schema/config/module chung cần Issue/PR và thống nhất với chủ trì bị ảnh hưởng trước ghi. Chốt một người ghi hoặc tách PR độc lập; giữ cả mục lịch sử khi xử lý xung đột. Sửa phần chung phải smoke tra cứu, QA và lịch.

| Nội dung | Bằng chứng nghiệm thu |
| --- | --- |
| Mã/UI | Ca tái hiện/hồi quy, test phù hợp, smoke luồng bị ảnh hưởng |
| Windows/Mac | Kiểm trực tiếp trên OS mục tiêu; OS khác không thay thế |
| QA/OCR thật | Đối chiếu nguồn/ảnh và expected đã duyệt; mock chỉ kiểm hợp đồng |
| Dữ liệu/model | Revision/hash/provenance, cổng trước học, holdout/retention, rollback |
| Tài liệu | Vai trò/đầu ra/tiêu chí rõ; khớp mã, link đúng; không chứa dữ liệu riêng |

PR chỉ hoàn tất khi tiêu chí/review/kiểm liên quan đạt, nhật ký đầy đủ và phần chưa kiểm được nêu rõ. Chưa đủ thì giữ đang làm/chờ kiểm; không tắt test hoặc nới cổng để chuyển PASS.

## 6. Tài sản và hồ sơ

| Đưa lên Git | Quản lý riêng |
| --- | --- |
| Mã/UI/script dùng chung, test/mẫu tổng hợp | Nguồn thật; ảnh/lịch/hội thoại cá nhân |
| Dependency, launcher/config mẫu, CI, README/docs nhóm | DB/vector/dataset/model/adapter, venv/cache/log, .env và khóa/token |
| Nhật ký thay đổi, metadata corpus, PDF này | Hồ sơ nội bộ, bàn giao công cụ, bảng ánh xạ vai trò-thành viên |

Tuân thủ `.gitignore`, kiểm staged, không `git add -f`. Gói dữ liệu/model có version/hash/quyền/provenance. Xử lý nội dung cục bộ; không sửa PDF nguồn hoặc dựng phần không đọc được; lịch/hội thoại không tự vào tập học. Ứng dụng hỗ trợ học tập, không chẩn đoán/kê đơn.

`LICH_SU_DU_AN.md` là nhật ký thay đổi chung: ngày/giờ Asia/Ho_Chi_Minh, ID, vai trò/tác giả thay đổi, loại, trước/sau, file, tác động, kiểm chứng và giới hạn. Không chép prompt, hội thoại, đường dẫn máy hoặc metadata bàn giao cá nhân. Hiệu chỉnh giữ ID/ngày và lý do; hồ sơ nội bộ quản lý riêng.

## 7. Kế hoạch và điều kiện phát hành

| Giai đoạn | Công việc | Điều kiện hoàn tất |
| --- | --- | --- |
| Chuẩn bị | TV1-TV3 lập backlog; TV5 kiểm môi trường; TV6 lập test; TV4 chốt dữ liệu/model/quyền ghi | Việc có chủ trì, tiêu chí, phụ thuộc, mức ảnh hưởng |
| Sửa/review | PR theo việc; thống nhất phần chung; TV6 tái kiểm; TV5 tích hợp | Review/test đạt, nhật ký đủ |
| Tích hợp | Đồng bộ main, smoke ba luồng, kiểm Windows/Mac; TV4 hợp nhất gói dữ liệu duyệt | Có kết quả môi trường mục tiêu; phân loại vấn đề còn lại |
| Phát hành | Đánh giá candidate độc lập, retention/rollback; TV4 quyết định | Cổng chất lượng đạt; lưu phiên bản/rollback |

Training chỉ khi đủ cổng nguồn/tài nguyên. Phân công không xác nhận corpus sẵn sàng, model đạt hoặc mọi công việc hoàn tất.

Đánh dấu trang cục bộ và sao chép trích dẫn có nguồn là hai đề xuất sau ổn định, chưa giao triển khai. TV1 chủ trì; TV2/TV5 phối hợp theo phạm vi; TV6 kiểm nguồn/định dạng. Chốt Issue/tiêu chí trước làm. Xuất ICS, kiểm xung đột, lịch sử và tóm tắt đã có trong ứng dụng.

## 8. Tài liệu liên quan và phiên bản

- [Quy tắc dự án](../../README_QUY_TAC.md): phối hợp, ranh giới, cổng chất lượng.
- [Đóng góp](../../CONTRIBUTING.md): môi trường, test, Issue, branch, PR, review.
- [README](../../README.md), [Windows](../../README_WINDOWS.md), [Mac](../../README_MAC.md): cài đặt và sử dụng.
- [Nhật ký](../../LICH_SU_DU_AN.md), [báo cáo](BAO_CAO_SUA_LOI_2026-10-09.md): kết quả đã/chưa nghiệm thu.
- [PDF phân công](../../output/pdf/PHAN_CHIA_NHIEM_VU_DO_AN_NHOM.pdf): cập nhật cùng Markdown trong một PR.

TV6 tăng phiên bản khi trách nhiệm/quy trình/tiêu chí đổi; TV4 và chủ trì bị ảnh hưởng review. Bản 1.1 chuẩn hóa giao việc theo YC-179, giữ sáu vai trò, ba chức năng và các cổng nguồn/model đã chốt.
