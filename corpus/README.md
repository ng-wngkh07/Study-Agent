# Metadata corpus dùng chung

Thư mục này chứa bản kê và hồ sơ bàn giao được phép chia sẻ qua Git. Nguồn được nạp vào `src/` trên máy chạy; dữ liệu sinh ra ở `data/` không commit vào repo mã. Xem [quy trình nhóm](../CONTRIBUTING.md).

## Cấu trúc khi có gói thật

```text
corpus/
  manifests/sources.jsonl                 # nguồn có hash/quyền/vị trí tải
  submissions/<ma-goi>/manifest.json      # một gói, một revision
  submissions/<ma-goi>/reviews.jsonl      # chỉ commit nếu nội dung được phép
  submissions/<ma-goi>/CHECKS.md          # kết quả kiểm và phần chưa rõ
  releases/<ma-release>/manifest.json     # người điều phối công bố
```

Hiện chỉ README này được tạo. Đường dẫn trên là quy ước cho gói thật; chưa tạo manifest/approval/release giả. Chưa có importer runtime đọc trực tiếp cấu trúc này. TV4 điều phối triển khai và kiểm chứng adapter giao nhận giữ nguyên gate trước khi tự động nhập.

## Gói nộp phải có

- `submission_id`, `revision`, `submitted_by`, thời gian thật ISO 8601, `status` (`pending_review`, `reviewed`, `rejected`), reviewer và quyết định.
- Từng nguồn: `source_relpath` tương đối với `src/`, `source_sha256`, số trang/đơn vị, môn, quyền chia sẻ, `artifact_ref`/hash/kích thước gói tải. Không ghi khóa/URL có token vào Git.
- Từng review: `(source_sha256, page, revision)`, loại nội dung, transcript/visual description, `completeness`, `unresolved`, người duyệt/thời gian, bằng chứng ảnh/raw capture và SHA-256.
- Đường dẫn bằng chứng tương đối trong gói, không dùng đường dẫn máy cá nhân hoặc ID SQLite; mô tả cách ánh xạ runtime trên máy nhận. Không thay nội dung raw capture/tái băm chỉ để hợp thức hoá đường dẫn.
- Danh sách complete/partial/pending, báo cáo nguồn và indexing thử nếu có; bước chưa chạy ghi `NOT_RUN`. Giữ revision cũ, gói đã duyệt không sửa tại chỗ.

Review runtime hiện dùng `filename`, `page`, `source_sha256`, `kind`, `image_reviewed`, `transcript`/`visual_description`, `completeness`, `unresolved`, `image_path`, `image_sha256`, `raw_capture_path`, `raw_capture_sha256`, `reviewed_at`. `app/source_page_reviews.py` kiểm hash và binding với raw capture. Gói là lớp giao nhận; không thay format/cổng runtime bằng bản kê tự khai `reviewed`.

## Release phải có

`release_id`, code commit, manifest nguồn/review và hash, artifact ref/hash/kích thước, embedding model/digest/dimensions, chunking config, policy corpus, readiness/thời gian audit, dataset/split/model revision/run ID nếu có training, kết luận đánh giá và người duyệt. Corpus release/model release có thể khác nhau; index mới chưa có adapter mới là hợp lệ.

Snapshot index phải đủ nguồn/bằng chứng/policy để kiểm lại, không chỉ `knowledge_base.db`. Người nhận kiểm integrity, hash, nguồn/trang/vector và mở PDF/ảnh trên máy đích. Bước chưa tự động hoá ghi rõ trong release.


## Nhận nguồn để phát triển trên máy riêng

Đây là quy ước bàn giao, không phải lệnh nhập tự động. Người gửi cung cấp artifact/ref,
manifest và SHA-256 qua kho được phép; người nhận kiểm hash/quyền/revision và review
trước khi đưa nguồn vào `src/` của clone riêng. Khởi động profile local với `AGENT_DATA_DIR`
riêng, chọn **Đồng bộ thư viện**, kiểm lỗi index và nguồn/trang/chunk. Xem [Mac](../README_MAC.md)
hoặc [Windows](../README_WINDOWS.md). Không đưa DB/vector/weights vào PR; kết quả index thử
không cấp quyền hợp nhất corpus chính hay training. Khi xây importer, thêm schema/validator
và kiểm provenance thực; hiện chưa có ví dụ manifest giả được coi là release đã duyệt.
