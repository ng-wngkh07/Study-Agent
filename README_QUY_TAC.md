# Quy tắc dự án Agent Học Tập - nhóm 6 người

## Phân công theo chức năng và trách nhiệm

Ứng dụng có **3 chức năng**: tra cứu tài liệu, QA dựa trên nguồn và thời khoá biểu từ ảnh.
Giữ **4 nhiệm vụ gốc**, thêm 2 trách nhiệm hỗ trợ; không mở tính năng lớn để đủ số người.

| Thành viên | Máy | Trách nhiệm |
| --- | --- | --- |
| TV1 | Windows | Tra cứu: tìm lỗi, sửa/nâng cấp UI/API, tìm kiếm và mở đúng nguồn. |
| TV2 | Windows | QA/hội thoại: tìm lỗi, sửa/nâng cấp truy xuất, trích dẫn và ngữ cảnh. |
| TV3 | Windows | Lịch từ ảnh: tìm lỗi, sửa/nâng cấp OCR/VLM, nháp/chỉnh/xác nhận và .ics. |
| TV4 | Mac | Người huấn luyện duy nhất; hợp nhất nguồn/index/vector chính, dataset, trial, release. |
| TV5 | Windows | Giao diện chung, tích hợp, cấu hình/demo và môi trường chạy Windows. |
| TV6 | Windows | Test hồi quy, nghiệm thu độc lập, đánh giá candidate và tài liệu chung. |

Chi tiết/đầu ra/reviewer: [phân công 6 người](docs/team/PHAN_CONG_6_NGUOI.md),
[PDF phân công](output/pdf/PHAN_CHIA_NHIEM_VU_DO_AN_NHOM.pdf).

## Đọc lịch sử trước mọi thay đổi

Trước sửa mã, test, cấu hình hoặc tài liệu, đọc `LICH_SU_DU_AN.md` theo chức năng,
file, lỗi và quyết định liên quan; đối chiếu main hiện tại. Giữ hành vi đã nghiệm thu,
thêm test chống tái phát lỗi. Không khôi phục phiên bản cũ hoặc ghi đè tính năng đã sửa.
Nếu thay quyết định, dẫn log cũ và giải thích lý do; quyết định mới không xoá lịch sử.

## Phạm vi và phần dùng chung

Mỗi người hoàn thành phần được giao, không tự sửa rộng phần người khác.
Nếu sửa ngoài phạm vi, module chung, API, schema, cấu hình/model hoặc đường dẫn:

1. Báo Issue/PR trước khi sửa: lỗi tái hiện, expected/actual, file/chức năng ảnh hưởng.
2. Đề xuất giải pháp nhỏ nhất, rủi ro, tương thích/migration, test và rollback.
3. Thống nhất chủ trì/người ghi/thứ tự tích hợp với người bị ảnh hưởng và Khải.
4. Sửa và kiểm lại; thay đổi phần chung phải smoke tra cứu, QA và thời khoá biểu.
5. Chưa bảo đảm tương thích thì giữ đang làm/NOT_RUN, chưa merge; không tắt test để che lỗi.

Điểm chung: server.py, config.py, searcher/indexer, file_lock.py, index.html/CSS và
phần chuyển chế độ. Không chọn bỏ cả file của người khác khi giải quyết xung đột.
Chỉnh riêng máy qua `.env`; không push đường dẫn/token/settings cá nhân. Nếu chỉnh
local là điều kiện chạy/tái hiện lỗi, báo rõ và cập nhật cấu hình mẫu khi đã thống nhất.

## GitHub, branch và PR

Một repo toàn bộ mã. Không push trực tiếp main, force-push nhánh chung hoặc reset mã
người khác. Không tự động merge các nhánh
train cho các thành viên khác. Bảo vệ main đã bật ở YC-173, kiểm lại tại YC-174:
CI features Windows/Mac và history phải đạt, nhánh cập nhật, hội thoại đã xử lý;
cần 1 approval có quyền ghi, khác tác giả và người push cuối. Quy tắc áp dụng cả admin,
review cũ bị huỷ khi có sửa mới; main không cho force-push/xoá. Đây là trạng thái tại mốc
kiểm, không thay cho kiểm trực tiếp Settings/PR trước merge. Tham khảo
[GitHub Docs về bảo vệ nhánh](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches).

Tên nhánh: `<loai>/<phamvi>/<ma-viec>-<ten>`; chữ thường không dấu, không khoảng trắng.
Loại: feature/fix/refactor/test/docs/chore; phạm vi: lookup/qa/timetable/training/shared.
Ví dụ `fix/lookup/12-sai-trang-minh`, `test/shared/21-hoi-quy-huy`.
Một branch/PR cho một việc rõ ràng; cập nhật main trước tạo và trước merge.

Vòng PR: đọc log → tái hiện/chốt tiêu chí → branch → sửa/test → thêm log → PR →
review chéo → xử lý xung đột/kiểm lại → merge → đồng bộ main và kiểm tích hợp.
Ít nhất một reviewer khác tác giả/người push cuối có quyền ghi; phần chung có review
của các chủ trì bị ảnh hưởng. Repo chỉ có tác giả sẽ chưa merge được: chủ repo vào
Settings → Collaborators → Add people, mời thành viên nhận lời rồi review Approve PR.
Tác giả không tự Approve; PR của Khải cũng cần người khác duyệt. Hướng dẫn chi tiết ở
[CONTRIBUTING](CONTRIBUTING.md). Không tự tắt quy tắc review chỉ để vượt blocker.
PR ghi trước/sau, phạm vi/ảnh hưởng, dữ liệu/model version, checks và phần chưa chạy.

## Một nhật ký chung của ứng dụng

**`LICH_SU_DU_AN.md` ở gốc là bản chung duy nhất, push cùng mã.** Mỗi thay đổi phải
có mục trong cùng PR, kể cả test/dependency/cấu hình/quy trình. Tác giả viết log;

Ghi ý chính lỗi/mục tiêu và thay đổi sản phẩm; **không copy prompt/hội thoại**.
Mỗi mục có ID, ngày/tháng/năm giờ (Asia/Ho_Chi_Minh), người, loại, trước/sau,
phần/file sửa, log/phiên bản liên quan, ảnh hưởng, kiểm thử, trạng thái và giới hạn.
ID mẫu `LOG-20261009-qa-12-sua-trich-dan-minh`; giữ ID/ngày cũ, không đánh lại số.
Hai PR cùng thêm log phải giữ cả hai; xử lý ID trùng trước merge.

Hiệu chỉnh thông tin cũ bằng lý do và ngày giờ sửa. Không xóa lịch sử hoặc đổi PASS
khi chưa có bằng chứng. Ghi PASS/FAIL/đang làm/NOT_RUN/N/A đúng kết quả thực tế.
CI kiểm PR có mục mới/ID cũ; reviewer kiểm nội dung, ảnh hưởng và việc tham khảo log.
Hồ sơ hội thoại cũ `docs/project/` giữ local để truy nguyên, không phải nhật ký chung.

## Tài sản Git và dữ liệu

Push app/static/scripts dùng chung/tests-mẫu tổng hợp/dependency/config mẫu/CI,
README/docs/team, nhật ký gốc, metadata corpus và PDF phân công đã cho phép.
Không push src nguồn thật hoặc data chứa SQLite/vector/weights/adapter/dataset/lịch/
hội thoại; không push docs/project, môi trường ảo/cache/log/.env/bí mật/tích hợp cá nhân.
Tuân thủ [.gitignore](.gitignore), không `git add -f`. Review staged trước commit.
Nguồn/index/model thật trao bằng gói version/hash/vị trí tải kiểm soát, không merge DB/weights.

## Nguyên tắc nguồn, model và nghiệm thu

- Nội dung xử lý cục bộ. Không sửa PDF nguồn để khớp OCR, không đoán trang/ô mờ.
  Lịch từ ảnh phải xem/chỉnh/xác nhận trước lưu; hội thoại/lịch cá nhân không tự vào tập học.
- Ứng dụng hỗ trợ học tập/tra cứu; giữ giới hạn nội dung y tế, không chẩn đoán/kê đơn.
- Khải giữ một writer corpus/index/vector/training chính. Nếu job đang được giao,
  xác minh terminal và bàn giao trước ghi; không chạy GPU cạnh tranh.
- Trước học: audit live `complete: true`, OCR review đầy đủ, source-page-chunk-vector
  có provenance/hash, dedup/split/tokenizer/tài nguyên đạt. Demo/test xanh/số vector không cấp quyền học.
- Candidate cần TV6 phối hợp TV1-3 đánh giá độc lập theo nguồn/holdout và giữ kiến thức
  cũ; không kích hoạt chỉ vì loss giảm. Giữ corpus/model revision, run ID, hash và rollback.
- Không tự đổi provider/model/cấu hình toàn cục của người khác. Ollama Windows là
  model phát triển, không đồng nhất chất lượng với MLX/adapter Mac.
- Test phù hợp thay đổi, kiểm phần bị ảnh hưởng và ghi NOT_RUN. Không dùng test mock
  để khẳng định chất lượng suy luận thật; Windows cần kiểm trên Windows.

Hai cải tiến nhỏ (đánh dấu trang và copy trích dẫn có nguồn) mới là đề xuất trong
bản phân công, chưa được giao triển khai. Ưu tiên ba chức năng ổn định và dễ bảo trì.
