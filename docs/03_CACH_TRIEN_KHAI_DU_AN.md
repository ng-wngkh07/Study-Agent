# TÀI LIỆU 03: HƯỚNG DẪN TRIỂN KHAI VÀ VẬN HÀNH DỰ ÁN STUDY AGENT

---

## 1. YÊU CẦU HỆ THỐNG VÀ PHẦN CỨNG

### 1.1. Cấu hình Phần cứng Khuyến nghị

Ứng dụng Study Agent được tối ưu hóa theo hồ sơ phần cứng **16GB RAM Profile** để có thể chạy mượt mà trên máy tính cá nhân của sinh viên và kỹ sư:

| Thành phần phần cứng | Cấu hình tối thiểu (Demo / FTS Only) | Cấu hình khuyến nghị (Full AI / VLM) | Ghi chú kiến trúc |
| :--- | :--- | :--- | :--- |
| **Hệ điều hành** | Windows 10/11 64-bit hoặc macOS 13+ | Windows 10/11 64-bit hoặc macOS (Apple Silicon M1/M2/M3/M4) | Linux và Mac Intel chưa thuộc phạm vi nghiệm thu chính thức của nhóm. |
| **Bộ vi xử lý (CPU)** | 4 Cores (Intel Core i5 Gen 8+ hoặc AMD Ryzen 3000+) | 8 Cores trở lên hoặc Apple Silicon (M-series) | CPU dùng để trích xuất văn bản PyMuPDF, FTS5 và chạy OCR bảng. |
| **Bộ nhớ RAM** | 8 GB RAM | **16 GB RAM** trở lên | Bản Full tải đồng thời mô hình ngôn ngữ và embedding; 16GB giúp tránh sập RAM. |
| **Card đồ họa (GPU/VRAM)**| Không bắt buộc (chạy CPU offload) | NVIDIA RTX 3050 (4GB VRAM) hoặc Apple Silicon Unified Memory | Hỗ trợ tăng tốc suy luận Ollama và mô hình thị giác Qwen2.5-VL. |
| **Ổ cứng trống** | 2 GB (chỉ code và dữ liệu demo) | **Tối thiểu 15 - 20 GB SSD** | Cần dung lượng để tải và lưu trữ 3 mô hình AI cục bộ qua Ollama. |
| **Kết nối mạng** | Cần cho lần đầu cài đặt thư viện và tải model. | Không cần Internet sau khi hoàn tất cài đặt (Offline 100%). | Mọi thao tác tra cứu, hỏi đáp và đọc ảnh lịch đều diễn ra cục bộ. |

### 1.2. Danh mục Phần mềm Cần chuẩn bị

1. **Python 3.12 (64-bit):** Bắt buộc cho Web Runtime trên cả Windows và macOS. (Lưu ý: Không dùng Python 3.13 cho web runtime vì các thư viện cố định trong `constraints-web-py312.txt` được biên dịch cho 3.12).
2. **Git:** Quản lý mã nguồn, clone repository và thực hiện quy trình đóng góp branch/PR.
3. **Ollama:** Nền tảng phục vụ suy luận mô hình ngôn ngữ và thị giác cục bộ.
4. **Node.js 22 LTS (Tùy chọn):** Chỉ cần thiết nếu bạn tham gia đóng góp hoặc chạy kiểm thử giao diện frontend (`node --test`). Người dùng thông thường không cần cài đặt Node.js.
5. **Windows Package Manager (WinGet):** Công cụ quản lý gói có sẵn trên Windows 10/11 phục vụ cài đặt tự động.

---

## 2. QUY TRÌNH CÀI ĐẶT TRÊN WINDOWS

Hệ thống cung cấp kịch bản cài đặt tự động toàn diện qua PowerShell (`setup_windows.ps1`). Thành viên không cần tự tìm kiếm các bộ cài đặt riêng lẻ trên Internet.

### 2.1. Cài đặt Lần đầu (Dành cho máy đã có Git)

Mở PowerShell với quyền người dùng thông thường (không cần Run as Administrator):

```powershell
# 1. Clone repository về máy
git clone https://github.com/ng-wngkh07/Study-Agent.git
cd Study-Agent

# 2. Chạy kịch bản cài đặt tự động (chọn 1 trong 2 chế độ bên dưới)
```

#### Chế độ A: Cài đặt Đầy đủ (Full Profile — Khuyến nghị cho Nghiệp vụ thật)
Chế độ này sẽ kiểm tra và cài đặt Python 3.12, Git, Ollama qua WinGet, tạo môi trường ảo `.venv`, cài thư viện Python và tự động tải 3 mô hình AI:
- `qwen2.5:3b` (Hỏi đáp học thuật QA)
- `bge-m3` (Vector Embedding ngữ nghĩa)
- `qwen2.5vl:3b` (Đọc ảnh thời khóa biểu và OCR thị giác)

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup_windows.ps1
```

> [!NOTE]
> Quá trình tải các mô hình AI có thể mất từ 10 đến 30 phút tùy thuộc vào tốc độ mạng Internet (tổng dung lượng tải về khoảng 6-7 GB). Kịch bản sẽ tự động xác minh mã băm và kiểm tra sức khỏe của từng mô hình sau khi tải xong.

#### Chế độ B: Cài đặt Rút gọn (Demo Only — Dành cho máy nhẹ hoặc sửa UI)
Nếu bạn chỉ cần kiểm tra tính năng tra cứu từ khóa, kiểm thử giao diện hoặc máy có cấu hình yếu/mạng chậm, sử dụng cờ `-DemoOnly`:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup_windows.ps1 -DemoOnly
```
*Chế độ này bỏ qua hoàn toàn việc tải Ollama và mô hình AI. Hệ thống sẽ tự động khởi tạo cơ sở dữ liệu demo sạch từ `tests/fixtures/documents` vào thư mục `data/team-demo/`.*

---

### 2.2. Cài đặt Dành cho máy Chưa có Git (Quy trình Tải ZIP)

1. Tải file mã nguồn ZIP từ GitHub: `https://github.com/ng-wngkh07/Study-Agent/archive/refs/heads/main.zip`
2. Giải nén file ZIP vào một thư mục làm việc, ví dụ: `C:\Users\<Ten_Ban>\Study-Agent-main`
3. Mở PowerShell tại thư mục vừa giải nén và chạy:
   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File .\setup_windows.ps1 -DemoOnly
   ```
4. Kịch bản sẽ tự động dùng WinGet để cài đặt Python 3.12 và Git cho hệ thống.
5. **Đóng toàn bộ cửa sổ PowerShell hiện tại và mở lại một cửa sổ PowerShell mới** để hệ thống nhận diện biến môi trường `PATH` mới.
6. Clone repo chính thức để làm việc với đầy đủ lịch sử Git và nhánh:
   ```powershell
   git clone https://github.com/ng-wngkh07/Study-Agent.git
   cd Study-Agent
   powershell -NoProfile -ExecutionPolicy Bypass -File .\setup_windows.ps1
   ```

---

## 3. QUY TRÌNH CÀI ĐẶT TRÊN MACOS

### 3.1. Cài đặt Môi trường Web Runtime (Python 3.12)

1. Cài đặt Python 3.12 và Git (khuyến nghị dùng Homebrew):
   ```bash
   brew install python@3.12 git ollama
   ```
2. Clone repository và chuẩn bị môi trường ảo:
   ```bash
   git clone https://github.com/ng-wngkh07/Study-Agent.git
   cd Study-Agent

   # Khởi tạo virtual environment dùng đúng Python 3.12
   python3.12 -m venv .venv
   source .venv/bin/activate

   # Cài đặt dependencies với các phiên bản cố định
   pip install --upgrade pip
   pip install -r requirements-dev.txt
   pip check
   ```
3. Cài đặt các mô hình trên Ollama:
   ```bash
   ollama serve &  # Chạy nền Ollama nếu chưa bật app
   ollama pull qwen2.5:3b
   ollama pull bge-m3
   ollama pull qwen2.5vl:3b
   ```

### 3.2. Cài đặt Môi trường Huấn luyện MLX Riêng biệt (Dành riêng cho TV4 - Apple Silicon)

> [!IMPORTANT]
> Môi trường huấn luyện MLX LoRA sử dụng **Python 3.13 độc lập** nằm trong thư mục `.train-venv`. Tuyệt đối không cài đặt chung vào `.venv` của web runtime để tránh xung đột phiên bản.

```bash
# Chỉ thực hiện trên máy Mac Apple Silicon (M1/M2/M3/M4)
python3.13 -m venv .train-venv
.train-venv/bin/python -m pip install --upgrade pip
.train-venv/bin/python -m pip install -r requirements-mlx.txt
.train-venv/bin/python -m pip check
```

---

## 4. KHỞI CHẠY ỨNG DỤNG VÀ CHỌN PROFILE HOẠT ĐỘNG

Ứng dụng hỗ trợ hai cấu hình chạy chính thức: **Profile Demo** (kiểm thử nhanh) và **Profile Local** (sử dụng tài liệu thực tế).

### 4.1. Khởi chạy trên Windows

Sử dụng kịch bản `start_windows.ps1`:

```powershell
# Chạy Profile Demo (Mặc định: dùng tài liệu giả lập trong tests/fixtures, lưu tại data/team-demo)
powershell -NoProfile -ExecutionPolicy Bypass -File .\start_windows.ps1

# Chạy Profile Local (Dùng tài liệu thật trong src/, lưu tại data/team-local hoặc data/)
powershell -NoProfile -ExecutionPolicy Bypass -File .\start_windows.ps1 -Profile local

# Chế độ tự động tải lại khi sửa mã nguồn (Hot Reload cho lập trình viên)
powershell -NoProfile -ExecutionPolicy Bypass -File .\start_windows.ps1 -Profile local -Reload
```

### 4.2. Khởi chạy trên macOS

Sử dụng kịch bản đa năng `scripts/dev.py`:

```bash
# Chạy Profile Demo
.venv/bin/python scripts/dev.py serve --profile demo

# Chạy Profile Local
.venv/bin/python scripts/dev.py serve --profile local

# Bật chế độ Reload
.venv/bin/python scripts/dev.py serve --profile local --reload
```

Hoặc nhấp đúp trực tiếp vào tệp `start_app.command` trong Finder trên macOS.

### 4.3. Truy cập Ứng dụng
Sau khi khởi động thành công, màn hình terminal sẽ hiển thị:
```text
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```
- **Giao diện Web người dùng:** Mở trình duyệt web truy cập: `http://127.0.0.1:8000`
- **Tài liệu API Swagger tự động:** Truy cập: `http://127.0.0.1:8000/docs`
- **Dừng máy chủ:** Nhấn tổ hợp phím `Ctrl + C` trong terminal.

---

## 5. HƯỚNG DẪN VẬN HÀNH CÁC LUỒNG NGHIỆP VỤ

### 5.1. Nạp Tài liệu Nguồn và Lập Chỉ mục (Indexing)

Khi sử dụng **Profile Local**, hệ thống không tự động quét lại toàn bộ file lúc khởi động để tiết kiệm thời gian. Khi bạn thêm sách mới vào thư mục nguồn, cần thực hiện đồng bộ chỉ mục:

#### Cách 1: Thao tác trực tiếp trên Giao diện Web
1. Đặt các file giáo trình (`.pdf`, `.docx`, `.pptx`, `.txt`, `.md`) vào thư mục `src/` (hoặc đường dẫn cấu hình trong `AGENT_SRC_DIR`).
2. Mở giao diện web tại `http://127.0.0.1:8000`.
3. Tại thanh bên (Sidebar), mở rộng mục **📚 Thư viện tài liệu** -> Nhấp nút **🔄 Đồng bộ thư viện**.
4. Hộp thoại tiến trình sẽ hiển thị trực quan số file đã quét, số trang đã trích xuất và số đoạn văn bản đã tạo.

#### Cách 2: Sử dụng Dòng lệnh CLI (`run.py`)
Mở terminal và thực thi:

```bash
# Windows
.venv\Scripts\python.exe run.py index

# macOS
.venv/bin/python run.py index
```

**Các tham số mở rộng của lệnh index:**
- `--force`: Bắt buộc lập chỉ mục lại toàn bộ từ đầu, ghi đè cơ sở dữ liệu cũ.
- `--embed-model bge-m3`: Chỉ định mô hình embedding tạo vector ngữ nghĩa (mặc định: `bge-m3`). Nếu muốn lập chỉ mục siêu tốc chỉ dùng từ khóa FTS5 (không tạo vector), truyền `--embed-model none`.
- `--ocr`: Kích hoạt OCR Tesseract cục bộ cho các trang PDF scan dạng ảnh không có lớp chữ số.
- `--force-ocr-file "ten_file.pdf"`: Ép buộc chạy OCR toàn bộ cho một file PDF bị lỗi font chữ số.

#### Bổ sung Vector Embedding sau khi lập chỉ mục:
Nếu trước đó bạn lập chỉ mục ở chế độ FTS5 và sau này muốn bổ sung tìm kiếm vector ngữ nghĩa:
```bash
.venv\Scripts\python.exe run.py embed --embed-model bge-m3
```

---

### 5.2. Kiểm tra Sức khỏe Hệ thống (Health Check)

Để kiểm tra xem môi trường máy tính đã sẵn sàng cho toàn bộ tính năng hay chưa:

```bash
# Kiểm tra tổng quát môi trường và kết nối
.venv\Scripts\python.exe scripts/dev.py check --profile local

# Kiểm tra nghiêm ngặt: Lệnh sẽ trả về mã lỗi thất bại nếu thiếu mô hình QA trong Ollama
.venv\Scripts\python.exe scripts/dev.py check --profile local --require-model
```

Kiểm tra số liệu thống kê cơ sở dữ liệu tri thức qua CLI:
```bash
.venv\Scripts\python.exe run.py status
```
Màn hình sẽ in chi tiết:
- Trạng thái kết nối máy chủ Ollama và danh sách model sẵn có.
- Tổng số tài liệu, số tài liệu scan chưa OCR, tổng số trang và tổng số chunks.
- Số lượng chunks đã có vector embedding.
- Danh sách trạng thái chi tiết của từng cuốn giáo trình.

---

### 5.3. Sử dụng Tính năng Hỏi đáp Học thuật (QA)
1. Tại giao diện chính, chọn chế độ **💬 Hỏi đáp dựa trên tài liệu**.
2. Nhập câu hỏi vào khung chat bên dưới (ví dụ: *"Ánh xạ tuyến tính được định nghĩa thế nào và cần thỏa mãn hai điều kiện gì?"*).
3. Câu trả lời sẽ hiển thị streaming trực tiếp.
4. Ở chân câu trả lời, nhấp vào các huy hiệu trích dẫn `[S1]`, `[S2]` để xem trích đoạn nguyên văn tiếng Việt và đối chiếu với giáo trình gốc.
5. Để quản lý cuộc trò chuyện:
   - Nhấp biểu tượng cây bút `✏️` trên thanh phiên để đổi tên cuộc trò chuyện.
   - Nhấp nút **📝 Tóm tắt chủ đề** để AI tự động tổng hợp ý chính của buổi học.
   - Nhấp nút **➕ Mới** trên thanh bên để mở phiên thảo luận mới độc lập.

---

### 5.4. Sử dụng Công cụ Học tập: Luyện tập & Ôn tập
1. Chuyển sang tab **🧰 Công cụ học tập**.
2. **Tab "Tạo câu hỏi":**
   - Tìm kiếm một khái niệm trong kho tài liệu (ví dụ: `trí nhớ`).
   - Nhấp nút **Chọn đoạn này để luyện tập** trên một kết quả tìm kiếm phù hợp.
   - Nhấp nút **📝 Tạo câu hỏi từ nội dung này**.
   - Hệ thống sẽ sinh tối đa 3 câu hỏi trắc nghiệm A/B/C/D. Chọn đáp án và xem kết quả giải thích kèm trích dẫn nguyên văn bằng chứng từ trang sách.
3. **Tab "Ôn tập":**
   - Các câu hỏi bạn trả lời sai hoặc chọn nút *"Chưa chắc"* sẽ tự động được lưu vào tab này.
   - Bạn có thể làm lại bài bất cứ lúc nào để củng cố kiến thức. Dữ liệu lưu cục bộ trong `localStorage` của trình duyệt và có nút xóa toàn bộ khi đã nắm vững.
4. **Tab "Trích xuất bài tập mẫu":**
   - Chọn một cuốn giáo trình và nhập khoảng trang cần ôn (ví dụ: từ trang 20 đến trang 45).
   - Nhấp **Tìm bài tập mẫu** để xem danh sách toàn bộ các bài tập thực hành nguyên bản có trong tài liệu.

---

### 5.5. Sử dụng Tính năng Số hóa Thời khóa biểu từ Ảnh
1. Chuyển sang tab **📅 Thời khóa biểu từ ảnh**.
2. Kéo thả file ảnh chụp thời khóa biểu vào khung tải ảnh.
3. Chờ hệ thống phân tích và hiển thị **Bảng nháp (Draft Table)**:
   - Kiểm tra các thông tin: Thứ, Tên môn học, Tiết, Giờ bắt đầu, Giờ kết thúc, Phòng học.
   - Nếu thời khóa biểu chỉ ghi theo tiết (ví dụ: Tiết 1-3) mà chưa có giờ đồng hồ, sử dụng khung **Công cụ điền giờ theo tiết học** bên trái để áp dụng khung giờ cho các tiết học.
   - Bổ sung hoặc chỉnh sửa trực tiếp các ô thông tin chưa rõ.
4. Chọn tùy chọn: *Ghi đè toàn bộ lịch học đang lưu* hoặc *Ghép thêm môn mới*.
5. Nhấp nút **💾 Xác nhận & Lưu vào lịch học**.
6. Để xuất lịch sang điện thoại hoặc máy tính:
   - Nhập ngày bắt đầu học kỳ (ví dụ: `2026-09-01`) và ngày kết thúc học kỳ (ví dụ: `2027-01-15`).
   - Nhấp **📥 Tải tệp .ics**.
   - Mở file `.ics` vừa tải về trên máy tính hoặc gửi qua điện thoại để tự động thêm toàn bộ lịch học lặp lại hàng tuần vào Google Calendar, Apple Calendar hoặc Outlook.

---

### 5.6. Quy trình Thẩm định OCR Cục bộ (Human-in-the-loop Review)
Đối với các tài liệu scan chữ xấu hoặc sách chuyên ngành có công thức phức tạp:
1. Mở menu **📚 Thư viện tài liệu** -> Nhấp nút **📝 Thẩm định OCR cục bộ**.
2. Chọn tài liệu nguồn và số trang cần nhận diện, nhấp **▶ Chạy OCR (qwen2.5vl:3b)**.
3. Khi kết quả hoàn tất, nhấp **Soát lỗi & Duyệt** trên dòng tương ứng trong bảng.
4. Màn hình chia đôi sẽ hiển thị:
   - Bên trái: Ảnh chụp trang gốc của tài liệu.
   - Bên phải: Khung văn bản cho phép chỉnh sửa trực tiếp nội dung nhận diện.
5. Người thẩm định nhập tên người duyệt, ghi chú sửa đổi và nhấp **💾 Lưu xác minh & Duyệt**.
6. Hệ thống sẽ tự động cập nhật lại các đoạn chunks và chỉ mục FTS5 của trang sách đó trong cơ sở dữ liệu.

---

## 6. QUY TRÌNH KIỂM THỬ VÀ ĐẢM BẢO CHẤT LƯỢNG (QA & TESTING)

Dự án Study Agent áp dụng tiêu chuẩn kiểm thử tự động nghiêm ngặt để đảm bảo không xảy ra lỗi hồi quy khi cập nhật tính năng.

### 6.1. Chạy Kiểm thử trên Windows

Sử dụng kịch bản PowerShell `test_windows.ps1`:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\test_windows.ps1
```
Kịch bản sẽ thực thi toàn bộ tập kiểm thử được chỉ định trong `pytest.windows.ini`, bao gồm hơn 120+ ca kiểm thử:
- Kiểm tra tính tương thích nền tảng và hỗ trợ UTF-8 (`test_platform_support.py`).
- Kiểm tra bảo chứng trích dẫn nguồn `[S#]` (`test_grounded_citations.py`).
- Kiểm tra độ tin cậy hội thoại và ngân sách ngữ cảnh (`test_dialogue_reliability.py`).
- Kiểm tra tính năng thời khóa biểu và xuất lịch .ics (`test_timetable_feature.py`).
- Kiểm tra an toàn y tế và từ chối chẩn đoán (`test_safety.py`).
- Kiểm tra dịch vụ sinh trắc nghiệm và hợp đồng giao diện (`test_practice.py`, `test_learning_tools_ui_contract.py`).
- Kiểm tra hồi quy các lỗi đã khắc phục (`test_audit_regressions.py`).

### 6.2. Chạy Kiểm thử trên macOS

```bash
# Chạy toàn bộ feature tests qua cấu hình windows/shared
.venv/bin/python -m pytest -c pytest.windows.ini

# Chạy kiểm tra tính tương thích thư viện
.venv/bin/python -m pip check
```

### 6.3. Kiểm thử Giao diện Người dùng (UI DOM Testing với Node.js)

Kiểm tra tính toàn vẹn của logic DOM JavaScript (yêu cầu Node.js 22):

```bash
# Kiểm tra giao diện tra cứu tài liệu
node --test tests/document_lookup_ui.test.cjs

# Kiểm tra giao diện công cụ học tập (luyện tập, ôn tập, trích xuất bài tập)
node --test tests/practice_ui.test.cjs
```

### 6.4. Kiểm tra Quy chuẩn Nhật ký Dự án trong CI

Mọi Pull Request gửi lên repository đều được GitHub Actions kiểm tra tự động xem tác giả PR đã cập nhật lịch sử thay đổi vào tệp `LICH_SU_DU_AN.md` hay chưa:

```bash
python scripts/check_history.py --base origin/main
```

---

## 7. QUẢN LÝ CẤU HÌNH BIẾN MÔI TRƯỜNG (`.env`)

Tệp cấu hình `.env` cho phép ghi đè các thiết lập mặc định của ứng dụng. Để sử dụng, sao chép từ tệp mẫu:
```powershell
# Windows
Copy-Item .env.example .env

# macOS
cp .env.example .env
```

Bảng giải thích chi tiết các biến môi trường được hỗ trợ:

| Tên biến môi trường | Giá trị mặc định | Mô tả chi tiết và Phạm vi ảnh hưởng |
| :--- | :--- | :--- |
| `AGENT_SRC_DIR` | `src` | Thư mục chứa giáo trình và tài liệu học tập của người dùng. |
| `AGENT_DATA_DIR` | `data` | Thư mục lưu trữ toàn bộ cơ sở dữ liệu CSDL, vector và cache. |
| `HISTORY_DB_PATH` | `data/history.db` | Đường dẫn tệp SQLite lưu trữ các phiên hội thoại hỏi đáp. |
| `TIMETABLE_DB_PATH` | `data/timetable.db` | Đường dẫn tệp SQLite lưu trữ lịch học và bản nháp thời khóa biểu. |
| `TIMETABLE_IMAGES_DIR` | `data/timetable_images` | Thư mục lưu trữ các file ảnh thời khóa biểu gốc theo mã băm SHA-256. |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Địa chỉ máy chủ dịch vụ Ollama cục bộ. |
| `DEFAULT_CHAT_MODEL` | `qwen2.5:3b` | Tên mô hình LLM chính dùng cho hỏi đáp QA và sinh trắc nghiệm. |
| `DEFAULT_EMBED_MODEL` | `bge-m3` | Tên mô hình embedding dùng để biểu diễn vector ngữ nghĩa. |
| `OLLAMA_AUX_CHAT_MODEL`| `qwen2.5vl:3b` | Tên mô hình thị giác VLM dùng để đọc ảnh thời khóa biểu và OCR. |
| `HOST` | `127.0.0.1` | Địa chỉ IP lắng nghe của máy chủ web (mặc định: chỉ localhost). |
| `PORT` | `8000` | Cổng dịch vụ HTTP của máy chủ web. |

> [!WARNING]
> Tệp `.env` chứa các đường dẫn cục bộ trên máy tính của bạn và đã được đưa vào `.gitignore`. Tuyệt đối không xóa bỏ quy tắc bỏ qua này để tránh đưa đường dẫn máy cá nhân lên kho lưu trữ chung.

---

## 8. MA TRẬN XỬ LÝ SỰ CỐ THƯỜNG GẶP (TROUBLESHOOTING MATRIX)

| Hiện tượng lỗi | Nguyên nhân gốc rễ | Hướng dẫn cách khắc phục chuẩn xác |
| :--- | :--- | :--- |
| **`Command failed: winget.exe` hoặc lỗi cài đặt WinGet trên Windows** | Máy Windows cũ chưa kích hoạt App Installer hoặc quyền PowerShell bị chặn. | 1. Mở PowerShell và chạy: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`<br>2. Chạy lại `.\setup_windows.ps1`<br>3. Nếu vẫn lỗi, cập nhật ứng dụng *App Installer* từ Microsoft Store. |
| **`Existing .venv is not Python 3.12` khi chạy setup Windows** | Thư mục `.venv` trước đó được tạo bằng phiên bản Python khác (ví dụ: Python 3.10 hoặc 3.11). | Đổi tên hoặc xóa thư mục môi trường ảo cũ:<br>`Rename-Item .venv .venv-backup`<br>Sau đó chạy lại kịch bản cài đặt: `.\setup_windows.ps1`. |
| **Cổng 8000 đã bị chiếm dụng (`Address already in use`)** | Một tiến trình khác (hoặc một phiên Study Agent cũ) đang chạy ngầm trên cổng 8000. | 1. Tìm và dừng tiến trình cũ trên Windows:<br>`Get-Process python \| Stop-Process`<br>2. Hoặc cấu hình đổi cổng trong file `.env`: Thêm dòng `PORT=8080`. |
| **Ollama mất kết nối (`🔴 Chưa kết nối` tại `run.py status`)** | Dịch vụ Ollama chưa được bật hoặc cổng 11434 bị tường lửa chặn. | 1. Khởi động ứng dụng Ollama từ Start Menu hoặc chạy lệnh: `ollama serve`<br>2. Kiểm tra truy cập qua trình duyệt tại: `http://127.0.0.1:11434` (phải hiển thị *"Ollama is running"*). |
| **Báo thiếu mô hình (`Missing model after pull`)** | Quá trình tải mô hình từ mạng Internet bị gián đoạn giữa chừng. | Tải thủ công mô hình bị thiếu qua terminal:<br>`ollama pull qwen2.5:3b`<br>`ollama pull bge-m3`<br>`ollama pull qwen2.5vl:3b` |
| **Tài liệu mới sao chép vào `src/` không xuất hiện khi tìm kiếm** | Profile Local không tự động quét lại toàn bộ file lúc khởi động máy chủ. | Mở giao diện web, tại mục **📚 Thư viện tài liệu** nhấp **🔄 Đồng bộ thư viện**, hoặc chạy lệnh CLI: `.venv\Scripts\python.exe run.py index`. |
| **Lỗi HTTP 503 `GPU hiện đang được sử dụng để huấn luyện mô hình`** | Hệ thống GPU Lock đang bị khóa độc quyền bởi một tiến trình huấn luyện MLX LoRA hoặc tiến trình cũ bị crash chưa giải phóng lock. | 1. Nếu đang có đợt train thật: Chờ tiến trình hoàn tất.<br>2. Nếu tiến trình đã tắt mà vẫn báo bận (stale lock): Hệ thống sẽ tự động phục hồi (Auto-heal), hoặc bạn có thể xóa tệp khóa thủ công tại `data/runtime/gpu.lock`. |
| **Lỗi `Invalid .env setting: KEY` khi khởi động** | Tệp `.env` chứa tên biến không nằm trong danh mục `ENV_KEYS` hợp lệ hoặc có dòng bị sai cú pháp. | Mở tệp `.env`, đối chiếu lại với tệp `.env.example`. Đảm bảo các khóa chỉ nằm trong danh mục cho phép và giá trị không bị để trống vô lý. |
| **Ảnh thời khóa biểu trích xuất ra bảng nháp bị rỗng môn học** | Ảnh quá mờ, góc chụp quá nghiêng, hoặc độ phân giải quá thấp (< 10px). | Chụp lại ảnh rõ nét, vuông góc với màn hình hoặc thời khóa biểu in giấy; đảm bảo các chữ số giờ học và tên môn học đọc được bằng mắt thường. |

---

## 9. QUY CHUẨN ĐÓNG GÓP VÀ BẢO TOÀN DỮ LIỆU NHÓM

Khi tham gia phát triển dự án Study Agent, toàn bộ thành viên cần tuân thủ nghiêm ngặt các quy tắc sau (theo `CONTRIBUTING.md` và `README_QUY_TAC.md`):

1. **Quy tắc Đặt tên Nhánh (Branch Naming):**
   - Định dạng chuẩn: `<loai>/<phamvi>/<ma-viec>-<ma-vai-tro>`
   - Ví dụ:
     - TV1 sửa lỗi tra cứu: `fix/lookup/12-sai-trang-tv1`
     - TV2 cải tiến QA: `feature/qa/15-nguon-bilingual-tv2`
     - TV3 sửa lỗi xuất lịch: `fix/timetable/08-fold-ics-tv3`
     - TV5 tích hợp giao diện: `feature/shared/20-theme-toggle-tv5`
     - TV6 bổ sung test hồi quy: `test/shared/25-audit-f01-tv6`
2. **Quy tắc Cập nhật Nhật ký (`LICH_SU_DU_AN.md`):**
   - Mọi Pull Request bắt buộc phải bổ sung một mục nhật ký mới vào đầu mục lịch sử chung.
   - Định dạng ID nhật ký: `LOG-YYYYMMDD-chucnang-maviec-tvN` (ví dụ: `LOG-20261010-ui-pr6-fix-codex`).
   - Ghi rõ: Người thực hiện, lỗi/mục tiêu, trước/sau thay đổi, file đã sửa, kết quả kiểm thử (PASS/FAIL/NOT_RUN) và các hạn chế còn lại.
   - **Tuyệt đối không copy prompt hội thoại nội bộ vào file nhật ký.**
3. **Ranh giới Tài sản Tuyệt đối:**
   - Chỉ commit lên Git: Mã nguồn, giao diện HTML/CSS/JS, script vận hành, test tổng hợp và tài liệu nhóm.
   - **Tuyệt đối không commit lên Git:**
     - Toàn bộ file trong thư mục `src/` (sách giáo trình bản quyền).
     - Toàn bộ file trong thư mục `data/` (`knowledge_base.db`, `history.db`, `timetable.db`, model weights, adapter).
     - Tệp cấu hình môi trường `.env`.
     - Ảnh lịch học cá nhân và lịch sử câu hỏi của người dùng.
   - Trước khi tạo commit, luôn kiểm tra trạng thái bằng `git status` và tuyệt đối **không sử dụng `git add -f`** để vượt qua `.gitignore`.
