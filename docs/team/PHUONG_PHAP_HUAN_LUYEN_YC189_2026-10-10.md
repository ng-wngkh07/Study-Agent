# Đối chiếu phương pháp huấn luyện với Agent Học Tập

Cập nhật: 10/10/2026. Phạm vi YC-189, tiếp nối YC-187/188; kết quả GitHub YC-190.

Ưu tiên hiện tại là sửa chất lượng dữ liệu và đo đúng hành vi ứng dụng. Bản nháp 216 mẫu có đủ sáu môn nhưng chưa được phép huấn luyện: chia cùng họ tài liệu vào train/valid, nhãn kiểm trắc nghiệm sai và một số đáp án bổ sung thông tin ngoài đoạn trích. Số lượng mẫu hoặc loss không giải quyết được các lỗi này.

## Nguồn nghiên cứu và quyết định áp dụng

| Phương pháp | Bằng chứng | Đối chiếu dự án và cách áp dụng |
| --- | --- | --- |
| LoRA trên base quantized, giảm nhu cầu bộ nhớ | [MLX-LM LoRA chính thức](https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/LORA.md), [bài QLoRA](https://arxiv.org/abs/2305.14314) | Máy 16 GB đang có Qwen2.5-3B-Instruct 4-bit. Giữ base và trainer MLX hiện có. Không mặc định MLX dùng NF4/paged optimizer của thí nghiệm CUDA trong bài báo. |
| Chỉ tính loss trên câu trả lời | [Mã dataset MLX-LM](https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/tuner/datasets.py), [TRL SFT](https://huggingface.co/docs/trl/en/sft_trainer) | Dự án đã có mask-prompt. Đối chiếu bản MLX-LM cài local: mask bắt đầu từ phần cuối assistant trong chat template. Cần đo token thực và bảo đảm target còn nguyên, không cắt bỏ câu trả lời để vừa giới hạn. Không chuyển sang TRL chỉ để dùng cùng ý tưởng. |
| Chọn mẫu ít nhưng đúng và đa dạng | [LIMA](https://arxiv.org/abs/2305.11206) | Bài báo trên mô hình 65B không chứng minh 144 mẫu học đủ cho mô hình 3B. Áp dụng việc kiểm từng nguồn, từng nhãn, giữ phản ví dụ và sáu nhiệm vụ; bộ nhỏ chỉ là thí nghiệm thăm dò sau nghiệm thu. |
| Chia theo nhóm nguồn thực | [GroupShuffleSplit](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupShuffleSplit.html) | Nhóm phải biểu diễn cùng sách/khóa học/bản dịch/nguồn dẫn xuất, không phải từng file hoặc từng môn. Kiểm hash PDF là cần thiết nhưng hai chương cùng sách có hash khác vẫn không độc lập. Khóa cả họ cùng một split; nhóm chưa rõ quan hệ được giữ ngoài bộ học cho đến khi xác minh. |
| Đo cả năng lực mới và năng lực cũ | [Nghiên cứu catastrophic forgetting](https://arxiv.org/abs/2308.08747) | Trial18 thật tăng target 13/20→15/20 nhưng retention 3/8→1/8; candidate bị loại. Giữ holdout cũ, bổ sung đánh giá từng chức năng trên đúng prompt/schema hiện tại; chỉ xem xét candidate khi đạt các ngưỡng và không có hồi quy nghiêm trọng. |
| Bộ nhớ nhỏ, checkpoint và đợt học ngắn | [MLX-LM](https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/LORA.md) | Giữ batch1, tối đa4 lớp, sequence1024, gradient checkpoint và learning rate do trial_plan duyệt. Giả thuyết khởi đầu là một lượt qua dữ liệu với LR1e-5; chưa chạy. Đọc lại RAM/GPU lock trước từng đợt. Không tăng số bước vì loss đang giảm. |

## Kinh nghiệm GitHub và diễn đàn

Đã đọc [thảo luận LocalLLaMA về LoRA trên Apple Silicon](https://www.reddit.com/r/LocalLLaMA/comments/18wabkc/lessons_learned_so_far_lora_fine_tuning_on/) và [issue MLX-LM #1658](https://github.com/ml-explore/mlx-lm/issues/1658). Đây là báo cáo của người sử dụng, hữu ích để đặt câu hỏi về độ ổn định và khả năng tái hiện; không phải bằng chứng một cấu hình chắc chắn tốt cho corpus này. Hướng dẫn Reddit từ năm 2024 có tên tham số cũ; dùng tên tham số và hành vi của phiên bản đã cài, không sao chép nguyên lệnh. Issue về finite-loss/clipping là đề xuất/báo cáo, không mặc định tính năng đã được phát hành. Các kết luận triển khai bên trên dựa vào tài liệu/mã chính thức và bằng chứng local.

## Tình hình thực tế đã kiểm

- Môi trường học: mlx-lm0.31.3, mlx0.32.2, transformers5.17.0 trên Python3.13. Môi trường web local Python3.14.8; GitHub CI Python3.12.
- Base được pin revision4f83f8f146fdf28b512a06562b671d7af4fab457, đã lưu SHA các file trọng số/tokenizer/config để kiểm trước chạy. Không tiếp tục từ adapter đã bị loại.
- Corpus trước bổ sung nguồn:154 tài liệu/22.705 trang, scope22.692 trang sau đúng13 ngoại lệ được người dùng duyệt. complete:true chỉ theo phạm vi này; whole-source vẫn false. Cần audit live lại sau mỗi bổ sung.
- Data03:144 train/72 valid,216 mẫu,36 đoạn nguồn×6 tác vụ. Review độc lập đủ36 đoạn: REJECT. Ví dụ source C++ gọi createNode(v) nhưng nhãn thay thành new Node(v); đoạn Rogers bị gán thành cognitive dissonance; nhiều explanation gọi câu nằm ngoài span là nguyên văn.
- Bốn ca hồi quy mới tái hiện lỗi: cờ kiểm trắc nghiệm không độc lập, thiếu yêu cầu nhãn verifier được tác giả duyệt, summary dùng PDF ngoài hội thoại runtime, chia lẫn bốn họ nguồn đã đối chiếu.
- Timetable dùng VLM riêng. LoRA văn bản bao gồm hỏi đáp có nguồn/thiếu nguồn, sinh câu hỏi, kiểm câu đúng/sai và summary; lookup, chấm điểm, lưu hội thoại và xuất lịch được kiểm qua hồi quy chức năng.

## Thay đổi đã áp dụng và phần đang làm

Đã triển khai cổng phạm vi nguồn gắn manifest/hash, kiểm admission cả train/valid và chặn nguồn/trang/alias không hợp lệ. PR8 đã sửa thiếu import annotation qua ca tái hiện độc lập; CI Windows/Mac Python3.12 PASS trên commit3c221ed. Đây là kiểm chứng mã, không phải nghiệm thu nhãn hay mô hình.

Đã giữ bản nháp bị loại và review theo từng đoạn để sửa có bằng chứng, thêm kiểm thử ngữ nghĩa tái hiện trước sửa. Hai trang nguồn vật lý MIT độc lập đã được xem toàn bộ ảnh, lưu transcript/hash; đang bổ sung có giới hạn vào canonical index với backup và kiểm bảo toàn mọi rows cũ. Nguồn kiểm tra mới không được chia lẫn với VLDC1.

Tiếp theo: sửa builder để dùng nhãn verifier riêng được duyệt cho từng trường; summary chỉ đọc bản ghi giới hạn như runtime; giữ đầy đủ phòng vệ trong prompt; chọn lại đoạn có công thức/điều kiện rõ và nguồn độc lập. Bộ đánh giá phải đóng băng trước học, pin byte đầu vào/base/tokenizer và ghi lý do dừng sinh thực, không tự gán stop khi thiếu dữ liệu. Baseline và candidate dùng cùng đầu vào, không chạy baseline trên bộ chưa duyệt.

Huấn luyện và so sánh candidate mới chưa chạy. Chỉ mở đợt thăm dò sau khi source scope, family split, nhãn, token, baseline và tài nguyên đều đạt. Chưa có cơ sở khẳng định đã cải thiện chất lượng hoặc sẵn sàng kích hoạt adapter.
