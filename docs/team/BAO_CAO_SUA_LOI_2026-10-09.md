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
