# TÀI LIỆU 02: CẤU TRÚC DỰ ÁN STUDY AGENT (BAMITIKA AI)

---

## 1. CÂY THƯ MỤC TỔNG THỂ DỰ ÁN

Dưới đây là cấu trúc toàn bộ cây thư mục và tập tin của dự án Study Agent (`Study-Agent-main`):

```text
Study-Agent-main/
├── .github/                                # Cấu hình GitHub Actions và quy trình cộng tác
│   ├── workflows/
│   │   └── team-checks.yml                 # CI workflow kiểm tra đa nền tảng (Windows, macOS, Python 3.12, Node 22)
│   └── pull_request_template.md            # Mẫu chuẩn cho Pull Request của nhóm 6 thành viên
├── app/                                    # Mã nguồn ứng dụng backend chính (Python 3.12)
│   ├── active_registry.py                  # Quản lý đăng ký adapter LoRA và base model đã thẩm định
│   ├── adapter_integrity.py               # Kiểm tra tính toàn vẹn cấu trúc và trọng số adapter
│   ├── answer_format.py                    # Làm sạch câu trả lời, loại bỏ thẻ suy nghĩ <think> và marker
│   ├── bilingual.py                        # Bộ dịch thuật song ngữ Anh - Việt ngữ cảnh có cache
│   ├── bilingual_terms.py                  # Từ điển và quy tắc dịch thuật ngữ tâm lý học/khoa học
│   ├── chunker.py                          # Cắt nhỏ trang văn bản thành chunks kèm overlap có ngữ cảnh
│   ├── config.py                           # Cấu hình biến môi trường, đường dẫn và siêu tham số hệ thống
│   ├── corpus_readiness.py                 # Đánh giá mức độ sẵn sàng của corpus trước khi đưa vào học
│   ├── corrective_training.py             # Xử lý các thử nghiệm huấn luyện sửa lỗi hồi quy
│   ├── curate_additions.py                 # Tuyển chọn các phần bổ sung vào tập dữ liệu
│   ├── curate_dataset_v7.py                # Pipeline tuyển chọn và lọc bộ dữ liệu huấn luyện v7
│   ├── curate_training.py                  # Các thuật toán kiểm duyệt và làm sạch dữ liệu huấn luyện
│   ├── dataset_balance.py                  # Kiểm tra và cân bằng phân phối các chủ đề trong dataset
│   ├── diagnose_v6.py                      # Chẩn đoán lỗi huấn luyện phiên bản v6
│   ├── dialogue.py                         # Cổng kiểm soát hội thoại (DialogueGate), ngân sách ngữ cảnh UTF-8
│   ├── document_lookup.py                  # Module tra cứu tài liệu độc lập (Read-only FTS + Hybrid)
│   ├── evaluate_model.py                   # Đánh giá chỉ số chất lượng mô hình
│   ├── evaluate_ollama.py                  # Đánh giá hiệu năng suy luận qua Ollama
│   ├── evaluate_v5_suite.py                # Bộ test đánh giá phiên bản v5
│   ├── evaluate_v6.py                      # Bộ test đánh giá phiên bản v6
│   ├── evaluation_metrics.py               # Các độ đo: lặp từ (repetition), trôi ngôn ngữ (language drift)
│   ├── file_lock.py                        # Module khóa file native (LockFileEx trên Win, fcntl trên Unix)
│   ├── fine_tune.py                        # Trình điều khiển huấn luyện MLX LoRA trên Apple Silicon
│   ├── gpu_lock.py                         # Điều phối khóa GPU liên tiến trình (GPULockManager)
│   ├── history.py                          # Lưu trữ lịch sử hỏi đáp và phiên đa lượt (HistoryStore)
│   ├── indexer.py                          # Bộ lập chỉ mục tài liệu (KnowledgeIndexer: SQLite FTS5 + Vector)
│   ├── memory_preflight.py                 # Kiểm tra và giám sát bộ nhớ RAM/VRAM trước khi chạy
│   ├── merge_training.py                   # Hợp nhất các tập dữ liệu huấn luyện đã duyệt
│   ├── mlx_infer.py                        # Script con thực thi suy luận mô hình MLX độc lập
│   ├── mlx_teacher.py                      # Sinh dữ liệu giáo viên (Teacher Model) bằng MLX
│   ├── ollama_client.py                    # Client giao tiếp HTTP với máy chủ Ollama cục bộ
│   ├── paired_evaluation.py                # Đánh giá đối đầu (A/B testing) giữa các phiên bản adapter
│   ├── pdf_extractor.py                    # Trích xuất văn bản từ PDF, DOCX, TXT, MD và ảnh (PDFExtractor)
│   ├── pipeline_orchestrator.py            # Điều phối toàn bộ quy trình từ dữ liệu đến huấn luyện
│   ├── practice.py                         # Dịch vụ sinh trắc nghiệm và trích xuất bài tập (PracticeService)
│   ├── preflight_7b.py                     # Kiểm tra điều kiện chạy thử nghiệm mô hình 7B
│   ├── prepare_additions.py                # Chuẩn bị các mẫu dữ liệu bổ sung
│   ├── prepare_v4.py                       # Chuẩn bị dữ liệu huấn luyện v4
│   ├── prepare_v5.py                       # Chuẩn bị dữ liệu huấn luyện v5
│   ├── prepare_v6.py                       # Chuẩn bị dữ liệu huấn luyện v6
│   ├── prepare_v7.py                       # Chuẩn bị dữ liệu huấn luyện v7
│   ├── query_normalizer.py                 # Chuẩn hóa câu hỏi tiếng Việt, sửa lỗi chính tả bằng model
│   ├── rag_agent.py                        # Agent điều phối RAG chính (PsychologyAgent / StudyAgent)
│   ├── run_ledger.py                       # Sổ cái theo dõi trạng thái các phiên huấn luyện (RunLedger)
│   ├── run_v6.py                           # Kịch bản thực thi huấn luyện v6
│   ├── run_v6_conservative.py              # Kịch bản huấn luyện v6 với tham số thận trọng
│   ├── safety.py                           # Bộ lọc an toàn: khủng hoảng tự hại, từ chối chẩn đoán (SafetyGuard)
│   ├── sample_ledger.py                    # Quản lý mẫu dữ liệu đã duyệt
│   ├── searcher.py                         # Tìm kiếm lai BM25 + Vector qua RRF (HybridSearcher)
│   ├── server.py                           # Máy chủ FastAPI chính, định nghĩa toàn bộ REST & SSE endpoints
│   ├── source_page_reviews.py              # Quản lý các bản ghi thẩm định trang nguồn
│   ├── study_acceptance.py                 # Đánh giá hồ sơ nghiệm thu mô hình học tập
│   ├── synthetic_curriculum.py             # Sinh giáo trình dữ liệu tổng hợp
│   ├── text_cleaner.py                     # Làm sạch văn bản tiếng Việt, sửa lỗi TCVN3, khử prompt injection
│   ├── timetable_ics.py                    # Xuất lịch chuẩn RFC 5545 iCalendar (.ics, múi giờ Asia/Ho_Chi_Minh)
│   ├── timetable_store.py                  # Lưu trữ bản nháp và lịch học chính thức (timetable.db)
│   ├── timetable_table.py                  # Nhận diện tọa độ bảng lịch học đại học (Literal Table OCR)
│   ├── timetable_vision.py                 # Trích xuất thời khóa biểu bằng VLM (qwen2.5vl:3b)
│   ├── token_auditor.py                    # Kiểm toán số lượng token trong tập dữ liệu
│   ├── topic_summarizer.py                 # Tóm tắt chủ đề phiên và sinh tiêu đề tự động (TopicSummarizer)
│   ├── trained_client.py                   # Client giao tiếp với mô hình MLX đã huấn luyện
│   ├── training_audit.py                   # Kiểm toán đối chiếu nguồn của tập huấn luyện
│   ├── training_data.py                    # Xử lý ngôn ngữ và chuẩn bị cặp dữ liệu hỏi-đáp
│   ├── training_telemetry.py               # Thu thập số liệu đo lường trong quá trình huấn luyện
│   ├── trial_audit.py                      # Kiểm toán các thử nghiệm huấn luyện
│   ├── verify_v6.py                        # Xác minh chất lượng dữ liệu v6
│   └── vision_ocr.py                       # Quản lý nhận diện OCR và quy trình thẩm định nhân sự (VisionOCRManager)
├── corpus/                                 # Quy ước cấu trúc metadata bàn giao nguồn học liệu
│   └── README.md                           # Hướng dẫn định dạng manifest, submission và release
├── docs/                                   # Tài liệu dự án
│   ├── team/                               # Tài liệu nội bộ nhóm
│   │   ├── BAO_CAO_SUA_LOI_2026-10-09.md   # Báo cáo sửa lỗi và các mốc kiểm chứng
│   │   └── PHAN_CONG_6_NGUOI.md            # Bảng phân công trách nhiệm chi tiết 6 vai trò (TV1 - TV6)
│   ├── 01_Y_TUONG_DU_AN.md                 # Tài liệu 1: Ý tưởng dự án
│   ├── 02_CAU_TRUC_DU_AN.md                # Tài liệu 2: Cấu trúc dự án (File này)
│   └── 03_CACH_TRIEN_KHAI_DU_AN.md         # Tài liệu 3: Hướng dẫn triển khai dự án
├── output/                                 # Thư mục chứa tài liệu xuất bản
│   └── pdf/
│       └── PHAN_CHIA_NHIEM_VU_DO_AN_NHOM.pdf # Bản PDF phân chia nhiệm vụ 6 người cập nhật đồng bộ
├── scripts/                                # Các script tiện ích vận hành và quản trị
│   ├── apple_vision_ocr.swift              # Helper gọi native Apple Vision OCR trên macOS
│   ├── build_pending_workspace.py          # Xây dựng workspace cho các nguồn chờ duyệt
│   ├── capture_handwritten_corpus.py       # Trích xuất dữ liệu chữ viết tay
│   ├── capture_pending_corpus.py           # Thu thập corpus chờ thẩm định
│   ├── check_history.py                    # Script CI kiểm tra xem PR có cập nhật LICH_SU_DU_AN.md không
│   ├── complete_corpus.py                  # Hoàn thiện bộ corpus
│   ├── create_v10_dataset.py               # Khởi tạo dataset v10
│   ├── curate_v10.py                       # Tuyển chọn dataset v10
│   ├── curate_v8_release.py                # Tuyển chọn bản phát hành v8
│   ├── dev.py                              # Trình điều khiển đa năng: serve, demo, check môi trường
│   ├── evaluate_rag_benchmark.py           # Chạy benchmark kiểm tra chất lượng RAG
│   ├── find_exact_16_sources.py            # Tìm kiếm 16 nguồn chính xác
│   ├── index_source_reviews.py             # Lập chỉ mục các bản thẩm định nguồn
│   ├── migrate_history_to_sessions.py      # Nâng cấp CSDL history cũ sang mô hình sessions
│   ├── prepare_16_excerpts.py              # Chuẩn bị 16 đoạn trích mẫu
│   ├── reconcile_pending_corpus.py         # Đối soát dữ liệu corpus chờ xử lý
│   ├── rejudge_v7_candidates.py            # Chấm điểm lại các ứng viên model v7
│   ├── release_string_reviews.py           # Phát hành bản review chuỗi
│   ├── run_qwen3_thinking_diagnostic.py    # Chẩn đoán token tư duy của dòng mô hình Qwen
│   ├── run_serial_reviewer_comparison.py   # So sánh chuỗi reviewer
│   ├── run_server.sh                       # Script bash chạy server đơn giản
│   ├── sample_candidate_sources.py         # Lấy mẫu các nguồn ứng viên
│   ├── service.sh                          # Script quản lý background service trên macOS
│   ├── start_detached_service.py           # Khởi chạy dịch vụ nền độc lập
│   ├── supervisor.sh                       # Giám sát trạng thái dịch vụ POSIX
│   ├── test_live_timetable_vision.py       # Kiểm tra trực tiếp trích xuất ảnh lịch
│   └── windows_setup.ps1                   # Thư viện hàm PowerShell hỗ trợ cài đặt trên Windows
├── static/                                 # Giao diện web frontend (Single Page Application)
│   ├── app.js                              # Logic hỏi đáp RAG, quản lý sessions, streaming SSE
│   ├── document-lookup.js                  # Logic tra cứu tài liệu, lọc sách, chuyển đổi tab công cụ
│   ├── index.html                          # Trang HTML giao diện chính duy nhất
│   ├── layout.js                           # Xử lý responsive sidebar và đóng mở menu mobile
│   ├── practice.js                         # Logic làm bài trắc nghiệm, lưu localStorage, lọc bài tập mẫu
│   ├── style.css                           # Bảng kiểu CSS chính của ứng dụng
│   ├── style.light-backup.css              # Bản sao lưu CSS giao diện sáng
│   ├── theme.css                           # Bảng màu Dark / Light theme native
│   ├── theme.js                            # Xử lý nút bật tắt giao diện sáng/tối
│   └── timetable.js                        # Logic kéo thả ảnh lịch, bảng nháp editor, xuất file .ics
├── tests/                                  # Bộ kiểm thử tự động (Pytest và Node.js)
│   ├── fixtures/                           # Dữ liệu thử nghiệm tổng hợp (Synthetic Data)
│   │   ├── documents/                      # Tài liệu PDF và Markdown mẫu phục vụ demo sạch
│   │   │   ├── demo.pdf                    # PDF demo tổng hợp
│   │   │   └── study_demo.md               # Tài liệu Markdown học tập demo
│   │   ├── qa/                             # Ca kiểm thử hỏi đáp mẫu
│   │   │   └── cases.json                  # Bộ câu hỏi và tiêu chí kiểm tra nguồn
│   │   ├── timetables/                     # Ảnh thời khóa biểu mẫu
│   │   │   ├── demo.png                    # Ảnh thời khóa biểu giả lập
│   │   │   └── expected.json               # Kết quả trích xuất kỳ vọng
│   │   └── README.md                       # Mô tả ranh giới dữ liệu fixture demo
│   ├── conftest.py                         # Cấu hình fixtures chung cho pytest
│   ├── document_lookup_ui.test.cjs         # Test giao diện tra cứu tài liệu bằng Node.js Test Runner
│   ├── practice_ui.test.cjs                # Test giao diện luyện tập và ôn tập bằng Node.js Test Runner
│   ├── test_adapter_integrity.py           # Test tính toàn vẹn adapter
│   ├── test_answer_quality.py              # Test chất lượng câu trả lời RAG
│   ├── test_api_server.py                  # Test các endpoint API FastAPI
│   ├── test_audit_regressions.py           # Test hồi quy các lỗi đã sửa (F-01 -> F-05)
│   ├── test_bilingual_training.py          # Test dữ liệu song ngữ
│   ├── test_codex_*.py                     # Các test hợp đồng kiểm toán chất lượng (14 files)
│   ├── test_continuous_pipeline.py         # Test pipeline tích hợp liên tục
│   ├── test_conversation_sessions.py       # Test quản lý phiên hội thoại đa lượt
│   ├── test_corpus_readiness.py            # Test đánh giá corpus
│   ├── test_corrective_training.py         # Test huấn luyện sửa lỗi
│   ├── test_curation_release_gates.py      # Test các cổng kiểm duyệt phát hành
│   ├── test_dataset_balance.py             # Test độ cân bằng tập dữ liệu
│   ├── test_detached_service.py            # Test dịch vụ nền
│   ├── test_dialogue_reliability.py        # Test độ tin cậy hội thoại và context budget
│   ├── test_document_lookup.py             # Test tính năng tra cứu tài liệu FTS và Hybrid
│   ├── test_entire_pending_reconciliation.py # Test đối soát toàn bộ pending
│   ├── test_evaluation_metrics.py          # Test độ đo lặp từ và trôi ngôn ngữ
│   ├── test_expanded_training.py           # Test huấn luyện mở rộng
│   ├── test_fine_tune_trials.py            # Test các đợt chạy fine-tune
│   ├── test_force_ocr.py                   # Test ép buộc chạy OCR
│   ├── test_gpu_coordination.py            # Test cơ chế khóa GPU giữa training và suy luận
│   ├── test_grounded_citations.py          # Test bắt buộc trích dẫn có căn cứ [S#]
│   ├── test_history.py                     # Test ghi nhận và truy vấn lịch sử
│   ├── test_learning_tools_ui_contract.py  # Test hợp đồng giao diện công cụ học tập
│   ├── test_new_folder_ingestion.py        # Test nạp thư mục tài liệu mới
│   ├── test_pdf_extractor.py               # Test trích xuất PDF và tài liệu đa định dạng
│   ├── test_pending_review_release.py      # Test phát hành thẩm định
│   ├── test_platform_support.py            # Test tính tương thích đa nền tảng (Windows vs Mac)
│   ├── test_practice.py                    # Test dịch vụ sinh trắc nghiệm và thẩm định đáp án
│   ├── test_preflight_7b.py                # Test kiểm tra bộ nhớ mô hình 7B
│   ├── test_rag_pipeline.py                # Test luồng RAG cơ bản
│   ├── test_registered_timetable_table.py  # Test nhận diện bảng thời khóa biểu đại học
│   ├── test_removed_sources.py             # Test xử lý khi tài liệu bị xóa
│   ├── test_safety.py                      # Test an toàn y tế và phát hiện khủng hoảng
│   ├── test_searcher.py                    # Test thuật toán HybridSearcher
│   ├── test_service_health.py              # Test kiểm tra sức khỏe hệ thống
│   ├── test_session_review_regressions.py  # Test hồi quy rà soát phiên
│   ├── test_shared_history.py              # Test chia sẻ lịch sử
│   ├── test_source_page_reviews.py         # Test rà soát trang nguồn
│   ├── test_study_agent_execution_*.py     # Test thực thi agent
│   ├── test_team_demo.py                   # Test môi trường demo sạch của nhóm
│   ├── test_text_cleaner.py                # Test bộ làm sạch văn bản tiếng Việt
│   ├── test_timetable_feature.py           # Test tính năng thời khóa biểu từ ảnh và xuất .ics
│   ├── test_trained_client.py              # Test client mô hình đã huấn luyện
│   ├── test_training_audit.py              # Test kiểm toán huấn luyện
│   ├── test_user_feedback_content_contract.py # Test hợp đồng nội dung phản hồi người dùng
│   ├── test_v6_data.py                     # Test dữ liệu v6
│   └── windows_setup_contract.ps1          # Test hợp đồng cài đặt PowerShell trên Windows
├── .env.example                            # Tệp mẫu cấu hình các biến môi trường
├── .gitattributes                          # Cấu hình chuẩn hóa ký tự xuống dòng Git
├── .gitignore                              # Định nghĩa các tệp và thư mục bị bỏ qua (bảo vệ dữ liệu cá nhân)
├── constraints-mlx-py313.txt               # Bộ phiên bản thư viện cố định cho MLX (Python 3.13)
├── constraints-web-py312.txt               # Bộ phiên bản thư viện cố định cho Web Runtime (Python 3.12)
├── CONTRIBUTING.md                         # Hướng dẫn đóng góp mã nguồn, quy chuẩn PR và nhánh
├── Improvement_QA_Study_Agent.docx         # Tài liệu phân tích 8 phương án cải tiến chất lượng QA (A -> H)
├── LICENSE                                 # Giấy phép phần mềm mã nguồn mở MIT
├── LICH_SU_DU_AN.md                        # Nhật ký ghi nhận toàn bộ lịch sử thay đổi của dự án
├── pytest.ini                              # Cấu hình Pytest mặc định
├── pytest.windows.ini                      # Cấu hình Pytest dành riêng cho Windows (bỏ test Mac/MLX)
├── README.md                               # Tài liệu hướng dẫn sử dụng và giới thiệu chung
├── README_MAC.md                           # Hướng dẫn cài đặt và phát triển chi tiết trên macOS
├── README_QUY_TAC.md                       # Quy tắc quản lý thay đổi, ranh giới tài sản và phối hợp
├── README_WINDOWS.md                       # Hướng dẫn cài đặt và phát triển chi tiết trên Windows
├── requirements.txt                        # Danh sách thư viện runtime cho web
├── requirements-dev.txt                    # Thư viện cho môi trường phát triển và kiểm thử
├── requirements-mlx.txt                    # Thư viện huấn luyện MLX trên Apple Silicon
├── requirements-windows.txt                # Thư viện cài đặt tương thích môi trường Windows
├── requirements-windows-tools.json         # Manifest danh mục công cụ (WinGet) và mô hình cho Windows
├── run.py                                  # CLI launcher chính của ứng dụng
├── setup_windows.ps1                       # Script PowerShell cài đặt tự động toàn bộ trên Windows
├── start_app.command                       # Script nhấp đúp khởi chạy nhanh trên macOS
├── start_windows.ps1                       # Script PowerShell khởi chạy ứng dụng trên Windows
└── test_windows.ps1                        # Script PowerShell chạy toàn bộ test kiểm thử trên Windows
```

---

## 2. BẢNG KIỂM KÊ VÀ PHÂN LOẠI TOÀN BỘ FILE TRONG REPOSITORY

Dưới đây là bảng phân loại toàn bộ các tập tin cấu thành hệ thống:

| Phân nhóm | Tên file / Đường dẫn | Ngôn ngữ / Công nghệ | Vai trò kỹ thuật trong hệ thống |
| :--- | :--- | :--- | :--- |
| **Cấu hình gốc** | `.env.example` | Dotenv | Mẫu khai báo các biến môi trường cấu hình cổng, host, đường dẫn dữ liệu và tên model. |
| **Cấu hình gốc** | `.gitignore` | Git Config | Bảo vệ an toàn dữ liệu: chặn commit `src/`, `data/`, model weights, adapter, DB và tệp môi trường. |
| **Cấu hình gốc** | `LICENSE` | Text | Giấy phép mã nguồn mở MIT bảo hộ quyền tác giả cho mã nguồn dự án. |
| **Quản lý Thư viện**| `requirements.txt` | Pip Requirements | Khai báo các thư viện phụ thuộc cốt lõi cho web runtime (FastAPI, PyMuPDF, Uvicorn...). |
| **Quản lý Thư viện**| `requirements-dev.txt` | Pip Requirements | Khai báo thêm `httpx` và `pytest` phục vụ kiểm thử và phát triển. |
| **Quản lý Thư viện**| `requirements-windows.txt`| Pip Requirements | Wrapper cài đặt trên Windows liên kết với bộ ràng buộc phiên bản. |
| **Quản lý Thư viện**| `requirements-mlx.txt` | Pip Requirements | Khai báo các thư viện MLX và Transformers cho macOS Apple Silicon Python 3.13. |
| **Ràng buộc Version**| `constraints-web-py312.txt`| Pip Constraints | Cố định phiên bản chính xác của toàn bộ cây dependency trên Python 3.12 tránh xung đột. |
| **Ràng buộc Version**| `constraints-mlx-py313.txt`| Pip Constraints | Cố định phiên bản chính xác cho môi trường huấn luyện MLX trên Python 3.13. |
| **Công cụ Windows** | `requirements-windows-tools.json`| JSON Manifest | Khai báo ID các gói WinGet (Python 3.12, Git, Ollama) và danh sách model cần tải. |
| **Script khởi động** | `run.py` | Python 3.12 | CLI đa năng: cung cấp các lệnh `index`, `embed`, `status`, `query`, `serve`, `train`. |
| **Script Windows** | `setup_windows.ps1` | PowerShell | Bộ cài đặt tự động trên Windows: kiểm tra và cài công cụ qua WinGet, tạo venv, kéo model Ollama. |
| **Script Windows** | `start_windows.ps1` | PowerShell | Khởi động server nhanh trên Windows bằng Python của `.venv` với tùy chọn profile `demo` hoặc `local`. |
| **Script Windows** | `test_windows.ps1` | PowerShell | Chạy tập kiểm thử tự động của Windows thông qua cấu hình `pytest.windows.ini`. |
| **Script macOS** | `start_app.command` | Bash / Shell | Kịch bản cho phép người dùng Mac nhấp đúp để khởi động ứng dụng trong Terminal. |
| **Backend Core** | `app/server.py` | Python (FastAPI) | Trọng tâm điều phối toàn bộ API backend, định tuyến REST và xử lý streaming Server-Sent Events. |
| **Backend Core** | `app/config.py` | Python | Điểm tập trung cấu hình đường dẫn (`BASE_DIR`, `DATA_DIR`), model mặc định, ngưỡng tìm kiếm. |
| **Backend Core** | `app/rag_agent.py` | Python | Trái tim của hệ thống RAG: kiểm tra an toàn, truy xuất lai, điều phối LLM, đối chiếu trích dẫn `[S#]`. |
| **Backend Core** | `app/document_lookup.py` | Python | Xử lý tra cứu tài liệu độc lập, render ảnh trang PDF và sinh liên kết xem trước. |
| **Backend Core** | `app/indexer.py` | Python | Quét thư mục, băm SHA-256, trích xuất văn bản, chunking và lưu vào SQLite FTS5 + Vector blobs. |
| **Backend Core** | `app/searcher.py` | Python | Thuật toán tìm kiếm lai kết hợp điểm BM25 và khoảng cách Cosine thông qua Reciprocal Rank Fusion (RRF). |
| **Backend Core** | `app/practice.py` | Python | Dịch vụ sinh câu hỏi trắc nghiệm bám sát trang sách, thẩm định trích dẫn 2 bước và lọc bài tập mẫu. |
| **Backend Core** | `app/timetable_vision.py`| Python | Trích xuất thời khóa biểu bằng VLM (`qwen2.5vl:3b`), chuẩn hóa thứ/giờ và phát hiện trùng lịch. |
| **Backend Core** | `app/timetable_store.py` | Python | Cơ sở dữ liệu SQLite quản lý bản nháp thời khóa biểu, lịch học chính thức và VLM cache. |
| **Backend Core** | `app/timetable_ics.py` | Python | Bộ sinh dữ liệu lịch chuẩn RFC 5545 iCalendar (`.ics`), múi giờ Việt Nam, line folding 75 bytes. |
| **Backend Core** | `app/timetable_table.py` | Python | Nhận diện ký tự và tọa độ hình học cho bảng đăng ký môn học đại học (Literal Table OCR). |
| **Backend Core** | `app/dialogue.py` | Python | Khóa độc quyền phiên suy luận (`DialogueGate`), định tuyến ý định, tính toán ngân sách UTF-8 bytes. |
| **Backend Core** | `app/history.py` | Python | CSDL SQLite quản lý lịch sử hội thoại, phiên đa lượt, kiểm soát idempotency qua `request_id`. |
| **Backend Core** | `app/topic_summarizer.py`| Python | Tự động tóm tắt chủ đề hội thoại bằng mô hình ngôn ngữ và tạo tiêu đề dự phòng không tốn GPU. |
| **Backend Core** | `app/safety.py` | Python | Bộ lọc an toàn: phát hiện dấu hiệu tự sát/tự hại (kích hoạt hotline 115) và từ chối chẩn đoán y tế. |
| **Backend Core** | `app/gpu_lock.py` | Python | Khóa GPU liên tiến trình (`GPULockManager`), bảo vệ bộ nhớ thống nhất 16GB RAM, trục xuất model Ollama. |
| **Backend Core** | `app/file_lock.py` | Python | Lớp trừu tượng khóa file: dùng Win32 API `LockFileEx` trên Windows và `fcntl.flock` trên Unix. |
| **Backend Core** | `app/pdf_extractor.py` | Python | Trích xuất văn bản đa định dạng (PDF, DOCX, PPTX, TXT, MD, Ảnh), phát hiện scan, kiểm tra symlink. |
| **Backend Core** | `app/vision_ocr.py` | Python | Quản lý các backend OCR (Tesseract, Ollama VLM, Apple Vision) và quy trình soát lỗi nhân sự. |
| **Backend Core** | `app/ollama_client.py` | Python | Giao tiếp HTTP với Ollama: kiểm tra sức khỏe, sinh text streaming, tạo embeddings, giải phóng VRAM. |
| **Backend Core** | `app/trained_client.py` | Python | Giao tiếp với mô hình MLX cục bộ trên Mac (unadapted base hoặc adapter đã nghiệm thu). |
| **Backend MLX** | `app/fine_tune.py` | Python | Kịch bản huấn luyện LoRA cho Qwen2.5-3B bằng framework MLX, tích hợp giám sát bộ nhớ và sổ cái. |
| **Backend MLX** | `app/run_ledger.py` | Python | Sổ cái trạng thái các run huấn luyện (CREATED, PREFLIGHT, RUNNING, COMPLETED, FAILED, OOM). |
| **Frontend UI** | `static/index.html` | HTML5 | Giao diện Single Page Application: 3 chế độ (Hỏi đáp, Công cụ học tập, Thời khóa biểu), modal thư viện. |
| **Frontend UI** | `static/app.js` | JavaScript | Xử lý chat stream SSE, hiển thị citation badges, quản lý lịch sử hội thoại trên sidebar. |
| **Frontend UI** | `static/document-lookup.js`| JavaScript | Điều khiển tìm kiếm tài liệu, xem trước nội dung, chọn phạm vi bài học và chuyển đổi tab. |
| **Frontend UI** | `static/practice.js` | JavaScript | Giao diện làm trắc nghiệm, chấm điểm, lưu tiến độ ôn lại vào localStorage, trích xuất bài tập. |
| **Frontend UI** | `static/timetable.js` | JavaScript | Kéo thả ảnh lịch, chỉnh sửa bảng nháp trực tiếp, đổi tiết sang giờ, tải file `.ics`. |
| **Frontend UI** | `static/layout.js` | JavaScript | Xử lý thu gọn thanh bên (sidebar collapse), hỗ trợ màn hình di động (mobile drawer). |
| **Frontend UI** | `static/theme.js` | JavaScript | Xử lý chuyển đổi giao diện Sáng / Tối, lưu trạng thái vào localStorage. |
| **Frontend UI** | `static/style.css` | CSS3 | Định dạng giao diện tổng thể, biến màu CSS, bố cục lưới responsive và typography. |
| **Frontend UI** | `static/theme.css` | CSS3 | Định nghĩa bảng màu chuẩn cho Dark Mode và Light Mode. |
| **Kiểm thử** | `tests/test_*.py` (50+ files)| Python (Pytest) | Bộ kiểm thử chức năng, kiểm thử đơn vị, kiểm thử hồi quy và kiểm thử hợp đồng API. |
| **Kiểm thử UI** | `tests/*.test.cjs` (2 files) | JavaScript (Node 22)| Kiểm tra giao diện và luồng DOM của phần Tra cứu và Luyện tập bằng Node.js Test Runner. |
| **CI / CD** | `.github/workflows/team-checks.yml`| YAML | Kịch bản kiểm tra tự động trên GitHub Actions: chạy trên cả Windows-latest và macOS-latest. |

---

## 3. KIẾN TRÚC PHÂN LỚP VÀ CHI TIẾT CÁC MODULE TRONG THƯ MỤC `app/`

### 3.1. Phân tích Chi tiết Từng Module Backend

#### 1. `app/config.py` — Trung tâm Cấu hình Hệ thống
- **Nhiệm vụ:** Định nghĩa toàn bộ hằng số, đường dẫn thư mục và siêu tham số mặc định cho toàn bộ ứng dụng.
- **Biến và Hằng số Cốt lõi:**
  - `BASE_DIR`: Đường dẫn tuyệt đối đến thư mục gốc của repository.
  - `_workspace_path(name, default)`: Hàm helper giải quyết đường dẫn tuyệt đối hoặc tương đối theo biến môi trường.
  - `SRC_DIR`: Đường dẫn thư mục chứa giáo trình nguồn (mặc định: `src/`).
  - `DATA_DIR`: Thư mục lưu trữ dữ liệu cục bộ (mặc định: `data/`).
  - `DB_PATH`: Đường dẫn CSDL tri thức chính (`data/knowledge_base.db`).
  - `OLLAMA_BASE_URL`: URL dịch vụ Ollama (mặc định: `http://localhost:11434`).
  - `DEFAULT_CHAT_MODEL`: Mô hình chat mặc định (`qwen2.5:3b` trên Windows, `qwen2.5-3b-4bit` trên Mac).
  - `DEFAULT_EMBED_MODEL`: Mô hình embedding mặc định (`bge-m3`).
  - `CHUNK_SIZE_CHARS` (1200) & `CHUNK_OVERLAP_CHARS` (200): Cấu hình kích thước cắt đoạn.
  - `DEFAULT_TOP_K` (6), `FTS_WEIGHT` (0.5), `SEMANTIC_WEIGHT` (0.5), `RRF_K` (60): Siêu tham số tìm kiếm lai.
  - `CRISIS_HOTLINES`: Danh mục đường dây nóng cấp cứu y tế Việt Nam (115).

#### 2. `app/server.py` — Máy chủ Web và Điều phối API (FastAPI)
- **Nhiệm vụ:** Định nghĩa ứng dụng FastAPI, cấu hình định tuyến (routes), bảo vệ đồng thời và xử lý ngoại lệ HTTP.
- **Các Pydantic Models Chính:**
  - `ChatRequest`: Kiểm thực câu hỏi (`query` tối đa 4000 ký tự), `chat_history` (tối đa 32 lượt), `top_k` (1..12), `source_document_id`, `source_page_num` (bắt buộc đi kèm nhau).
  - `PracticeGenerateRequest`: Yêu cầu sinh câu hỏi trắc nghiệm từ một trang sách.
  - `PracticeAnswerRequest`: Gửi đáp án trắc nghiệm (`A`, `B`, `C`, `D`).
  - `TimetableExtractRequest`: Nhận ảnh base64 để phân tích thời khóa biểu.
  - `TimetableConfirmRequest` & `TimetableConfirmEntry`: Kiểm thực danh sách môn học xác nhận (giờ bắt đầu < giờ kết thúc, thứ 1..7).
  - `OCRReviewRequest`: Gửi nội dung văn bản sau khi người thẩm định soát lỗi.
- **Các Endpoints Nổi bật:**
  - `POST /api/chat/stream`: Stream SSE hỏi đáp RAG, xử lý khóa GPU, khóa hội thoại và kiểm tra idempotency qua `request_id`.
  - `GET /api/documents/search`: Tìm kiếm tài liệu bằng từ khóa (FTS) hoặc lai (Hybrid).
  - `POST /api/practice/generate` & `POST /api/practice/answer`: Sinh và chấm trắc nghiệm.
  - `POST /api/timetable/extract` & `POST /api/timetable/confirm`: Phân tích và lưu lịch học.
  - `GET /api/timetable/export.ics`: Xuất file lịch tiêu chuẩn.
  - `GET /api/health`: Báo cáo trạng thái máy chủ, kết nối Ollama và trạng thái bận của GPU.

#### 3. `app/rag_agent.py` — Agent Hỏi đáp Học thuật (PsychologyAgent / StudyAgent)
- **Nhiệm vụ:** Điều phối toàn bộ quy trình từ câu hỏi thô đến câu trả lời hoàn chỉnh có bảo chứng nguồn.
- **Các Hàm và Thành phần Chính:**
  - `SYSTEM_PROMPT`: Tập 12 quy tắc cốt lõi ép buộc mô hình: chỉ dựa vào nguồn hiện tại, gắn thẻ `[S#]`, không bịa đặt nguồn, bảo vệ bản quyền, an toàn y tế, giữ nguyên điều kiện/giả thiết toán học.
  - `weak_keyword_evidence(query, chunks)`: Kiểm tra độ bao phủ từ vựng, tách biệt từ chỉ dẫn (`nêu`, `hãy`, `giải thích`) với thuật ngữ bản chất (`ánh xạ tuyến tính`).
  - `has_relevant_evidence(query, chunks)`: Đánh giá xem tài liệu trích xuất có đủ bằng chứng để trả lời hay không. Nếu không, agent lập tức từ chối để tránh bịa đặt.
  - `process_query_stream()`: Bộ sinh generator trả về các event theo luồng: kiểm tra an toàn -> chuẩn hóa câu hỏi -> tìm kiếm lai -> dịch ngữ cảnh -> phân bổ budget -> gọi model -> đối soát trích dẫn `[S#]`.
  - `process_query_sync()`: Hàm bọc đồng bộ trả về kết quả JSON đầy đủ kèm siêu dữ liệu truy vết.

#### 4. `app/document_lookup.py` — Tra cứu Tài liệu Độc lập (DocumentLookup)
- **Nhiệm vụ:** Cung cấp chức năng tìm kiếm và hiển thị tài liệu dạng chỉ đọc (Read-only), hoàn toàn tách biệt khỏi lịch sử chat.
- **Các Phương thức Chính:**
  - `connect()`: Mở kết nối SQLite với URI `mode=ro` (chỉ đọc) để đảm bảo không bao giờ làm hỏng CSDL.
  - `documents()`: Lấy danh sách các tài liệu đã lập chỉ mục và còn tồn tại trên ổ đĩa.
  - `search(query, limit, doc_id, method)`: Thực thi FTS5 BM25 hoặc Hybrid search; sinh đường dẫn xem PDF và ảnh trang gốc.
  - `page_image(doc_id, page_num)`: Dùng PyMuPDF render trang PDF thành ảnh PNG kích thước tối đa 1400x2200 mà không làm méo mó công thức toán hay bảng biểu.
  - `source_preview(filename, page_num)`: Ánh xạ từ tên file và số trang sang ID CSDL an toàn.

#### 5. `app/indexer.py` — Bộ Lập chỉ mục Tri thức (KnowledgeIndexer)
- **Nhiệm vụ:** Quét thư mục sách, trích xuất nội dung, chia đoạn văn bản, tính toán vector embedding và lưu trữ vào CSDL.
- **Cơ chế Kỹ thuật:**
  - `pack_vector(vec)` & `unpack_vector(blob)`: Chuyển đổi mảng số thực float32 thành nhị phân BLOB qua thư viện `struct` để lưu trực tiếp trong SQLite mà không cần cài extension vector ngoài.
  - `_init_db()`: Khởi tạo bảng `documents`, `chunks`, bảng ảo FTS5 `chunks_fts` và 3 triggers tự động đồng bộ (`chunks_ai`, `chunks_ad`, `chunks_au`).
  - `index_all()`: Quét toàn bộ file trong `SRC_DIR`. Kiểm tra băm SHA-256 để bỏ qua các file không đổi (Incremental Indexing). Tự động dọn dẹp các tài liệu đã bị xóa khỏi đĩa.
  - `backfill_missing_embeddings()`: Quét các đoạn chunk chưa có vector và gọi mô hình `bge-m3` để bổ sung embedding theo từng lô (batch size 32).
  - `update_page_chunks()`: Cho phép cập nhật lại nội dung các đoạn văn bản của một trang sau khi con người thẩm định OCR mà vẫn bảo toàn giao dịch CSDL.

#### 6. `app/searcher.py` — Tìm kiếm Lai Đa phương thức (HybridSearcher)
- **Nhiệm vụ:** Kết hợp sức mạnh tìm kiếm từ khóa chính xác của BM25 và tìm kiếm ý nghĩa ngữ nghĩa của Vector Embedding.
- **Các Thuật toán Chính:**
  - `_clean_fts_query()`: Làm sạch truy vấn FTS5, thêm ký tự đại diện `*` và hỗ trợ từ dính tiếng Việt (gluewords như `xạtuyến`).
  - `search_fts()`: Tìm kiếm BM25 trên SQLite FTS5; tự động nhận diện câu hỏi định nghĩa để hạ điểm các đoạn mục lục/tiêu đề và tăng điểm các đoạn chứa từ khóa định nghĩa/tính chất.
  - `search_semantic()`: Tính khoảng cách Cosine giữa vector truy vấn và toàn bộ chunks có embedding; lọc theo ngưỡng tương đồng tối thiểu.
  - `search_hybrid()`: Hợp nhất kết quả bằng Reciprocal Rank Fusion (RRF), cân bằng số lượng đoạn trích theo từng đầu sách để tránh việc một cuốn sách chiếm lĩnh toàn bộ kết quả.

#### 7. `app/dialogue.py` — Cổng Hội thoại và Ngân sách Ngữ cảnh
- **Nhiệm vụ:** Quản lý hàng đợi suy luận cục bộ và ngăn chặn tràn cửa sổ ngữ cảnh (Context Window Overflow).
- **Các Thành phần Chính:**
  - `DialogueGate`: Khóa độc quyền toàn tiến trình thông qua tệp `data/runtime/dialogue.lock`. Đảm bảo mỗi thời điểm chỉ có 1 câu hỏi được nạp ngữ cảnh và ghi vào CSDL.
  - `dialogue_intent()`: Định tuyến xác định các câu hỏi xã giao (chào hỏi, cảm ơn) hoặc các câu hỏi nối tiếp đại từ (`nó là gì`, `cho ví dụ nữa`).
  - `build_context()`: Tính toán ngân sách UTF-8 bytes bảo thủ. Bảo đảm tổng kích thước system prompt + user query + context passages + chat history không vượt quá giới hạn mô hình (8192 bytes), luôn dự phòng 640 tokens cho câu trả lời. Mã nguồn cũ trong lịch sử được ẩn đi để không gây nhầm lẫn với trích dẫn của lượt hiện tại.

#### 8. `app/gpu_lock.py` — Điều phối Khóa GPU (GPULockManager)
- **Nhiệm vụ:** Phân định tài nguyên phần cứng, ngăn ngừa xung đột bộ nhớ thống nhất (Unified Memory) giữa tiến trình huấn luyện MLX và tiến trình suy luận Ollama trên máy Mac 16GB RAM.
- **Cơ chế Hoạt động:**
  - Khóa tệp cấp nhân (`fcntl.flock` trên Mac / `LockFileEx` trên Windows) tại `data/runtime/gpu.lock`.
  - Hai chế độ khóa:
    - *Shared Lock (Khóa chia sẻ):* Dành cho các tác vụ suy luận (Inference), cho phép nhiều yêu cầu đọc đồng thời.
    - *Exclusive Lock (Khóa độc quyền):* Dành cho tiến trình huấn luyện MLX LoRA, chặn toàn bộ suy luận cho đến khi huấn luyện xong.
  - `unload_resident_models()`: Tự động gọi Ollama giải phóng toàn bộ mô hình khỏi VRAM trước khi bắt đầu huấn luyện MLX để tránh tràn bộ nhớ.
  - Cơ chế tự phục hồi (Auto-healing): Tự động phát hiện nếu tiến trình huấn luyện bị crash hoặc bị kill đột ngột để giải phóng trạng thái về `idle`.

#### 9. `app/file_lock.py` — Lớp Trừu tượng Khóa File Đa nền tảng
- **Nhiệm vụ:** Đem lại ngữ nghĩa khóa tệp đồng nhất cho cả Unix và Windows.
- **Triển khai:**
  - Trên Unix/macOS: Sử dụng module chuẩn `fcntl.flock`.
  - Trên Windows: Do Windows không có `fcntl`, module sử dụng `ctypes` gọi trực tiếp hàm Win32 API `kernel32.LockFileEx` và `kernel32.UnlockFileEx` với cấu trúc `OVERLAPPED`. Hỗ trợ đầy đủ cờ `LOCK_SH` (shared), `LOCK_EX` (exclusive), `LOCK_NB` (non-blocking).
  - Hàm `windows_pid_alive()`: Kiểm tra sự tồn tại của tiến trình trên Windows an toàn qua `OpenProcess` và `GetExitCodeProcess`, tránh dùng `os.kill(pid, 0)` vốn có thể gây dừng tiến trình trên Windows.

#### 10. `app/timetable_vision.py`, `timetable_store.py`, `timetable_ics.py`, `timetable_table.py`
- **Hệ thống Thời khóa biểu hoàn chỉnh:**
  - `timetable_vision.py`: Xác thực ảnh an toàn qua Pillow; gọi mô hình `qwen2.5vl:3b` với JSON schema ràng buộc; chuẩn hóa ngày/giờ và phát hiện xung đột.
  - `timetable_store.py`: Quản lý CSDL `timetable.db` gồm các bảng `timetable_drafts` (bản nháp), `timetable_confirmed` (lịch đã lưu) và `timetable_vlm_cache` (bộ nhớ đệm kết quả trích xuất theo mã băm ảnh).
  - `timetable_table.py`: Nhận diện hình học các ô chữ in của bảng đăng ký môn học đại học, tách riêng các buổi Lý thuyết và Thực hành.
  - `timetable_ics.py`: Chuyển đổi các buổi học thành sự kiện lặp hàng tuần `RRULE` trong tệp `.ics`, cấu hình múi giờ chuẩn `Asia/Ho_Chi_Minh` và bẻ dòng 75 ký tự theo RFC 5545.

#### 11. `app/practice.py` — Dịch vụ Luyện tập Chủ động (PracticeService)
- **Nhiệm vụ:** Tự động tạo bộ câu hỏi trắc nghiệm bám sát theo tài liệu và trích xuất bài tập mẫu có sẵn.
- **Cơ chế Bảo chứng 2 bước:**
  1. *Bước 1:* Yêu cầu mô hình tạo câu hỏi trắc nghiệm kèm chuỗi trích dẫn nguyên văn (`evidence_quote`) từ đoạn văn bản nguồn.
  2. *Bước 2 (`_verify_questions`):* Thuật toán đối soát chuỗi ký tự kiểm tra xem `evidence_quote` có xuất hiện liên tục và nguyên văn trong tài liệu hay không; nếu không khớp, câu hỏi bị loại bỏ để đảm bảo tính khách quan tuyệt đối.
  - Lưu trữ phiên làm bài trong bộ nhớ đệm (TTL 60 phút), giữ kín đáp án cho đến khi người học gửi câu trả lời.
  - Quét và lọc bài tập mẫu nguyên bản thông qua biểu thức chính quy nhận diện tiêu đề bài tập (`EXERCISE_HEADING`).

#### 12. `app/history.py` & `app/topic_summarizer.py` — Quản lý Phiên và Tóm tắt
- **Nhiệm vụ:** Duy trì lịch sử học tập bền vững trên máy người dùng.
- **Cơ chế Hoạt động:**
  - `history.py`: CSDL `history.db` quản lý cấu trúc phiên (`sessions`) và các lượt hỏi đáp theo thứ tự (`session_turns`).
  - Hỗ trợ cơ chế Idempotency: Kiểm tra `request_id` để tránh việc người dùng bấm gửi nhiều lần tạo ra các lượt trùng lặp.
  - Hàm `generate_fallback_title()`: Tự động trích xuất tiêu đề ngắn gọn từ câu hỏi đầu tiên bằng thuật toán xử lý chuỗi thuần túy (Zero GPU cost).
  - `topic_summarizer.py`: Sử dụng mô hình ngôn ngữ tóm tắt nội dung chính của phiên hội thoại (1-3 câu), bảo vệ tiêu đề thủ công do người dùng tự đặt không bị ghi đè.

#### 13. `app/pdf_extractor.py` & `app/vision_ocr.py` — Xử lý Văn bản và OCR
- **Nhiệm vụ:** Đọc và số hóa toàn bộ tài liệu đầu vào.
- **Cơ chế Hoạt động:**
  - `pdf_extractor.py`: Hỗ trợ định dạng phong phú (`.pdf`, `.docx`, `.pptx`, `.txt`, `.md`, `.png`, `.jpg`). Kiểm tra tính an toàn của symlink, ngăn chặn tấn công directory traversal thoát khỏi thư mục nguồn.
  - `vision_ocr.py`: Quản lý 3 backend OCR (`tesseract`, `ollama_vision`, `apple_vision`). Cung cấp quy trình soát lỗi nhân sự (Human-in-the-loop review) qua giao diện web; chỉ các trang đã được duyệt (`is_verified = True`) mới được phép đưa vào tập dữ liệu huấn luyện.

---

## 4. CƠ SỞ DỮ LIỆU VÀ MÔ HÌNH DỮ LIỆU (DATA SCHEMAS)

Hệ thống Study Agent sử dụng **ba cơ sở dữ liệu SQLite độc lập** nhằm phân tách ranh giới dữ liệu tri thức và dữ liệu cá nhân:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       data/knowledge_base.db                                │
│                   (Tri thức học thuật đã lập chỉ mục)                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  • documents: Danh mục file sách, hash SHA256, số trang, trạng thái scan    │
│  • chunks: Các đoạn văn bản 1200 ký tự, số trang, vector embedding nhị phân │
│  • chunks_fts: Bảng ảo FTS5 phục vụ tìm kiếm toàn văn BM25 (unicode61)      │
│  • Triggers: chunks_ai, chunks_ad, chunks_au (Tự động đồng bộ FTS)          │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           data/history.db                                   │
│                     (Lịch sử hỏi đáp và phiên làm việc)                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  • sessions: Danh sách phiên trò chuyện, tiêu đề, tóm tắt, revision         │
│  • session_turns: Chi tiết từng lượt hỏi-đáp, trích dẫn JSON, model         │
│  • searches: Bảng lưu trữ lịch sử tra cứu cũ (legacy compatibility)         │
│  • history_metadata: Quản lý phiên bản migration của cơ sở dữ liệu          │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                          data/timetable.db                                  │
│                 (Dữ liệu thời khóa biểu và thị giác máy tính)               │
├─────────────────────────────────────────────────────────────────────────────┤
│  • timetable_drafts: Các bản nháp trích xuất từ ảnh chờ người dùng duyệt    │
│  • timetable_confirmed: Lịch học chính thức đã xác nhận, thứ, giờ, phòng    │
│  • timetable_confirmation_events: Lịch sử các lần xác nhận hoặc ghi đè      │
│  • timetable_vlm_cache: Bộ nhớ đệm kết quả VLM theo hash ảnh và model digest│
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.1. Chi tiết Lược đồ CSDL Tri thức (`knowledge_base.db`)

```sql
-- 1. Bảng quản lý tài liệu nguồn
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT UNIQUE NOT NULL,            -- Đường dẫn tương đối tính từ src/
    clean_title TEXT NOT NULL,                 -- Tên sách thân thiện hiển thị trên giao diện
    filepath TEXT NOT NULL,                    -- Đường dẫn tuyệt đối trên đĩa
    file_size INTEGER NOT NULL,                -- Dung lượng file (bytes)
    file_hash TEXT NOT NULL,                   -- Mã băm SHA-256 phát hiện thay đổi
    total_pages INTEGER NOT NULL,              -- Tổng số trang của tài liệu
    extracted_pages_count INTEGER NOT NULL,    -- Số trang đã trích xuất chữ thành công
    is_scanned INTEGER NOT NULL DEFAULT 0,     -- 1 nếu là tài liệu scan dạng ảnh
    status TEXT NOT NULL,                      -- 'indexed', 'scanned_unocred', 'ocr_partial_reviewed', 'error'
    error_message TEXT,                        -- Thông báo lỗi nếu trích xuất thất bại
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Bảng lưu trữ các đoạn văn bản (Chunks) và Vector
CREATE TABLE chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    book_title TEXT NOT NULL,                  -- Tên sách phục vụ hiển thị
    filename TEXT NOT NULL,                    -- Tên file nguồn
    page_num INTEGER NOT NULL,                 -- Số trang gốc trong tài liệu
    chunk_index INTEGER NOT NULL,              -- Thứ tự đoạn trong trang
    text TEXT NOT NULL,                        -- Nội dung văn bản của đoạn (tối đa ~1200 ký tự)
    embedding BLOB,                            -- Vector nhị phân float32 1024 chiều (pack_vector)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_chunks_doc_id ON chunks(doc_id);
CREATE INDEX idx_chunks_page ON chunks(doc_id, page_num);

-- 3. Bảng ảo FTS5 phục vụ tìm kiếm toàn văn BM25
CREATE VIRTUAL TABLE chunks_fts USING fts5(
    book_title,
    text,
    content='chunks',
    content_rowid='id',
    tokenize='unicode61 remove_diacritics 0'   -- Giữ nguyên dấu tiếng Việt để tìm chính xác
);

-- 4. Các Triggers tự động đồng bộ bảng ảo FTS5 khi bảng chunks thay đổi
CREATE TRIGGER chunks_ai AFTER INSERT ON chunks BEGIN
    INSERT INTO chunks_fts(rowid, book_title, text) VALUES (new.id, new.book_title, new.text);
END;

CREATE TRIGGER chunks_ad AFTER DELETE ON chunks BEGIN
    INSERT INTO chunks_fts(chunks_fts, rowid, book_title, text) VALUES('delete', old.id, old.book_title, old.text);
END;

CREATE TRIGGER chunks_au AFTER UPDATE ON chunks BEGIN
    INSERT INTO chunks_fts(chunks_fts, rowid, book_title, text) VALUES('delete', old.id, old.book_title, old.text);
    INSERT INTO chunks_fts(rowid, book_title, text) VALUES (new.id, new.book_title, new.text);
END;
```

### 4.2. Chi tiết Lược đồ CSDL Hội thoại (`history.db`)

```sql
-- 1. Bảng phiên hội thoại đa lượt
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,                       -- UUID định danh phiên
    title TEXT NOT NULL,                       -- Tiêu đề phiên hội thoại
    title_mode TEXT NOT NULL DEFAULT 'auto',   -- 'auto' (máy sinh) hoặc 'manual' (người dùng đổi)
    summary TEXT,                              -- Tóm tắt nội dung chính của phiên
    summary_status TEXT NOT NULL DEFAULT 'none',-- 'none', 'pending', 'completed'
    summarized_revision INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,                  -- Thời gian tạo ISO 8601
    updated_at TEXT NOT NULL,                  -- Thời gian cập nhật gần nhất
    revision INTEGER NOT NULL DEFAULT 1,       -- Phiên bản sửa đổi của phiên
    is_legacy INTEGER NOT NULL DEFAULT 0
);

-- 2. Bảng chi tiết các lượt hỏi đáp trong phiên
CREATE TABLE session_turns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    turn_index INTEGER NOT NULL,               -- Thứ tự lượt trong phiên (0, 1, 2...)
    question TEXT NOT NULL,                    -- Nội dung câu hỏi của người dùng
    answer TEXT NOT NULL,                      -- Câu trả lời hoàn chỉnh của trợ lý
    citations_json TEXT NOT NULL,              -- Danh sách trích dẫn nguồn JSON ([S1], [S2]...)
    model TEXT NOT NULL,                       -- Mô hình đã thực thi suy luận
    created_at TEXT NOT NULL,                  -- Thời gian hoàn thành ISO 8601
    request_id TEXT,                           -- ID yêu cầu phía client để kiểm tra idempotency
    legacy_search_id INTEGER,
    UNIQUE(session_id, turn_index),
    UNIQUE(session_id, request_id)
);
```

### 4.3. Chi tiết Lược đồ CSDL Thời khóa biểu (`timetable.db`)

```sql
-- 1. Bảng lưu trữ bản nháp trích xuất từ ảnh
CREATE TABLE timetable_drafts (
    draft_id TEXT PRIMARY KEY,                 -- UUID định danh bản nháp
    image_hash TEXT NOT NULL,                  -- Mã băm SHA-256 của ảnh gốc
    filename TEXT NOT NULL,                    -- Tên file ảnh tải lên
    created_at TEXT NOT NULL,                  -- Thời điểm trích xuất
    status TEXT NOT NULL,                      -- 'draft' hoặc 'confirmed'
    raw_model_output TEXT,                     -- Chuỗi JSON thô từ mô hình VLM
    entries_json TEXT NOT NULL,                -- Danh sách môn học dạng JSON
    uncertainties_json TEXT NOT NULL,          -- Danh sách các cảnh báo nghi vấn dạng JSON
    model_digest TEXT,                         -- Mã băm trọng số mô hình VLM
    prompt_version TEXT,                       -- Phiên bản prompt trích xuất
    options_json TEXT,                         -- Tùy chọn tiền xử lý ảnh
    confirmed_at TEXT,                         -- Thời điểm người dùng nhấn xác nhận
    confirmed_entries_json TEXT                -- Dữ liệu cuối cùng sau khi người dùng sửa
);

-- 2. Bảng lưu trữ lịch học chính thức đã xác nhận
CREATE TABLE timetable_confirmed (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    draft_id TEXT,                             -- Liên kết với bản nháp (nếu trích xuất từ ảnh)
    course TEXT NOT NULL,                      -- Tên môn học
    weekday INTEGER NOT NULL,                  -- Thứ trong tuần (1 = Thứ Hai ... 7 = Chủ Nhật)
    start_time TEXT NOT NULL,                  -- Giờ bắt đầu HH:MM (ví dụ: '07:30')
    end_time TEXT NOT NULL,                    -- Giờ kết thúc HH:MM (ví dụ: '09:00')
    room TEXT,                                 -- Phòng học (ví dụ: 'A101')
    created_at TEXT NOT NULL
);

-- 3. Bảng cache kết quả mô hình VLM
CREATE TABLE timetable_vlm_cache (
    cache_key TEXT PRIMARY KEY,                -- image_hash:model_digest:prompt_version
    image_hash TEXT NOT NULL,
    model_digest TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    response_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
```

---

## 5. RANH GIỚI MÔI TRƯỜNG VÀ PHẦN CỨNG

### 5.1. So sánh Ranh giới Windows 10/11 vs macOS Apple Silicon

Hệ thống Study Agent được thiết kế với sự phân chia trách nhiệm môi trường rõ ràng giữa các thành viên trong nhóm dự án (theo tài liệu `docs/team/PHAN_CONG_6_NGUOI.md`):

| Tiêu chí so sánh | Môi trường Windows 10/11 64-bit | Môi trường macOS Apple Silicon (M-series) |
| :--- | :--- | :--- |
| **Vai trò thành viên** | **TV1, TV2, TV3, TV5, TV6** (5 thành viên) | **TV4** (1 thành viên - Điều phối kỹ thuật) |
| **Phạm vi nghiệp vụ** | Tra cứu tài liệu, Hỏi đáp QA, Thời khóa biểu, Giao diện chung, Kiểm thử & Nghiệm thu. | Quản lý kho nguồn, Hợp nhất chỉ mục chính, Chuẩn bị dữ liệu và Huấn luyện mô hình MLX LoRA. |
| **Runtime Python** | Python 3.12 trong môi trường ảo `.venv`. | Python 3.12 cho Web Runtime và **Python 3.13** trong `.train-venv` cho MLX. |
| **Mô hình suy luận** | Chạy qua **Ollama Windows** (`qwen2.5:3b`, `bge-m3`, `qwen2.5vl:3b`). | Chạy qua **Ollama Mac** hoặc **Native MLX Engine** (`qwen2.5-3b-4bit`). |
| **Khóa tệp (File Lock)** | Native Win32 API `LockFileEx` / `UnlockFileEx` qua `ctypes` (`app/file_lock.py`). | POSIX `fcntl.flock` native của nhân Unix / Darwin. |
| **Huấn luyện mô hình** | **Bị chặn có chủ đích** trong `run.py` (báo lỗi giải thích rõ ràng nếu cố tình chạy lệnh `train`). | Hỗ trợ đầy đủ qua `mlx-lm`, `app/fine_tune.py`. |
| **Nhận diện OCR bảng** | Sử dụng VLM Ollama hoặc Tesseract OCR (tùy chọn). | Tích hợp thêm **Apple Vision OCR Native** qua script Swift (`scripts/apple_vision_ocr.swift`). |

### 5.2. Cơ chế Điều phối Tài nguyên GPU và Bộ nhớ (16GB RAM Profile)
Để đảm bảo ứng dụng không làm treo máy trạm cá nhân khi chạy các mô hình AI lớn:
1. **Kiểm tra trước khi chạy (Preflight Checks):**
   - Trước khi suy luận hoặc huấn luyện, hệ thống gọi `LiveMemoryMonitor` trong `app/memory_preflight.py` để đo đạc bộ nhớ còn trống.
   - Nếu bộ nhớ không đủ ngưỡng an toàn, hệ thống từ chối thực thi thay vì để hệ điều hành kích hoạt cơ chế OOM Killer.
2. **Trục xuất mô hình cư trú (Model Eviction):**
   - Khi tiến trình huấn luyện MLX chuẩn bị khởi động trên Mac, `gpu_coordinator` gửi lệnh POST tới Ollama với tham số `keep_alive: 0` để giải phóng toàn bộ mô hình chat/vision đang chiếm giữ VRAM.
   - Hệ thống liên tục thăm dò endpoint `/api/ps` cho đến khi xác nhận danh sách mô hình đang nạp là rỗng hoàn toàn mới bắt đầu huấn luyện.
3. **Cờ `keep_alive: "0s"` cho Vision VLM:**
   - Khi người dùng gửi ảnh thời khóa biểu, request gọi mô hình `qwen2.5vl:3b` được gắn cờ `keep_alive: "0s"`. Ngay sau khi trả về kết quả JSON, mô hình thị giác lập tức được giải phóng khỏi bộ nhớ để nhường chỗ cho mô hình chat `qwen2.5:3b`.
