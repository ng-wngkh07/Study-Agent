# Phân chia nhiệm vụ đồ án nhóm

Agent Học Tập - phương án nhóm 6 thành viên. Lập ngày 09/10/2026.

## 1. Phân chia nhiệm vụ đồ án nhóm

AGENT HỌC TẬP | NHÓM 6 THÀNH VIÊN

Giữ 4 nhiệm vụ gốc: tra cứu tài liệu, QA, thời khoá biểu từ ảnh và lập chỉ mục - huấn luyện. Bổ sung 2 trách nhiệm hỗ trợ: giao diện/môi trường dùng chung và kiểm thử/nghiệm thu/tài liệu. Không tạo thêm chức năng lớn chỉ để đủ số người.

| Chức năng của ứng dụng | Người dùng thực hiện gì? |
| --- | --- |
| Tra cứu tài liệu | Tìm theo từ khóa/chủ đề, chọn tài liệu, đọc trích đoạn và mở đúng nguồn/trang. |
| QA dựa trên tài liệu | Đặt câu hỏi, hỏi tiếp trong hội thoại và xem nguồn dẫn cho câu trả lời. |
| Thời khoá biểu từ ảnh | Tải ảnh, xem/chỉnh bản nháp, xác nhận lưu, kiểm xung đột và xuất lịch .ics. |

Lập chỉ mục và huấn luyện là công việc kỹ thuật phục vụ ba chức năng trên; không phải chức năng thứ tư mà người dùng bắt buộc thao tác.

| Thành viên | Nhiệm vụ | Môi trường |
| --- | --- | --- |
| TV1 | Chủ trì tra cứu tài liệu | Windows |
| TV2 | Chủ trì QA và hội thoại | Windows |
| TV3 | Chủ trì thời khoá biểu từ ảnh | Windows |
| TV4 | Chỉ mục chính, dữ liệu và huấn luyện | Mac |
| TV5 | Giao diện chung, tích hợp, môi trường chạy | Windows |
| TV6 | Kiểm thử, nghiệm thu và tài liệu chung | Windows |


## 2. Nhiệm vụ 1 và 2

CHỦ TRÌ HAI CHỨC NĂNG TRA CỨU VÀ QA

### TV1 - Tra cứu tài liệu

- Tìm lỗi, tái hiện, sửa và nâng cấp trong luồng tìm tài liệu. Chủ trì giao diện tra cứu và logic/API liên quan; đảm bảo kết quả có đúng tên tài liệu và trang nguồn.

- Kiểm tìm từ khóa tiếng Việt/thuật ngữ gốc, lọc sách, kết quả rỗng, nguồn bị thiếu, mở PDF/ảnh đúng trang và quay về từ khóa khi embedding hoặc GPU không khả dụng.

- Phạm vi chính: app/document_lookup.py, static/document-lookup.js, tests tra cứu. searcher/indexer và API chung chỉ sửa sau phối hợp TV2, TV4, TV5.

- Bàn giao: PR nhỏ theo lỗi/nâng cấp, ca tái hiện trước sửa, test phù hợp, kết quả sau sửa và mục nhật ký. Đạt khi tra cứu đúng nguồn và không làm QA hoặc lịch bị lỗi.

- Review: TV2 review ảnh hưởng truy xuất; TV4 review thay đổi index/schema; TV6 kiểm lại ca lỗi độc lập.

### TV2 - QA và hội thoại

- Tìm lỗi, sửa và nâng cấp hỏi đáp có nguồn; giữ ngữ cảnh nhiều lượt, lưu phiên và tóm tắt. Phân biệt câu trả lời có bằng chứng với nội dung không đủ nguồn.

- Kiểm trích dẫn khớp nội dung nguồn, câu hỏi nối tiếp, lựa chọn model, model mất kết nối, giới hạn ngữ cảnh và trạng thái bận. Không tạo câu trả lời hoặc trích dẫn giả để che lỗi.

- Phạm vi chính: app/rag_agent.py, app/dialogue.py, app/topic_summarizer.py và phần QA trong static/app.js. API/server/config dùng chung cần phối hợp.

- Bàn giao: PR, test chống tái phát lỗi, bộ ca QA có nguồn và ghi rõ model/data version. Đạt khi hội thoại hoạt động đúng và trích dẫn mở đúng nguồn; mock đạt chưa chứng minh chất lượng model thật.

- Review: TV1 kiểm nguồn/truy xuất; TV5 kiểm UI/API chung; TV6 nghiệm thu trên cùng bộ ca.

## 3. Nhiệm vụ 3 và 4

CHỨC NĂNG LỊCH TỪ ẢNH VÀ NGƯỜI HUẤN LUYỆN DUY NHẤT

### TV3 - Thời khoá biểu từ ảnh

- Tìm lỗi, sửa và nâng cấp tải ảnh, OCR/VLM, chuẩn hoá ngày/giờ/phòng, bản nháp và lưu lịch. Không đoán ô mờ hoặc thiếu dữ liệu.

- Giữ bước người dùng xem/chỉnh/xác nhận trước khi lưu. Kiểm ngày/giờ sai, tiết học chưa ánh xạ, xung đột trong bản nháp hoặc với lịch đã lưu, ảnh lỗi và xuất .ics.

- Phạm vi chính: app/timetable_*.py và static/timetable.js. Không đưa ảnh/lịch cá nhân vào corpus QA hoặc tập huấn luyện.

- Bàn giao: ảnh mẫu tổng hợp, kết quả mong đợi, PR, test và log. Đạt khi ô chưa rõ được báo đúng, dữ liệu xác nhận được lưu đúng và tra cứu/QA vẫn hoạt động.

- Review: TV2 review API liên quan; TV5 review giao diện; TV6 kiểm lại bằng ảnh/ca độc lập.

### TV4 - dữ liệu, chỉ mục chính và huấn luyện

- Là người phụ trách huấn luyện duy nhất. Thu nhận gói nguồn/review đã duyệt; hợp nhất nguồn, index/vector chính, chuẩn bị dataset, chạy trial và quản lý phiên bản model trên Mac.

- Trước học: audit live complete: true, review OCR toàn bộ, kiểm provenance nguồn - trang - chunk - vector, hash, dedup/tách tập, tokenizer và tài nguyên. Không suy corpus sẵn sàng từ số lượng file/vector hoặc test xanh.

- Chỉ một writer/job cho corpus/index/vector chính. Nếu đã giao job cho công cụ/agent, phải xác nhận kết thúc và bàn giao trước khi tự ghi; không chạy GPU training và suy luận cạnh tranh.

- Phát hành gói riêng có corpus/model revision, hash, run ID, chỉ số và hướng rollback. Không merge DB/vector/weights qua Git; không tự kích hoạt candidate chỉ vì loss giảm.

- TV6 chủ trì đánh giá độc lập candidate, có nguồn/holdout và ca giữ kiến thức cũ; phối hợp TV1-3 khi cần. Không đạt thì giữ candidate để phân tích, không thay model đang dùng.

## 4. Nhiệm vụ 5 và 6

HAI VAI TRÒ HỖ TRỢ CÓ ĐẦU RA CỤ THỂ

### TV5 - Giao diện chung và môi trường chạy

- Chủ trì điều hướng ba chế độ, bố cục/CSS chung, thông báo trạng thái và tích hợp giao diện. Các thành viên TV1-3 vẫn sở hữu UI chức năng của mình; TV5 không sửa lại luồng nghiệp vụ của họ nếu chưa thống nhất.

- Duy trì README_WINDOWS, launcher/config mẫu, demo và khả năng chạy trên Windows. Đường dẫn không hard-code theo máy; model theo cấu hình. Không thay provider, model huấn luyện hoặc cấu hình toàn cục của người khác.

- Phạm vi: static/index.html, style.css, launcher/dev/config chung. server.py, file_lock.py và hợp đồng API chỉ sửa trong PR được các chủ trì ảnh hưởng review.

- Bàn giao: kết quả chạy trên máy Windows, checklist tích hợp ba luồng, PR sửa lỗi môi trường/giao diện và hướng dẫn tái hiện. Ghi NOT_RUN nếu chưa kiểm thật, không dùng kết quả Mac để xác nhận Windows.

- Phối hợp TV6 kiểm CI và bản demo; Khải là đầu mối merge. TV5 có thể hỗ trợ giải quyết xung đột nhưng không tự ghi đè logic hoặc dữ liệu của người khác.

### TV6 - Kiểm thử, nghiệm thu và tài liệu

- Thiết kế bộ ca hồi quy cho cả ba chức năng, test ranh giới và dữ liệu tổng hợp; lập báo lỗi có bước tái hiện, expected/actual, môi trường và mức ảnh hưởng.

- Review PR, kiểm log và tái kiểm ca lỗi sau sửa. Duy trì tiêu chí nghiệm thu, hướng dẫn nhóm và nhật ký chung; mỗi tác giả vẫn phải viết mục log cho thay đổi của mình, không đẩy toàn bộ việc ghi log sang TV6.

- Đánh giá model theo nguồn/holdout độc lập và ca giữ kiến thức cũ trên phiên bản đã chốt. Nếu cần suy luận trên Mac, thống nhất thời gian với Khải; không tự chạy training hoặc writer corpus.

- Bàn giao: bộ ca kiểm thử có kết quả, báo cáo hồi quy/model, danh sách lỗi còn lại và checklist release. Không tự sửa rộng phần chức năng của TV1-3; xử lý test/tài liệu của mình hoặc phối hợp chủ trì khi lỗi chạm phần khác.

- TV6 nghiệm thu, Khải quyết định merge/phát hành sau review và cổng chất lượng. Tác giả PR không tự duyệt PR của mình.

## 5. Quy tắc GitHub và tạo branch

MỘT REPO MÃ CHUNG, MỘT NHÁNH MAIN ỔN ĐỊNH

### Trước khi sửa

- Clone toàn bộ repo. Đọc quy tắc, nhật ký chung và các mục liên quan chức năng/file/lỗi; kiểm phiên bản main hiện tại. Không khôi phục mã cũ chỉ vì bản local dễ chạy hơn.

- Mỗi việc có Issue hoặc mô tả đầu việc với chủ trì, phạm vi, tiêu chí và phần bị ảnh hưởng. Một branch cho một lỗi/nâng cấp rõ ràng; không gom nhiều chức năng không liên quan.

- Tạo branch từ main mới nhất. Dùng mẫu <loai>/<phamvi>/<ma-viec>-<ten>; chữ thường không dấu, không khoảng trắng. Loại: feature, fix, refactor, test, docs, chore; phạm vi: lookup, qa, timetable, training, shared.

- Ví dụ: fix/lookup/12-sai-trang-minh; feature/qa/18-cai-thien-trich-dan-lan; test/shared/21-hoi-quy-huy; docs/shared/25-cap-nhat-huong-dan-an. training là phạm vi công việc, không cấp quyền train cho người khác.

### Một vòng branch - PR - merge

- 1. Cập nhật main: git switch main; git pull --ff-only origin main. Tạo nhánh: git switch -c fix/lookup/12-sai-trang-minh. Các lệnh thực hiện lần lượt trong repo đã có remote.

- 2. Sửa đúng phạm vi, kiểm thử và thêm log cùng PR. Trước commit, xem danh sách staged để loại .env, dữ liệu/model và file cá nhân.

- 3. Push nhánh riêng: git push -u origin fix/lookup/12-sai-trang-minh. Mở PR vào main, mô tả lỗi trước/sau, file ảnh hưởng, log ID, kiểm thử và NOT_RUN.

- 4. Trước merge: git fetch origin, rồi git merge origin/main trên nhánh của mình. Xử lý xung đột cùng chủ trì file; đọc log mới và kiểm lại sau thay đổi, không chọn toàn bộ ours/theirs để bỏ công việc người khác.

- 5. Có ít nhất một reviewer khác tác giả; sửa phần chung cần reviewer từ từng chức năng bị ảnh hưởng. Khải merge sau các check áp dụng đạt; sau merge nhóm đồng bộ main.

- Không push trực tiếp main, không force-push nhánh chung, không tự reset/ghi đè thay đổi của thành viên khác. Nên bật bảo vệ main và yêu cầu review/check; đây là quy tắc cần cấu hình khi có repo, chưa phải trạng thái GitHub đã bật.

Tham khảo: [GitHub Docs - About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches), [Git - git-switch](https://git-scm.com/docs/git-switch).

## 6. Giới hạn thay đổi và tài sản Git

LÀM ĐÚNG PHẦN VIỆC, BẢO VỆ HỢP ĐỒNG CHUNG

### Không làm hỏng phần còn lại

- Mỗi người chịu trách nhiệm hoàn thành phần được giao. Đọc caller, API, dữ liệu và log liên quan trước sửa; giữ hành vi đã được nghiệm thu. Chỉ refactor/đổi hợp đồng khi có lý do và phương án tương thích rõ.

- Nếu cần sửa module ngoài phạm vi hoặc dùng chung: báo Issue/PR trước khi sửa, kèm lỗi tái hiện, file/chức năng ảnh hưởng, giải pháp nhỏ nhất, rủi ro, test cần chạy và rollback/migration nếu đổi schema.

- Chủ trì liên quan và Khải thống nhất người ghi, thứ tự tích hợp và hướng xử lý. Có thể tách PR phần chung rồi PR chức năng. Không sửa ngầm, đổi API/format dữ liệu hoặc đè cả file để phần mình chạy được.

- Chỉnh riêng máy qua .env/cấu hình local, không commit đường dẫn/token/settings cá nhân. Nếu thay đổi local là điều kiện để tái hiện hoặc chạy được, phải báo rõ và cập nhật cấu hình mẫu/hướng dẫn khi đã thống nhất.

- Kiểm lại phần bị ảnh hưởng; sửa phần chung phải smoke tra cứu, QA và thời khoá biểu. Nếu chưa thể đảm bảo tương thích, ghi đang làm/NOT_RUN và chưa merge; không che lỗi bằng việc tắt test.

| Đưa lên repo mã | Giữ ở kho/local riêng |
| --- | --- |
| app/, static/, scripts dùng chung, tests và mẫu tổng hợp | src/ nguồn thật; data/ DB, vector, model, adapter, dataset, lịch/hội thoại |
| Dependency, launcher, config mẫu, CI, README, docs/team | Môi trường ảo, cache, log runtime, .env, khóa/token |
| LICH_SU_DU_AN.md; metadata corpus; PDF phân công này | docs/project/ hồ sơ cá nhân, handoff và tích hợp công cụ riêng |

Tuân thủ .gitignore; không dùng git add -f để vượt ranh giới. Nguồn/index/model thật chia sẻ bằng gói có phiên bản, hash và vị trí tải kiểm soát. Không merge SQLite/vector/weights giữa các branch.

Giữ các nguyên tắc ban đầu: xử lý nội dung cục bộ; không sửa PDF nguồn để khớp OCR; không đoán phần nguồn không đọc được; lịch cá nhân không tự vào tập học; không nới cổng toàn corpus hay bỏ đánh giá độc lập để tuyên bố hoàn tất. Giữ giới hạn nội dung y tế: hỗ trợ học tập/tra cứu, không chẩn đoán hoặc kê đơn.

## 7. Nhật ký thay đổi ứng dụng

MỘT FILE CHUNG: LICH_SU_DU_AN.md Ở GỐC REPO

### Trước sửa và khi bàn giao

- Đọc lịch sử theo chức năng, file, lỗi hoặc quyết định liên quan. Chốt phiên bản/hành vi đang áp dụng; nếu thay quyết định cũ, dẫn log ID và lý do. Thêm ca hồi quy để không lặp lỗi hoặc ghi đè tính năng đã sửa.

- Nhật ký ghi ý chính của lỗi và thay đổi sản phẩm, không copy prompt, hội thoại hoặc log tool. Mỗi tác giả thêm mục mới trong cùng PR; không tạo nhật ký riêng cho từng người hoặc từng tính năng.

- Ghi ngày/tháng/năm và giờ, múi giờ Asia/Ho_Chi_Minh; người thực hiện; ID riêng; loại thay đổi; trước/sau; file/phần sửa; ảnh hưởng; kiểm thử; trạng thái và giới hạn. ID mẫu: LOG-20261009-qa-12-sua-trich-dan-minh.

- Không xoá/đánh lại số các mục cũ. Hiệu chỉnh nội dung ghi sai bằng lý do và thời gian sửa; bảo toàn ID/ngày cũ. Nếu hai branch cùng thêm log, giữ cả hai mục hợp lệ và giải quyết ID trùng, không chọn bỏ một bên.

- PASS chỉ cho kiểm chứng đã chạy. FAIL, đang làm, NOT_RUN hoặc N/A có lý do phải ghi rõ; không dùng green unit test để khẳng định chất lượng QA/OCR hoặc model.

### Ví dụ cấu trúc mục log - minh hoạ, chưa triển khai

- Ngày: DD/MM/YYYY HH:mm (UTC+07). ID/người: LOG-<ngay>-<chucnang>-<viec>-<ten>. Loại: sửa lỗi / tính năng / cấu hình / dữ liệu-model / tài liệu.

- Lỗi/mục tiêu: đường dẫn mở nguồn trỏ sai trang. Trước/sau: trước mở trang khác; sau mở đúng trang theo kết quả tra cứu. Phần sửa: file/API/UI cụ thể; không ghi lại câu người dùng đã hỏi.

- Liên quan/ảnh hưởng: log cũ cần giữ, QA dùng chung link nguồn. Kiểm thử: ca tái hiện, ca hồi quy và môi trường/model/data version. Trạng thái/giới hạn: kết quả thật và phần chưa chạy.

PR chỉ hoàn tất khi đúng phạm vi, review đạt, test liên quan đạt, nhật ký đầy đủ, phần chưa chạy được báo rõ và không phát sinh hồi quy chưa xử lý. Sau merge, TV6 kiểm tích hợp; Khải phát hành model khi các cổng độc lập đạt.

Hồ sơ hội thoại cũ giữ local để truy nguyên, không phải nhật ký chung của ứng dụng. YC-167 được biên tập thành kết quả thay đổi sản phẩm; YC-168 ghi cập nhật nhóm 6 người và quy tắc mới. Không chép prompt vào các mục mới.

## 8. Cải tiến nhỏ và lộ trình thực hiện

ĐỀ XUẤT, CHƯA GIAO TRIỂN KHAI TÍNH NĂNG MỚI

### Hai cải tiến có thể cân nhắc sau ổn định

- Đánh dấu trang tài liệu cục bộ: lưu tham chiếu tài liệu/trang để mở lại nhanh; dùng định danh/hash nguồn và báo khi nguồn đổi/mất. Không sao chép nội dung sách, không thêm tài khoản hoặc đồng bộ cloud. TV1 chủ trì, TV5 hỗ trợ UI, TV6 kiểm nguồn thay đổi.

- Sao chép trích dẫn có nguồn: nút copy trích đoạn kèm tên tài liệu và số trang để ghi chú học tập; giữ nguyên nội dung nguồn, không gọi LLM. TV1 và TV2 thống nhất định dạng dùng chung; TV6 kiểm copy không làm mất thông tin nguồn.

- Chỉ triển khai sau khi nhóm chốt Issue và tiêu chí, xác nhận chưa trùng chức năng đang có ở nhánh mới nhất. Không mở thêm hệ thống flashcard, quản lý học tập, tài khoản/cloud hoặc microservice chỉ để chia người.

- Xuất .ics, kiểm xung đột lịch, lịch sử hội thoại và tóm tắt đã có trong mã hiện tại; không ghi là tính năng mới. Tập trung sửa lỗi và kiểm chứng các chức năng này trước mở rộng.

### Lộ trình gọn cho 6 người

- Giai đoạn 1: TV1-3 lập backlog lỗi theo ba chức năng; TV5 thử chạy Windows và rà điểm dùng chung; TV6 lập ma trận test; Khải xác minh nguồn/corpus/job và bản model. Chốt trọng số đầu việc, không chia đều theo số feature.

- Giai đoạn 2: làm PR nhỏ có log, reviewer và test; phần chung thống nhất trước. TV6 tái kiểm lỗi và chống hồi quy; TV5 tích hợp UI/môi trường.

- Giai đoạn 3: đồng bộ main, smoke cả ba chức năng, nghiệm thu trực tiếp Windows/Mac. Khải hợp nhất dữ liệu theo gói đã duyệt; training chỉ khi đủ cổng nguồn và tài nguyên.

- Giai đoạn 4: đánh giá candidate độc lập, giữ kiến thức cũ và rollback; Khải quyết định phát hành. Chỉ sau đó cân nhắc hai cải tiến nhỏ bằng Issue riêng.

Tài liệu này phân công và đặt quy tắc, không xác nhận đã sửa mọi lỗi, đã chạy Windows/CI hay đã huấn luyện model. Môi trường Windows và suy luận thật cần kết quả kiểm trực tiếp; mỗi PR ghi kết quả của chính phiên bản đó.

Tài liệu dùng chung trong repo: README_QUY_TAC.md, CONTRIBUTING.md, README_WINDOWS.md, LICH_SU_DU_AN.md và docs/team/PHAN_CONG_6_NGUOI.md. PDF lập ngày 09/10/2026; cập nhật PDF và bản Markdown trong cùng PR nếu phân công thay đổi.
