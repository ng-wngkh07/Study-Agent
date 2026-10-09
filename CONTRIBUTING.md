# Làm việc nhóm với Agent Học Tập

Đọc [quy tắc dự án](README_QUY_TAC.md), [phân công 6 người](docs/team/PHAN_CONG_6_NGUOI.md),
[hướng dẫn Windows](README_WINDOWS.md) và [nhật ký chung](LICH_SU_DU_AN.md).

## Phân công

TV1 tra cứu, TV2 QA, TV3 lịch từ ảnh; cả ba sửa UI/API/test theo chức năng.
(TV4, Mac) là người huấn luyện duy nhất và hợp nhất corpus/index/vector chính.
TV5 giao diện/môi trường chung; TV6 kiểm thử/nghiệm thu/tài liệu. Năm người còn lại Windows.
Hai vai trò hỗ trợ có đầu ra riêng, không tạo thêm tính năng lớn để chia người.

## Quy trình một thay đổi

1. Đọc lịch sử theo lỗi/file/chức năng và main mới nhất; giữ các sửa lỗi/tính năng đã nghiệm thu.
2. Chốt Issue, chủ trì, tiêu chí và ảnh hưởng. Nếu sửa phần chung/ngoài phạm vi, báo trước và
   thống nhất giải pháp nhỏ nhất, tương thích, test, migration/rollback với người bị ảnh hưởng.
3. Tạo nhánh `<loai>/<phamvi>/<ma-viec>-<ten>` từ main: ví dụ `fix/qa/12-sua-trich-dan-minh`.
   Cập nhật từ origin/main trước merge, xử lý xung đột cùng chủ trì; không ghi đè cả file.
4. Tái hiện, sửa đúng phần, kiểm thử. Thay phần chung phải smoke cả tra cứu, QA và lịch ảnh.
5. Tác giả thêm mục nhật ký: ngày/giờ, lỗi/mục tiêu, trước/sau, phần sửa, ảnh hưởng, checks,
   NOT_RUN và log cũ liên quan. Không copy prompt hoặc tạo log riêng cho từng người.
6. Push nhánh, mở PR vào main. Ít nhất một reviewer khác; phần chung cần chủ trì bị ảnh hưởng
   review. Khải merge sau check phù hợp; TV6 kiểm tích hợp và nhóm đồng bộ main.
7. Training là đợt riêng trên Mac sau cổng nguồn/model đạt, không tự chạy vì PR mã đã merge.

Không push trực tiếp main, force-push nhánh chung, tắt test để che lỗi hoặc tự sửa rộng phần
người khác. Giữ một người ghi module dùng chung tại một thời điểm, hoặc phối hợp PR tách biệt.
Chỉnh local qua .env, báo nếu đó là điều kiện chạy; không commit setting/đường dẫn cá nhân.

## Phạm vi Git và model

Chia sẻ mã/UI/scripts/tests-mẫu/dependency/config mẫu/CI/docs/nhật ký/metadata corpus và
PDF phân công được phép. Nguồn thật src, toàn data, docs/project và tích hợp/cache/bí mật
cá nhân giữ riêng. Không vượt .gitignore bằng git add -f; không merge SQLite/vector/weights.

1 writer duy nhất hợp nhất corpus/training, không tạo writer thứ hai khi job còn chạy. Readiness
live complete: true, OCR review và provenance toàn nguồn-trang-chunk-vector, dedup/split/
tokenizer/tài nguyên phải đạt. TV6 phối hợp chủ trì đánh giá candidate độc lập, giữ kiến thức
cũ và rollback trước phát hành; loss/test xanh chưa đủ. Windows Ollama không phải adapter MLX.

## Bàn giao

PR cần phạm vi đúng, review, test phù hợp, nhật ký và giới hạn rõ. Tập test feature không
thay kiểm model/ảnh thật; không suy Windows đạt từ Mac. CI/bảo vệ main chỉ có kết quả/trạng
thái thật sau cấu hình và chạy trên repo. Hai cải tiến nhỏ trong phân công là đề xuất, chưa triển khai.
