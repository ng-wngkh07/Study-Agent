# Study Agent - Agent Học Tập

Ứng dụng học tập chạy cục bộ với ba chức năng: **tra cứu tài liệu**, **hỏi đáp có nguồn (QA)** và **thời khóa biểu từ ảnh**. 

## Bắt đầu trên Windows

Làm theo [README_WINDOWS.md](README_WINDOWS.md). Bộ cài tự chuẩn bị Python 3.12, Git, Ollama, thư viện Python và các model QA/embedding/đọc ảnh từ danh sách trong repo. Không cần tự tìm bản cài.

Nếu đã có Git:

```powershell
git clone https://github.com/ng-wngkh07/Study-Agent.git
cd Study-Agent
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup_windows.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\start_windows.ps1
```

Mở `http://127.0.0.1:8000`. Chưa có Git thì dùng hướng dẫn tải ZIP và chuẩn bị Git ở README Windows. Chỉ cần demo/kiểm thử nhẹ: chạy bộ cài với `-DemoOnly`, không tải Ollama/model.

## Cấu trúc chia sẻ

| Phần | Nội dung |
| --- | --- |
| `app/`, `run.py` | API, tìm kiếm, QA, OCR/lịch, chỉ mục và mã training |
| `static/` | Giao diện của ba chức năng |
| `scripts/` | Công cụ dùng chung; quản lý dịch vụ Mac và tiện ích corpus được ghi rõ theo nền tảng |
| `tests/`, `tests/fixtures/` | Kiểm thử và dữ liệu demo tổng hợp |
| `requirements*.txt` | Thư viện Python, Windows dùng requirements-windows.txt |
| `requirements-windows-tools.json`, `*.ps1` | Danh sách phần mềm/model Windows và script cài/chạy/test |
| `.github/`, `.gitignore`, `.gitattributes` | CI, template PR, ranh giới tài sản, quy tắc xuống dòng |
| `docs/team/`, `output/pdf/` | Phân công nhóm và PDF được cho phép |
| `corpus/` | Metadata và hướng dẫn bàn giao nguồn |
| README, CONTRIBUTING, LICH_SU_DU_AN, LICENSE | Quy tắc, hướng dẫn, nhật ký chung và giấy phép |

`src/` là tài liệu thật; `data/` chứa DB, vector, model, cache và dữ liệu cá nhân. Các phần này giữ riêng, không push/merge qua Git. Bàn giao gói có version/hash qua kho được kiểm soát; không dùng `git add -f` để vượt ignore. Script thử nghiệm gắn chat/máy cá nhân và hồ sơ Antigravity/Codex giữ local.

## Quy tắc nhóm

Đọc [quy tắc](README_QUY_TAC.md), [CONTRIBUTING](CONTRIBUTING.md), [phân công 6 người](docs/team/PHAN_CONG_6_NGUOI.md), [PDF](output/pdf/PHAN_CHIA_NHIEM_VU_DO_AN_NHOM.pdf) và [nhật ký](LICH_SU_DU_AN.md) trước thay đổi.

Tạo branch từ main mới nhất: `<loai>/<phamvi>/<ma-viec>-<ten>`, ví dụ `fix/qa/12-sua-trich-dan-minh`. Chỉ sửa phần đã nhận; phần chung cần báo và phối hợp với chủ trì bị ảnh hưởng. Mỗi PR thêm mục log tóm tắt lỗi/thay đổi, ngày giờ, file, test và giới hạn; không copy prompt. Review chéo trước khi Khải merge; không ghi đè sửa lỗi của người khác.

Lần đưa mã đầu tiên vào repo được Khải yêu cầu tại YC-169. Từ các thay đổi tiếp theo áp dụng branch/PR/review như trên.

## Phát triển và kiểm thử trên Mac

Môi trường demo dùng cùng thư viện web và nguồn tổng hợp:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-windows.txt
.venv/bin/python scripts/dev.py serve
.venv/bin/python -m pytest -c pytest.windows.ini
```

Chạy local với nguồn riêng: cấu hình `.env` theo `.env.example`, dùng `scripts/dev.py serve --profile local`. Các launcher `.command`/`.sh` và MLX dành cho Mac. Windows dùng Ollama để phát triển, không phải adapter MLX được huấn luyện trên Mac.

Khải là người duy nhất ghi corpus/index/vector chính và training. Môi trường MLX/model thật được quản lý riêng trên Mac; không chạy training từ demo. Trước học cần audit live `complete: true`, OCR review, nguồn-trang-chunk-vector đầy đủ, dedup/split/tokenizer và tài nguyên đạt. Đánh giá candidate độc lập, giữ kiến thức cũ và có rollback trước kích hoạt; không suy chất lượng từ loss hoặc test xanh.

## Nghiệm thu

CI `Team feature checks` chạy Python 3.12 trên Windows và Mac: demo, kiểm môi trường, tập feature; Windows thêm parse PowerShell, kiểm hợp đồng installer và chạy setup DemoOnly. PR còn kiểm nhật ký mới. Xem [Actions](https://github.com/ng-wngkh07/Study-Agent/actions) cho kết quả thật.

Kiểm thử mock/demo không chứng nhận chất lượng QA/đọc ảnh thật. Chạy bộ cài full từ máy chưa có công cụ, tải model và nghiệm thu ảnh/QA thật là các ca riêng cần nhóm xác nhận. Không đưa lịch cá nhân/hội thoại vào tập huấn luyện.
