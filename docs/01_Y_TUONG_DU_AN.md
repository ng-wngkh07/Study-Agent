# TÀI LIỆU 01: Ý TƯỞNG DỰ ÁN STUDY AGENT (BAMITIKA AI)

---

## 1. TỔNG QUAN DỰ ÁN

### 1.1. Tên dự án và Định danh Hệ thống
- **Tên dự án:** Study Agent — Trợ Lý Học Tập Cục Bộ.
- **Tên thương hiệu giao diện:** **BaMiTiKa AI** (*Tra cứu tài liệu và hỏi đáp đa lĩnh vực*).
- **Khẩu hiệu cốt lõi:** *"100% Cục bộ & Miễn phí — Bảo vệ quyền riêng tư — Dẫn nguồn minh bạch"*.
- **Phiên bản kiến trúc hiện tại:** `2026-10-05-content-images-literal-timetable` kết hợp với dialogue policy `2026-10-03-single-request-context-budget` và bộ mở rộng học tập `2026-10-10-learning-tools`.

### 1.2. Mục tiêu Dự án
Dự án Study Agent được thiết kế nhằm xây dựng một **Hệ sinh thái Trợ lý Học tập Tự quản (Self-hosted & Local-first Academic Assistant)** chạy hoàn toàn trên phần cứng của người dùng (máy trạm Windows hoặc macOS Apple Silicon). Mục tiêu cốt lõi bao gồm:
1. **Triệt tiêu nguy cơ rò rỉ dữ liệu học tập cá nhân:** Toàn bộ giáo trình, tài liệu chuyên ngành, lịch học cá nhân, ảnh chụp thời khóa biểu và nhật ký hội thoại được lưu trữ và xử lý cục bộ; không gửi bất kỳ dữ liệu nào lên máy chủ đám mây của bên thứ ba.
2. **Khắc phục triệt để ảo giác (Hallucination) của mô hình ngôn ngữ lớn (LLM):** Ép buộc mọi câu trả lời phải được bảo chứng bằng bằng chứng trích xuất từ tài liệu học tập thực tế thông qua kiến trúc Tìm kiếm Tăng cường Tạo sinh lai (Hybrid RAG: FTS5 BM25 + Vector Embeddings kết hợp thuật toán Reciprocal Rank Fusion - RRF).
3. **Minh bạch hóa tri thức học thuật:** Mọi luận điểm trả lời đều phải đính kèm mã định danh trích dẫn `[S#]` có thể nhấp chuột để mở trực tiếp trang tài liệu PDF gốc hoặc đoạn văn bản nguồn tương ứng.
4. **Tự động hóa số hóa lịch biểu học tập:** Sử dụng mô hình thị giác ngôn ngữ cục bộ (Vision-Language Model - VLM) và nhận diện ký tự quang học dạng bảng (Literal Table OCR) để phân tích ảnh chụp thời khóa biểu thành lịch học có cấu trúc, kiểm tra xung đột và xuất ra định dạng tiêu chuẩn quốc tế iCalendar (`.ics`).
5. **Cung cấp công cụ tự luyện tập chủ động (Active Learning):** Tự động sinh bộ câu hỏi trắc nghiệm bám sát theo từng trang sách được chọn, thẩm định đáp án hai bước bằng mô hình và lưu trữ danh sách ôn tập cá nhân.

### 1.3. Bài toán Thực tế Cần Giải Quyết
Trong quá trình học tập và nghiên cứu học thuật của sinh viên và giảng viên, có 4 rào cản lớn thường gặp:
1. **Khối lượng giáo trình đồ sộ và phân tán:** Sinh viên phải đọc hàng nghìn trang giáo trình PDF/sách scan (Đại số tuyến tính, Lập trình C++, Tâm lý học, Khoa học dữ liệu...). Việc tìm kiếm một định lý, công thức hoặc khái niệm cụ thể qua Ctrl+F thông thường thường thất bại do khác biệt ngữ nghĩa, lỗi OCR hoặc từ đồng nghĩa.
2. **Sự không đáng tin cậy của các AI đám mây phổ thông:** Khi hỏi ChatGPT hoặc Claude về các định lý toán học phức tạp hoặc trích dẫn giáo trình môn học, mô hình thường tự bịa ra công thức, làm mất đi giả thiết/điều kiện xác định, hoặc trích dẫn sai số trang và tên sách.
3. **Mất an toàn dữ liệu và chi phí API đắt đỏ:** Việc tải toàn bộ tài liệu nghiên cứu nội bộ, bài giảng chưa xuất bản hoặc thông tin lịch trình cá nhân lên các dịch vụ đám mây vi phạm quyền riêng tư và phát sinh chi phí duy trì API liên tục.
4. **Nhập liệu thủ công thời khóa biểu phức tạp:** Đầu mỗi học kỳ, sinh viên nhận ảnh chụp màn hình lịch đăng ký môn học hoặc thời khóa biểu dạng bảng với các cột Lý thuyết (LT), Thực hành (TH), phân chia theo tiết học (Tiết 1-3, Tiết 7-9) hoặc khung giờ lẻ. Việc tự gõ lại từng môn vào Google Calendar hay Apple Calendar rất tốn thời gian và dễ nhầm lẫn gây trùng lịch.

### 1.4. Đối tượng Sử dụng
- **Sinh viên đại học & cao đẳng:** Cần tra cứu nhanh định nghĩa, ôn tập bài giảng, làm bài tập trắc nghiệm tự đánh giá và quản lý thời khóa biểu học kỳ.
- **Học viên cao học & Nhà nghiên cứu:** Cần một công cụ tra cứu tài liệu học thuật chuyên sâu ngoại tuyến, giữ nguyên bản quyền tài liệu, hỗ trợ dịch thuật ngữ song ngữ Anh - Việt có kiểm chứng.
- **Giảng viên & Trợ giảng:** Quản lý kho bài giảng, trích xuất bài tập mẫu có sẵn trong giáo trình và thẩm định chất lượng số hóa tài liệu scan.

### 1.5. Giá trị Mang lại
- **Chạy 100% Cục bộ (Local-first):** Hoạt động hoàn toàn không cần Internet sau khi đã cài đặt dependencies và tải weights mô hình. Không phụ thuộc vào bất kỳ nhà cung cấp dịch vụ đám mây nào.
- **Zero Privacy Leakage:** Dữ liệu cá nhân, câu hỏi hỏi đáp, ảnh lịch không bao giờ rời khỏi thiết bị người dùng.
- **Truy xuất Nguồn gốc Tuyệt đối (Absolute Grounded Citations):** Câu trả lời gắn nhãn `[S1]`, `[S2]` tương ứng với từng đoạn trích cụ thể. Hệ thống có cơ chế kiểm tra chéo (Source Attribution Guard) tự động từ chối câu trả lời nếu mô hình tự ý bịa ra mã trích dẫn hoặc nói ngoài tài liệu.
- **An toàn Y tế & Tâm lý (Safety & Crisis Guard):** Tích hợp bộ lọc quy tắc từ chối chẩn đoán bệnh tật, từ chối kê đơn, và phát hiện khẩn cấp các biểu hiện khủng hoảng tâm lý/tự hại để kích hoạt thông tin cứu trợ đường dây nóng y tế 115 Việt Nam.
- **Tối ưu hóa Tài nguyên Phần cứng 16GB RAM:** Kiến trúc phân định tài nguyên chặt chẽ với cơ chế khóa GPU liên tiến trình (Inter-process GPU Lock) giúp các mô hình 3B (LLM, Embedding, VLM) chạy mượt mà trên laptop cá nhân mà không gây sập RAM (Out-Of-Memory - OOM).

### 1.6. Phạm vi Hệ thống (System Scope)
Hệ thống Study Agent phân định ranh giới chức năng rõ ràng thành **3 trụ cột nghiệp vụ chính** và các công cụ hỗ trợ:
1. **Chế độ 1 — Tra cứu tài liệu (Document Lookup):** Tra cứu từ khóa (FTS5 BM25) kết hợp ngữ nghĩa (Vector Embedding), xem trước tài liệu, render trực tiếp ảnh trang gốc từ PDF, lọc theo từng đầu sách.
2. **Chế độ 2 — Hỏi đáp có nguồn (Academic QA) & Công cụ học tập:**
   - *Hỏi đáp RAG hội thoại:* Đặt câu hỏi theo ngữ cảnh, ghi nhận hội thoại đa lượt (Multi-turn Sessions), tóm tắt chủ đề tự động, quản lý cửa sổ ngữ cảnh UTF-8 nghiêm ngặt.
   - *Tạo câu hỏi luyện tập (Practice Service):* Sinh câu hỏi trắc nghiệm 4 lựa chọn từ trang sách được chọn, xác thực bằng chứng nguyên văn hai bước (Dual Verification), lưu trữ câu sai/chưa chắc vào danh sách ôn tập trình duyệt (`localStorage`).
   - *Trích xuất bài tập mẫu (Example Exercises Extraction):* Lọc nguyên văn các bài tập có sẵn trong sách mà không qua chỉnh sửa của AI.
3. **Chế độ 3 — Thời khóa biểu từ ảnh (Vision Timetable):** Phân tích ảnh lịch chụp bằng VLM (`qwen2.5vl:3b`) hoặc Local Literal Table OCR, trích xuất thành bản nháp (Draft), cung cấp giao diện rà soát chỉnh sửa, phát hiện xung đột lịch, chuyển đổi tiết học sang giờ đồng hồ và xuất file iCalendar (`.ics`).
4. **Phạm vi Ngoài hệ thống (Explicit Non-Goals):**
   - Không cung cấp chẩn đoán y khoa, không kê đơn thuốc, không tư vấn tâm lý lâm sàng.
   - Không can thiệp, chỉnh sửa file PDF gốc trong thư mục nguồn.
   - Không đồng bộ đám mây và không dùng dữ liệu lịch cá nhân của người dùng để đưa vào tập huấn luyện (Fine-tuning).
   - Hệ thống huấn luyện chuyên sâu MLX LoRA chỉ áp dụng trên máy Mac của người điều phối (TV4); môi trường Windows chỉ phục vụ suy luận, kiểm thử và nghiệp vụ người dùng.

---

## 2. Ý TƯỞNG VÀ CÁCH GIẢI QUYẾT BÀI TOÁN

### 2.1. Bản chất Vấn đề và Triết lý Thiết kế
Mô hình ngôn ngữ lớn (LLM) bản chất là một bộ máy dự đoán token tiếp theo dựa trên phân phối xác suất thống kê. Khi được yêu cầu trả lời một câu hỏi học thuật:
- Nếu không có ngữ cảnh, mô hình sẽ "bịa" (hallucinate) các dữ kiện có vẻ hợp lý nhưng sai lệch bản chất.
- Nếu đưa ngữ cảnh quá dài, mô hình sẽ gặp hiện tượng "lost in the middle", bỏ quên các điều kiện biên của bài toán.
- Nếu phụ thuộc vào mô hình thương mại qua API, chi phí tính toán tăng theo số trang sách và tiềm ẩn rủi ro lộ bí mật học thuật.

**Triết lý giải quyết của Study Agent:**
> *"Biến LLM từ một nguồn tri thức vạn năng thành một bộ máy suy luận và tổng hợp dựa trên bằng chứng khép kín (Closed-domain Evidence Synthesizer)."*

### 2.2. Phương pháp Giải quyết Kỹ thuật

```
                     ┌────────────────────────────────────────────────────────┐
                     │              NGUỒN TÀI LIỆU (src/ hoặc Demo)           │
                     │          (PDF, DOCX, PPTX, TXT, MD, PNG/JPG)           │
                     └───────────────────────────┬────────────────────────────┘
                                                 │
                                                 ▼
                     ┌────────────────────────────────────────────────────────┐
                     │            BỘ TRÍCH XUẤT VÀ CHUẨN HÓA DỮ LIỆU          │
                     │  • PyMuPDF / python-docx / python-pptx trích xuất      │
                     │  • Vision OCR (Tesseract / Ollama VLM) cho trang scan  │
                     │  • Text Cleaner: Chuẩn hóa NFC, sửa TCVN3, gộp từ      │
                     │  • Text Chunker: Cắt đoạn 1200 ký tự, overlap 200      │
                     └───────────────────────────┬────────────────────────────┘
                                                 │
                                                 ▼
                     ┌────────────────────────────────────────────────────────┐
                     │           LƯU TRỮ CHỈ MỤC KÉP (DUAL INDEX STORE)       │
                     │  • SQLite FTS5: BM25 Full-text search (không dấu)      │
                     │  • Binary BLOB Vector: BGE-M3 1024-dim Embeddings      │
                     └───────────────────────────┬────────────────────────────┘
                                                 │
                   ┌─────────────────────────────┴─────────────────────────────┐
                   ▼                                                           ▼
    ┌───────────────────────────────┐                           ┌───────────────────────────────┐
    │     TRUY XUẤT TỪ KHÓA (FTS)   │                           │    TRUY XUẤT NGỮ NGHĨA (VEC)  │
    │   • BM25 rank score           │                           │   • Cosine similarity score   │
    │   • Hạ điểm Heading / Mục lục │                           │   • Ngưỡng lọc tối thiểu 0.15 │
    │   • Nhận diện tên sách/chương │                           │   • GPU Lock bảo vệ suy luận  │
    └──────────────┬────────────────┘                           └──────────────┬────────────────┘
                   │                                                           │
                   └─────────────────────────────┬─────────────────────────────┘
                                                 ▼
                     ┌────────────────────────────────────────────────────────┐
                     │             RECIPROCAL RANK FUSION (RRF)               │
                     │       Score = 0.5/(60 + Rank_FTS) + 0.5/(60 + Rank_Vec)│
                     │   • Khử trùng lặp nội dung văn bản                     │
                     │   • Cân bằng độ đa dạng theo từng cuốn sách            │
                     └───────────────────────────┬────────────────────────────┘
                                                 │ (Top-K Chunks được chọn)
                                                 ▼
                     ┌────────────────────────────────────────────────────────┐
                     │         ĐIỀU PHỐI HỘI THOẠI & PHÒNG VỆ NGỮ CẢNH        │
                     │   • Khử tấn công Jailbreak / Prompt Injection          │
                     │   • Kiểm tra an toàn y tế (Crisis / Diagnosis Guard)   │
                     │   • Tính toán Context Budget (Tối đa 8192 UTF-8 bytes) │
                     │   • Dịch thuật song ngữ trích đoạn En-Vi nếu cần       │
                     └───────────────────────────┬────────────────────────────┘
                                                 │
                                                 ▼
                     ┌────────────────────────────────────────────────────────┐
                     │            SUY LUẬN MÔ HÌNH NGÔN NGỮ (LLM)             │
                     │       • Ollama Qwen2.5-3B hoặc MLX Local Engine        │
                     │       • Ép buộc gắn thẻ nguồn [S#] sau mỗi ý           │
                     └───────────────────────────┬────────────────────────────┘
                                                 │
                                                 ▼
                     ┌────────────────────────────────────────────────────────┐
                     │         HẬU XỬ LÝ & BẢO CHỨNG NGUỒN (SOURCE ATTRIB)    │
                     │   • Lọc bỏ thẻ suy nghĩ <think>, <reasoning>           │
                     │   • Đối chiếu mã [S#] trong câu trả lời với trích đoạn │
                     │   • Từ chối trả lời nếu thiếu nguồn hoặc sai nguồn     │
                     │   • Trả về Stream SSE kèm siêu dữ liệu trích dẫn       │
                     └────────────────────────────────────────────────────────┘
```

### 2.3. Quy trình Người dùng (End-to-End User Journeys)

#### Luồng 1: Người dùng Tra cứu Tài liệu
1. Người dùng mở tab **🧰 Công cụ học tập** -> **Tạo câu hỏi từ tài liệu** (nơi tích hợp giao diện tìm kiếm tài liệu).
2. Nhập từ khóa truy vấn (ví dụ: `ánh xạ tuyến tính`, `hệ thống 1`).
3. Chọn phạm vi: Tất cả tài liệu hoặc một tài liệu cụ thể; chọn phương thức: *Từ khóa (FTS)* hoặc *Ngữ nghĩa và từ khóa (Hybrid)*.
4. Hệ thống thực thi truy vấn chỉ mục read-only, trả về danh sách các đoạn trích cùng số trang, tên sách, điểm tương đồng.
5. Người dùng có thể:
   - Nhấp **Xem PDF trang X** để mở trực tiếp tài liệu tại trang đó.
   - Nhấp **Xem ảnh trang gốc** để kiểm tra bản scan/ảnh chụp nguyên bản không qua biên tập.
   - Nhấp **Chọn đoạn này để hỏi đáp / luyện tập** để khóa phạm vi nguồn cho các lượt thao tác tiếp theo.

#### Luồng 2: Người dùng Hỏi đáp Học thuật (QA)
1. Người dùng nhập câu hỏi vào ô chat tại tab **💬 Hỏi đáp dựa trên tài liệu**.
2. Hệ thống kiểm tra an toàn:
   - Nếu phát hiện dấu hiệu tự sát/tự hại -> Lập tức hiển thị thông điệp khẩn cấp và số điện thoại cấp cứu 115.
   - Nếu phát hiện yêu cầu chẩn đoán bệnh tật/kê đơn -> Từ chối lịch sự và khuyến cáo đến cơ sở y tế.
   - Nếu là lời chào hỏi xã giao -> Trả lời ngắn tự nhiên mà không tốn chi phí tìm kiếm RAG.
3. Hệ thống chuẩn hóa câu hỏi (sửa lỗi chính tả tiếng Việt), thực hiện Hybrid Retrieval tìm Top-K đoạn trích liên quan nhất.
4. Đóng gói Prompt an toàn vào thẻ `<context>` với ngân sách ký tự được tính toán chặt chẽ.
5. Mô hình LLM sinh câu trả lời theo thời gian thực (Server-Sent Events - SSE streaming).
6. Khi hoàn tất, hệ thống đối soát các mã trích dẫn `[S1]`, `[S2]`. Nếu câu trả lời không có căn cứ, hệ thống tự động thay thế bằng thông báo an toàn: *"Tôi chưa có đủ thông tin đáng tin cậy để trả lời chắc chắn..."*.
7. Lượt hỏi đáp hoàn chỉnh được ghi nhận vào phiên làm việc (`history.db`) và hiển thị thanh trích dẫn bên dưới tin nhắn.

#### Luồng 3: Người dùng Lập Thời khóa biểu từ Ảnh
1. Người dùng chuyển sang tab **📅 Thời khóa biểu từ ảnh**.
2. Kéo thả file ảnh chụp thời khóa biểu (PNG/JPEG/WebP) vào dropzone.
3. Hệ thống kiểm tra tính hợp lệ của file (dung lượng dưới 15MB, kích thước an toàn chống decompression bomb).
4. Hệ thống ưu tiên chạy phân tích bảng đăng ký môn học cục bộ (Literal Table OCR), nếu không khớp sẽ chuyển sang gọi mô hình Vision VLM (`qwen2.5vl:3b`) qua Ollama dưới sự bảo vệ của khóa GPU.
5. Kết quả trích xuất được hiển thị dưới dạng **Bản nháp (Draft Table)** có thể chỉnh sửa:
   - Tên môn học, thứ trong tuần, giờ bắt đầu, giờ kết thúc, phòng học, tiết học.
   - Các cảnh báo về ô chữ mờ, tiết học chưa có giờ cụ thể hoặc các tiết học bị xung đột/trùng giờ.
6. Người dùng kiểm tra, chỉnh sửa trực tiếp trên bảng nháp, có thể áp dụng công cụ quy đổi tiết học sang giờ đồng hồ.
7. Nhấp **💾 Xác nhận & Lưu vào lịch học** (có tùy chọn ghi đè toàn bộ hoặc ghép thêm môn).
8. Nhập ngày bắt đầu và kết thúc học kỳ, nhấp **📥 Tải tệp .ics** để nhập vào Google Calendar hoặc Apple Calendar.

---

## 3. CHỨC NĂNG CHÍNH VÀ HIỆN THỰC HÓA

### 3.1. Bảng Tổng hợp Trạng thái Triển khai Thực tế

| Tên chức năng | Mô tả cốt lõi | Các module / File chính | Trạng thái thực tế từ Code |
| :--- | :--- | :--- | :--- |
| **Tra cứu tài liệu (Document Lookup)** | Tìm kiếm Full-Text FTS5 kết hợp Vector Embedding BGE-M3 qua RRF; mở PDF theo trang; xem ảnh trang gốc. | `app/document_lookup.py`<br>`app/searcher.py`<br>`app/indexer.py`<br>`static/document-lookup.js` | **Đã hoàn thiện & Đạt kiểm thử** (100% hoạt động cục bộ) |
| **Hỏi đáp có nguồn (Academic QA)** | RAG hội thoại đa lượt, streaming token SSE, quản lý ngân sách UTF-8, đối chiếu citation `[S#]`, an toàn y tế/khủng hoảng. | `app/rag_agent.py`<br>`app/dialogue.py`<br>`app/safety.py`<br>`app/server.py`<br>`static/app.js` | **Đã hoàn thiện & Đạt kiểm thử** (Hỗ trợ Ollama và MLX) |
| **Quản lý Phiên & Tóm tắt (Sessions & Summarization)** | Quản lý phiên hội thoại có ID, tự sinh tiêu đề thông minh không tốn GPU, tóm tắt chủ đề phiên bằng LLM, bảo vệ tiêu đề người dùng đặt. | `app/history.py`<br>`app/topic_summarizer.py`<br>`app/server.py` | **Đã hoàn thiện & Đạt kiểm thử** (Lưu trữ SQLite `history.db`) |
| **Luyện tập bám sát nguồn (Practice Service)** | Sinh 1-3 câu hỏi trắc nghiệm từ trang sách được chọn; kiểm định đáp án 2 bước; lưu câu sai/chưa chắc vào localStorage để ôn lại. | `app/practice.py`<br>`app/server.py`<br>`static/practice.js` | **Đã hoàn thiện & Đạt kiểm thử** (Tích hợp trong tab Công cụ học tập) |
| **Trích xuất bài tập mẫu (Example Exercises)** | Quét và lọc nguyên văn các bài tập có sẵn trong sách (bài tập, ví dụ, câu hỏi ôn tập) theo trang/chủ đề mà không sửa nội dung. | `app/practice.py`<br>`static/practice.js` | **Đã hoàn thiện & Đạt kiểm thử** |
| **Thời khóa biểu từ ảnh (Vision Timetable)** | Đọc ảnh lịch học qua VLM/Literal OCR, sinh bản nháp editable, phát hiện trùng lịch, xuất chuẩn RFC 5545 iCalendar (`.ics`). | `app/timetable_vision.py`<br>`app/timetable_store.py`<br>`app/timetable_table.py`<br>`app/timetable_ics.py` | **Đã hoàn thiện & Đạt kiểm thử** (Bảo vệ GPU, lưu `timetable.db`) |
| **Thẩm định OCR cục bộ (OCR Review Workflow)** | Giao diện soát lỗi và xác nhận văn bản OCR từng trang; cập nhật lại chunks/FTS sau khi duyệt; chặn đưa OCR chưa duyệt vào training. | `app/vision_ocr.py`<br>`app/server.py`<br>`static/index.html` | **Đã hoàn thiện & Đạt kiểm thử** |
| **Phối hợp khóa GPU & Khóa File** | Phân định tài nguyên tránh OOM trên máy 16GB RAM; khóa file tương thích đa nền tảng (`LockFileEx` trên Win, `flock` trên POSIX). | `app/gpu_lock.py`<br>`app/file_lock.py`<br>`app/dialogue.py` | **Đã hoàn thiện & Đạt kiểm thử** |
| **Huấn luyện mô hình MLX LoRA (Training Pipeline)** | Fine-tune Qwen2.5-3B bằng MLX trên Apple Silicon macOS; sổ theo dõi run ledger; cổng kiểm duyệt dataset chặt chẽ. | `app/fine_tune.py`<br>`app/run_ledger.py`<br>`app/curate_dataset_v7.py` | **Đã triển khai cho Mac (TV4)**; Windows bị chặn có chủ đích. |

---

### 3.2. Chi tiết Từng Chức năng Nghiệp vụ

#### Chức năng 1: Tra cứu Tài liệu Đa phương thức (Document Lookup)
- **Mục đích:** Cung cấp khả năng tìm kiếm chính xác các đoạn kiến thức trong thư viện giáo trình mà không cần phải mở từng file PDF hay lật từng trang sách.
- **Cách sử dụng:** Truy cập tab *Công cụ học tập* -> *Tạo câu hỏi từ tài liệu*, nhập từ khóa vào ô tìm kiếm, chọn bộ lọc sách và phương thức tìm kiếm, xem kết quả và nhấp liên kết PDF/ảnh.
- **Đầu vào:** Chuỗi truy vấn văn bản (`q`), giới hạn số lượng (`limit`), mã tài liệu (`document_id`), phương thức tìm kiếm (`fts` hoặc `hybrid`).
- **Đầu ra:** Danh sách các đoạn trích JSON chứa: `chunk_id`, `doc_id`, `book_title`, `filename`, `page_num`, `chunk_index`, `text`, `pdf_url`, `page_image_url`, `fts_score` / `hybrid_score`.
- **Quy trình xử lý bên trong:**
  1. Hàm `DocumentLookup.search()` tại `app/document_lookup.py` tiếp nhận truy vấn.
  2. Thực hiện làm sạch truy vấn bằng `HybridSearcher._clean_fts_query()`, loại bỏ các ký tự đặc biệt gây lỗi cú pháp SQLite FTS5.
  3. Nếu chọn `fts`: Chạy câu lệnh SQL truy vấn bảng ảo `chunks_fts` sử dụng hàm tính điểm `bm25(chunks_fts)`.
  4. Nếu chọn `hybrid`:
     - Kiểm tra và chiếm khóa GPU (`gpu_coordinator.acquire_for_inference()`).
     - Gọi Ollama tạo vector embedding cho câu truy vấn thông qua mô hình `bge-m3`.
     - Tính khoảng cách Cosine giữa vector truy vấn và toàn bộ vector của tài liệu được giải nén qua `unpack_vector()`.
     - Lọc các đoạn có điểm tương đồng trên ngưỡng tối thiểu `0.15`.
  5. Hợp nhất hai danh sách xếp hạng bằng công thức Reciprocal Rank Fusion:
     $$\text{RRF\_Score} = \sum \frac{1}{60 + \text{Rank}}$$
  6. Khử trùng lặp văn bản bằng cách chuẩn hóa khoảng trắng và chữ thường (`casefold()`).
  7. Sinh đường dẫn xem PDF trực tiếp (`/api/documents/{doc_id}/pdf#page={page_num}`) và ảnh trang gốc (`/api/documents/{doc_id}/pages/{page_num}/image`).
- **Các hàm/class liên quan:**
  - Class `DocumentLookup` (`app/document_lookup.py:17`): Các phương thức `documents()`, `document()`, `search()`, `page_image()`, `source_preview()`.
  - Class `HybridSearcher` (`app/searcher.py:61`): Phương thức `_clean_fts_query()`, `search_fts()`, `search_semantic()`, `search_hybrid()`.
  - API Endpoints: `GET /api/documents`, `GET /api/documents/search`, `GET /api/documents/{document_id}/pdf`, `GET /api/documents/{document_id}/pages/{page_num}/image`.

#### Chức năng 2: Hỏi đáp Dẫn nguồn Học thuật (Academic Grounded QA)
- **Mục đích:** Trả lời các thắc mắc học tập của người dùng bằng cách tổng hợp thông tin từ nhiều trang sách khác nhau, đảm bảo mỗi câu trả lời đều có trích dẫn xác thực.
- **Cách sử dụng:** Nhập câu hỏi vào khung chat chính, theo dõi câu trả lời hiển thị dạng gõ chữ (streaming), nhấp vào các huy hiệu trích dẫn `[S1]`, `[S2]` ở chân câu trả lời để đối chiếu trang sách nguồn.
- **Đầu vào:** `ChatRequest` (Pydantic model) chứa: `query`, `chat_history`, `session_id`, `model`, `embed_model`, `top_k`, `temperature`, `source_document_id`, `source_page_num`, `request_id`.
- **Đầu ra:** Dòng sự kiện Server-Sent Events (SSE) gồm các loại event: `token`, `citations`, `retrieval_trace`, `context`, `done`, `error`, `crisis`.
- **Quy trình xử lý bên trong:**
  1. Kiểm tra an toàn khẩn cấp qua `SafetyGuard.check_crisis()` và `SafetyGuard.check_roleplay_or_diagnosis()`.
  2. Phân tích ý định qua `dialogue_intent()`: Nếu là chào hỏi hoặc cảm ơn -> Trả lời trực tiếp ngay lập tức mà không tìm kiếm RAG.
  3. Chuẩn hóa câu hỏi tiếng Việt qua `normalize_query()`.
  4. Truy xuất tài liệu:
     - Nếu người dùng đã chọn trước trang nguồn (`source_page`): Lấy trực tiếp các chunk của trang đó qua `HybridSearcher.source_page_chunks()`.
     - Nếu là câu hỏi tổng quan đa chương (`is_broad_query()`): Sinh các khía cạnh truy vấn phụ qua `extract_query_facets()` và gộp kết quả.
     - Trường hợp thông thường: Gọi `HybridSearcher.search_hybrid()`.
  5. Kiểm tra bằng chứng liên quan qua `has_relevant_evidence()`: Nếu không tìm thấy bằng chứng thỏa đáng -> Trả lời từ chối và gợi ý người dùng làm rõ câu hỏi.
  6. Dịch ngữ cảnh song ngữ qua `LocalTranslator.translate()` nếu trích đoạn là tiếng Anh.
  7. Phân bổ ngân sách ngữ cảnh (Context Budget) qua `build_context()`: Tính toán giới hạn UTF-8 bytes bảo đảm không vượt quá cửa sổ ngữ cảnh 8192 bytes của mô hình, bảo lưu 640 tokens cho đầu ra.
  8. Chiếm giữ đồng thời cổng hội thoại (`dialogue_gate.acquire()`) và khóa GPU (`gpu_coordinator.acquire_for_inference()`).
  9. Gọi mô hình (Ollama hoặc MLX) sinh token streaming.
  10. Hậu xử lý câu trả lời:
      - Loại bỏ các khối `<think>`, `<reasoning>`, `<final>` qua `clean_answer()`.
      - Kiểm tra lặp từ ngữ (`has_repetition()`) hoặc lệch ngôn ngữ (`has_language_drift()`).
      - Quét toàn bộ mã `[S#]` trong văn bản và đối chiếu với danh mục nguồn thực tế. Nếu phát hiện mô hình tự bịa mã `[S#]` không có trong context -> Chuyển thành câu trả lời từ chối an toàn.
  11. Lưu trữ turn vào phiên hội thoại trong SQLite `history.db` thông qua `HistoryStore.add_turn()` và kích hoạt kiểm tra idempotency qua `request_id`.
- **Các hàm/class liên quan:**
  - Class `PsychologyAgent` (`app/rag_agent.py:141`): Phương thức `process_query_stream()`, `process_query_sync()`.
  - Module `dialogue` (`app/dialogue.py`): Class `DialogueGate`, hàm `dialogue_intent()`, `build_context()`.
  - Class `SafetyGuard` (`app/safety.py:21`).
  - API Endpoints: `POST /api/chat`, `POST /api/chat/stream`.

#### Chức năng 3: Công cụ Học tập Chủ động (Practice & Learning Tools)
- **Mục đích:** Giúp sinh viên chuyển từ đọc thụ động sang kiểm tra kiến thức chủ động (Active Recall) thông qua câu hỏi trắc nghiệm tự động sinh từ tài liệu học tập.
- **Cách sử dụng:**
  - *Tab 1 (Tạo câu hỏi):* Chọn một trang sách từ phần Tra cứu hoặc Hỏi đáp, nhấn nút **📝 Tạo câu hỏi từ nội dung này**. Làm bài trắc nghiệm, chọn đáp án và xem lời giải thích chi tiết có trích dẫn nguyên văn.
  - *Tab 2 (Ôn tập):* Xem lại các câu trả lời sai hoặc các câu người dùng đánh dấu "Chưa chắc", làm lại bài và xóa tiến độ khi đã thuộc.
  - *Tab 3 (Trích xuất bài tập mẫu):* Chọn giáo trình và khoảng trang (ví dụ trang 10 đến 50) để lọc ra toàn bộ các bài tập thực hành nguyên bản có trong sách.
- **Đầu vào:** `PracticeGenerateRequest` (chứa `source_document_id`, `source_page_num`, `count`, `model`), `PracticeAnswerRequest` (chứa `practice_id`, `question_id`, `answer`).
- **Đầu ra:** Bộ câu hỏi trắc nghiệm JSON (câu hỏi, 4 đáp án A/B/C/D, ID đoạn trích dẫn, trích dẫn nguyên văn bằng chứng) và kết quả chấm điểm tức thì.
- **Quy trình xử lý bên trong:**
  1. `PracticeService.generate()` tại `app/practice.py` lấy nội dung các đoạn văn bản của trang sách được chọn.
  2. Gửi prompt yêu cầu mô hình sinh tối đa 3 câu hỏi trắc nghiệm với quy định nghiêm ngặt: Mỗi câu phải có một trích dẫn bằng chứng nguyên văn (`evidence_quote`) dài tối thiểu 20 ký tự từ đoạn nguồn.
  3. Bước kiểm định thứ hai (`_verify_questions()`): Hệ thống đối chiếu chuỗi `evidence_quote` xem có thực sự tồn tại từng chữ trong đoạn văn bản nguồn hay không; nếu không khớp, câu hỏi bị hủy bỏ ngay lập tức.
  4. Lưu trữ phiên luyện tập trong bộ nhớ đệm an toàn (`OrderedDict` giới hạn 50 phiên, thời gian sống TTL 60 phút). Giữ kín đáp án tại máy chủ, không trả về trình duyệt trước khi người dùng nộp bài.
  5. Khi người dùng gửi câu trả lời qua `/api/practice/answer`, hệ thống so khớp đáp án, trả về kết quả đúng/sai kèm lời giải thích chi tiết.
  6. Tại frontend, nếu người học chọn sai hoặc chọn "Chưa chắc", câu hỏi được lưu cục bộ vào `localStorage` của trình duyệt dưới khóa `study-agent-review-v1`.
- **Các hàm/class liên quan:**
  - Class `PracticeService` (`app/practice.py:26`): Phương thức `generate()`, `answer()`, `list_example_exercises()`.
  - Frontend: `static/practice.js`.
  - API Endpoints: `POST /api/practice/generate`, `POST /api/practice/answer`, `GET /api/practice/examples`.

#### Chức năng 4: Số hóa Thời khóa biểu từ Ảnh (Vision Timetable)
- **Mục đích:** Chuyển đổi nhanh chóng hình ảnh thời khóa biểu học tập phức tạp thành dữ liệu lịch có cấu trúc và đồng bộ vào ứng dụng lịch của điện thoại/máy tính.
- **Cách sử dụng:** Tải ảnh lên giao diện, chờ hệ thống trích xuất bản nháp, rà soát lại thông tin trên bảng, bổ sung giờ cho các tiết học còn thiếu, kiểm tra xung đột và xuất file `.ics`.
- **Đầu vào:** `TimetableExtractRequest` (chứa chuỗi base64 của ảnh và tên file), `TimetableConfirmRequest` (chứa danh sách các môn học đã xác nhận).
- **Đầu ra:** Bản nháp trích xuất (Draft ID, danh sách môn, danh sách cảnh báo), danh sách lịch học chính thức đã lưu và file lịch tải về `timetable_export.ics`.
- **Quy trình xử lý bên trong:**
  1. Xác thực an toàn ảnh qua `validate_image_payload()`: Kiểm tra dung lượng (tối đa 15MB), kiểm tra magic bytes (PNG, JPEG, WebP), giải nén an toàn qua Pillow chống tấn công decompression bomb.
  2. Tính toán mã băm SHA-256 của ảnh và lưu trữ file ảnh vào thư mục riêng `data/timetable_images/{image_hash}.png` (tách biệt hoàn toàn khỏi thư mục tri thức RAG).
  3. Kiểm tra trích xuất bảng chữ in đại học qua `timetable_table.extract_registered_table()`: Nhận diện tọa độ các cột Lý thuyết (LT), Thực hành (TH), mã môn học và khung giờ.
  4. Nếu không phải bảng đăng ký môn học chuẩn, kích hoạt mô hình Vision VLM (`qwen2.5vl:3b`) qua Ollama dưới sự kiểm soát của `gpu_coordinator`.
  5. Xử lý phản hồi JSON, chuẩn hóa thứ trong tuần về định dạng chuẩn ISO (1 = Thứ Hai ... 7 = Chủ Nhật) qua `normalize_weekday()`, chuẩn hóa giờ đồng hồ HH:MM qua `format_clock_time()`.
  6. Kiểm tra phát hiện xung đột lịch học trùng giờ (`detect_conflicts()`).
  7. Ghi nhận bản nháp vào bảng `timetable_drafts` trong `timetable.db`.
  8. Sau khi người dùng chỉnh sửa và xác nhận (`/api/timetable/confirm`):
     - Mở transaction khóa ghi `BEGIN IMMEDIATE` trong SQLite.
     - Xác thực lại toàn bộ giá trị qua `validate_entry_values()`.
     - Kiểm tra xung đột chéo giữa các môn trong đợt lưu và các môn đã lưu từ trước.
     - Lưu trữ vào bảng `timetable_confirmed`.
  9. Khi xuất lịch (`/api/timetable/export.ics`):
     - Gọi `timetable_ics.generate_ics()` tạo nội dung chuẩn RFC 5545.
     - Cấu hình khối `VTIMEZONE` định danh `Asia/Ho_Chi_Minh` (+07:00).
     - Tạo sự kiện lặp hàng tuần `RRULE:FREQ=WEEKLY;BYDAY=...;UNTIL=...`.
     - Thực hiện escape ký tự đặc biệt và bẻ dòng (line folding) chuẩn 75 octets UTF-8.
- **Các hàm/class liên quan:**
  - Module `timetable_vision` (`app/timetable_vision.py`): Các hàm `call_vlm_extract()`, `validate_image_payload()`, `normalize_weekday()`, `detect_conflicts()`.
  - Module `timetable_store` (`app/timetable_store.py`): Các hàm `save_draft()`, `confirm_draft()`, `add_manual_entry()`, `get_confirmed_entries()`.
  - Module `timetable_ics` (`app/timetable_ics.py`): Hàm `generate_ics()`, `_fold_line()`, `_escape_text()`.
  - Module `timetable_table` (`app/timetable_table.py`): Hàm `extract_registered_table()`, `parse_registered_table()`.
  - API Endpoints: `POST /api/timetable/extract`, `POST /api/timetable/confirm`, `GET /api/timetable`, `POST /api/timetable/manual`, `DELETE /api/timetable/entries/{id}`, `GET /api/timetable/export.ics`.

---

## 4. CÔNG NGHỆ SỬ DỤNG VÀ CĂN CỨ KIẾN TRÚC

Bảng tổng hợp chi tiết toàn bộ các công nghệ, thư viện, mô hình và căn cứ sử dụng trong mã nguồn:

| Nhóm công nghệ | Tên công nghệ / Phiên bản | Vai trò trong hệ thống | Lý do kiến trúc & Lợi ích kỹ thuật | File mã nguồn thể hiện |
| :--- | :--- | :--- | :--- | :--- |
| **Ngôn ngữ nền tảng** | **Python 3.12** | Môi trường runtime chính cho Web API, RAG, Trích xuất tài liệu và Kiểm thử trên Windows & Mac. | Phiên bản ổn định cao, tương thích tốt với FastAPI, PyMuPDF và hỗ trợ UTF-8 native trên Windows qua biến `PYTHONUTF8=1`. | `runtime.txt`, `setup_windows.ps1`, `requirements.txt` |
| **Ngôn ngữ huấn luyện** | **Python 3.13** (riêng biệt trong `.train-venv`) | Môi trường huấn luyện MLX LoRA độc quyền trên macOS Apple Silicon. | Framework MLX tối ưu hóa tốt nhất trên Python 3.13 cho kiến trúc ARM64 của Apple Silicon. Tách biệt môi trường để không gây xung đột dependency với web server. | `requirements-mlx.txt`, `constraints-mlx-py313.txt` |
| **Web Framework** | **FastAPI** (`>=0.110.1, <1`) | Xây dựng RESTful API backend, xử lý streaming Server-Sent Events (SSE), định tuyến bất đồng bộ. | Hiệu năng cao dựa trên Starlette và Pydantic, hỗ trợ AsyncIO native, tự động sinh tài liệu Swagger UI tại `/docs`. | `app/server.py` |
| **Data Validation** | **Pydantic v2** (`>=2, <3`) | Định nghĩa schema, kiểm thực dữ liệu đầu vào (request validation) và serialize dữ liệu đầu ra. | Tốc độ thực thi C-Rust cực nhanh, hỗ trợ các decorator `@field_validator` và `@model_validator` kiểm tra tính hợp lệ của giờ học, câu hỏi. | `app/server.py` |
| **ASGI Server** | **Uvicorn** (`>=0.28, <1`) | Máy chủ web HTTP/1.1 và WebSocket bất đồng bộ phục vụ ứng dụng FastAPI. | Nhẹ, hiệu năng cao, tích hợp hoàn hảo với hệ sinh thái ASGI của Python. | `run.py`, `scripts/dev.py` |
| **Cơ sở dữ liệu** | **SQLite3** (với module **FTS5**) | Lưu trữ tri thức tài liệu (chunks, metadata, vector blob), lịch sử hội thoại (`history.db`) và thời khóa biểu (`timetable.db`). | Cài đặt sẵn trong Python standard library, không cần cài đặt dịch vụ database server phức tạp. Module FTS5 cung cấp thuật toán BM25 tìm kiếm toàn văn bản xuất sắc. | `app/indexer.py`<br>`app/history.py`<br>`app/timetable_store.py` |
| **Mô hình Ngôn ngữ (LLM)** | **Qwen2.5-3B-Instruct** (`qwen2.5:3b`) | Suy luận hỏi đáp học thuật, tóm tắt chủ đề hội thoại và sinh câu hỏi trắc nghiệm luyện tập. | Kích thước nhỏ gọn (3 tỷ tham số), footprint VRAM chỉ ~2.5GB khi lượng tử hóa 4-bit, khả năng hiểu và diễn đạt tiếng Việt cực kỳ vượt trội so với các mô hình cùng kích thước. | `app/config.py`<br>`requirements-windows-tools.json` |
| **Mô hình Embedding** | **BGE-M3** (`bge-m3`) | Mô hình biểu diễn vector ngữ nghĩa đa ngôn ngữ (1024 chiều). | Hỗ trợ hơn 100 ngôn ngữ, tối ưu đặc biệt cho tiếng Việt và tiếng Anh, hỗ trợ độ dài ngữ cảnh lên tới 8192 tokens. | `app/config.py`<br>`app/indexer.py` |
| **Mô hình Thị giác (VLM)** | **Qwen2.5-VL-3B** (`qwen2.5vl:3b`) | Đọc hiểu hình ảnh thời khóa biểu và trích xuất chữ viết tay/scan phức tạp. | Khả năng đọc bảng biểu, nhận diện bố cục dòng cột và hiểu nhãn ngày giờ tiếng Việt xuất sắc ở kích thước 3B. | `app/timetable_vision.py`<br>`app/vision_ocr.py` |
| **Trình quản lý Model Cục bộ** | **Ollama** | Runtime phục vụ suy luận LLM, VLM và Embedding trên máy trạm Windows & Mac. | Cài đặt cực kỳ đơn giản qua WinGet, quản lý tải mô hình tự động, cung cấp REST API chuẩn hóa (`/api/generate`, `/api/embeddings`, `/api/ps`). | `app/ollama_client.py`<br>`scripts/windows_setup.ps1` |
| **Framework Huấn luyện** | **Apple MLX / MLX-LM** | Thư viện tính toán học máy tối ưu riêng cho Apple Silicon Unified Memory. | Tận dụng bộ nhớ thống nhất (Unified Memory) của chip Apple M-series, huấn luyện LoRA trực tiếp trên Mac với tốc độ cao và mức tiêu thụ điện năng tối thiểu. | `app/fine_tune.py`<br>`app/mlx_infer.py` |
| **Xử lý PDF & Tài liệu** | **PyMuPDF (fitz)** (`>=1.24.3, <2`) | Trích xuất văn bản từ PDF, phát hiện trang scan dạng ảnh, render trực tiếp ảnh trang PDF sang PNG. | Tốc độ trích xuất nhanh gấp hàng chục lần so với PyPDF2 hay pdfplumber; khả năng render trang PDF độ phân giải cao phục vụ soát lỗi. | `app/pdf_extractor.py`<br>`app/document_lookup.py` |
| **Xử lý Hình ảnh** | **Pillow (PIL)** (`>=10, <13`) | Kiểm tra kích thước, xoay ảnh theo EXIF, chuẩn hóa RGB, chuyển đổi base64 và phòng chống Decompression Bomb. | Thư viện xử lý ảnh chuẩn mực, an toàn và tối ưu của Python. | `app/timetable_vision.py`<br>`app/pdf_extractor.py` |
| **Tính toán Ma trận** | **NumPy** (`>=1.26, <3`) | Tính toán đại số tuyến tính, chuẩn hóa vector và tính độ tương đồng Cosine giữa các embedding vector. | Cung cấp các thao tác mảng n-chiều tốc độ cao bằng mã máy C. | `app/searcher.py`<br>`app/indexer.py` |
| **Khóa File Đa nền tảng** | **Windows LockFileEx / Unix fcntl** | Đảm bảo tính độc quyền khi truy cập tài nguyên phần cứng GPU và cơ sở dữ liệu. | Trên Windows: dùng `LockFileEx` qua ctypes để hỗ trợ shared/exclusive lock; trên Unix/macOS: dùng `fcntl.flock`. | `app/file_lock.py`<br>`app/gpu_lock.py` |
| **Frontend** | **HTML5 + Vanilla JavaScript + CSS3** | Xây dựng giao diện người dùng đơn trang (Single Page Application - SPA). | Không phụ thuộc vào các framework nặng nề (React/Vue/Angular), không cần bước build webpack/vite phức tạp, tốc độ tải trang tức thì. | `static/index.html`<br>`static/app.js`<br>`static/style.css` |
| **Kiểm thử Tự động** | **Pytest + Node Test Runner** | Kiểm tra hồi quy, kiểm tra hợp đồng API, kiểm tra UI DOM. | Pytest cho toàn bộ mã backend Python; Node.js test runner (`node --test`) kiểm tra tính toàn vẹn của logic JavaScript giao diện. | `tests/`<br>`pytest.windows.ini` |

---

## 5. KIẾN TRÚC VÀ QUY TRÌNH NGHIỆP VỤ TỔNG QUÁT

### 5.1. Phân tầng Kiến trúc (Layered Architecture)
Hệ thống được tổ chức theo mô hình phân tầng chặt chẽ nhằm đảm bảo tính độc lập, dễ bảo trì và dễ mở rộng:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       TẦNG TRÌNH DIỄN (PRESENTATION LAYER)                  │
│   • static/index.html: Giao diện người dùng đơn trang                       │
│   • static/app.js: Điều phối hội thoại, streaming SSE, quản lý sessions     │
│   • static/document-lookup.js: Giao diện tra cứu và xem trước tài liệu      │
│   • static/timetable.js: Kéo thả ảnh, bảng nháp editor, xuất file .ics     │
│   • static/practice.js: Trắc nghiệm luyện tập, lưu tiến độ localStorage    │
│   • static/layout.js & theme.js: Responsive sidebar, chuyển Dark/Light mode │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ HTTP / REST / Server-Sent Events
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          TẦNG GIAO DIỆN API (API ROUTING LAYER)             │
│   • app/server.py (FastAPI App):                                            │
│     - /api/chat & /api/chat/stream: Endpoint hỏi đáp RAG                    │
│     - /api/documents & /api/documents/search: Endpoint tra cứu tài liệu     │
│     - /api/practice/*: Endpoint tạo và chấm câu hỏi luyện tập               │
│     - /api/timetable/*: Endpoint phân tích ảnh, xác nhận và xuất lịch .ics  │
│     - /api/sessions/* & /api/history/*: Endpoint quản lý phiên hội thoại    │
│     - /api/ocr/*: Endpoint thẩm định và chỉnh sửa bản OCR trang sách        │
│     - /api/health & /api/status: Kiểm tra trạng thái dịch vụ và tài nguyên  │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Threadpool / Service Invocations
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     TẦNG NGHIỆP VỤ CỐT LÕI (CORE BUSINESS LOGIC)            │
│   • app/rag_agent.py (PsychologyAgent): Điều phối luồng RAG và trích dẫn    │
│   • app/document_lookup.py (DocumentLookup): Tra cứu tài liệu độc lập       │
│   • app/searcher.py (HybridSearcher): Tìm kiếm lai FTS5 BM25 + Vector RRF   │
│   • app/indexer.py (KnowledgeIndexer): Quét, băm SHA256 và lập chỉ mục PDF  │
│   • app/practice.py (PracticeService): Sinh và thẩm định trắc nghiệm 2 bước │
│   • app/timetable_vision.py & timetable_table.py: Xử lý thị giác thời khóa biểu│
│   • app/topic_summarizer.py: Tóm tắt phiên và sinh tiêu đề hội thoại        │
│   • app/safety.py: Giám sát nguy cơ tự hại và từ chối chẩn đoán y tế        │
│   • app/dialogue.py: Định tuyến ý định, quản lý ngân sách UTF-8 bytes       │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Cổng kiểm soát tài nguyên & Đồng bộ
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TẦNG ĐIỀU PHỐI TÀI NGUYÊN & MÔ HÌNH (INFRASTRUCTURE)     │
│   • app/gpu_lock.py (GPULockManager): Độc quyền GPU giữa training & suy luận│
│   • app/file_lock.py: Khóa file đa nền tảng (LockFileEx Win / flock POSIX)  │
│   • app/ollama_client.py: Kết nối Ollama (qwen2.5:3b, bge-m3, qwen2.5vl:3b) │
│   • app/trained_client.py: Kết nối mô hình MLX nền tảng trên macOS          │
│   • app/vision_ocr.py: Quản lý các backend OCR (Tesseract / Ollama VLM)     │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Đọc / Ghi tệp cục bộ
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        TẦNG DỮ LIỆU & LƯU TRỮ (DATA PERSISTENCE)            │
│   • data/knowledge_base.db: SQLite FTS5 chunks, metadata tài liệu, vectors  │
│   • data/history.db: SQLite sessions, session_turns, legacy searches        │
│   • data/timetable.db: SQLite drafts, confirmed entries, VLM cache          │
│   • data/timetable_images/: Thư mục lưu ảnh lịch gốc theo SHA-256           │
│   • data/ocr_cache/: Thư mục cache kết quả OCR và bản thẩm định nhân sự     │
│   • src/ (hoặc tests/fixtures/documents): Thư mục chứa tài liệu nguồn       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2. Mối liên hệ và Tương tác giữa các Module
1. **Sự kết hợp giữa `indexer.py` và `searcher.py`:**
   - `KnowledgeIndexer` chịu trách nhiệm quét thư mục `src/`, sử dụng `PDFExtractor` để trích xuất văn bản và `TextChunker` để băm nhỏ thành các đoạn 1200 ký tự. Dữ liệu được ghi đồng thời vào bảng `documents`, bảng `chunks` và bảng ảo `chunks_fts` (qua triggers SQLite). Nếu có sẵn mô hình embedding, vector sẽ được sinh và đóng gói nhị phân (`pack_vector`) vào cột `embedding`.
   - `HybridSearcher` sử dụng chung cơ sở dữ liệu `knowledge_base.db` nhưng mở ở chế độ read-only, kết hợp điểm số BM25 từ `chunks_fts` và độ tương đồng Cosine từ cột `embedding` để cung cấp hàm tìm kiếm `search_hybrid()` cho cả `rag_agent.py`, `document_lookup.py` và `practice.py`.
2. **Sự kết hợp giữa `server.py`, `dialogue.py` và `gpu_lock.py`:**
   - Khi có request gửi tới `/api/chat` hoặc `/api/chat/stream`, `server.py` gọi `dialogue_gate.acquire()`. Khóa này đảm bảo mỗi thời điểm chỉ có duy nhất một request suy luận được nạp ngữ cảnh và ghi nhận lịch sử vào `history.db`.
   - Tiếp theo, luồng suy luận yêu cầu quyền chia sẻ từ `gpu_coordinator.acquire_for_inference()`. Nếu hệ thống đang trong tiến trình huấn luyện MLX LoRA (nắm giữ exclusive lock), yêu cầu suy luận sẽ bị từ chối an toàn với mã lỗi HTTP 503 và thông báo rõ ràng cho người dùng.
3. **Sự phân tách giữa Dữ liệu Tri thức và Dữ liệu Cá nhân:**
   - Tri thức học thuật nằm trong `knowledge_base.db` và có thể tái tạo hoàn toàn từ thư mục `src/`.
   - Thông tin cá nhân của người học nằm ở hai cơ sở dữ liệu độc lập: `history.db` (lịch sử hỏi đáp) và `timetable.db` (ảnh và lịch học). Các dữ liệu này được cấu hình loại trừ (`.gitignore`) và tuyệt đối không bao giờ bị nạp vào tri thức RAG hay tập dữ liệu huấn luyện AI.
