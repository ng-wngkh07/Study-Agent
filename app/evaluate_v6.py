"""Frozen v6 transfer cases; reuse earlier outputs only for identical messages."""

import argparse
import hashlib
import json
from pathlib import Path

from app.config import MLX_MODEL_DIR
from app.evaluation_metrics import plain_answer_metrics
from app.prepare_v5 import write_json
from app.prepare_v6 import SYSTEM
from app.fine_tune import verify_auxiliary_files


def freeze(path):
    suite=json.loads(Path("data/evaluation/v5-frozen-suite.json").read_text())
    errata=json.loads(Path("data/evaluation/v5-reference-errata.json").read_text())["entries"]
    for correction in errata:
        next(c for c in suite if c["id"]==correction["case_id"])["reference"]=correction["corrected_reference"]
    fresh=[
        ("new_filter", "Có 2.500 thư; 4% là thư rác. Bộ lọc gắn cờ đúng 80% thư rác và gắn cờ nhầm 2% thư thường. Trong thư bị gắn cờ, tỷ lệ thư rác là bao nhiêu? Nêu số thư để giải thích.", "100 thư rác, 2400 thư thường; 80 đúng và 48 nhầm; 80/128=62.5%."),
        ("new_weighted", "Nhóm A có 20 người, 80% hoàn thành bài; nhóm B có 80 người, 50% hoàn thành. Tỷ lệ hoàn thành chung là bao nhiêu? Có được lấy trung bình 80% và 50% không?", "16+40=56 người trên 100; 56%; trung bình hai tỷ lệ không trọng số 65% là sai vì nhóm khác kích thước."),
        ("new_modus_tollens", "Giả sử quy tắc không có ngoại lệ: nếu Minh hoàn thành bài thì Minh nhận chứng nhận. Minh không nhận chứng nhận. Có suy ra Minh không hoàn thành bài được không? Vì sao?", "Có, theo quy tắc giả định: P=>Q và không Q suy ra không P. Không tự thêm ngoại lệ trái giả thiết."),
        ("new_explicit_subject", "Ghi chú: Đức gặp Hạnh ở thư viện. Hạnh nói rõ mình chưa đọc cuốn X. Đức đã đọc cuốn X. Ai chưa đọc X? Chỉ dùng ghi chú.", "Hạnh chưa đọc, Đức đã đọc; chủ thể rõ nên không từ chối hoặc đổi chủ thể."),
        ("new_motive", "Một người từ chối lời mời ăn tối. Chỉ biết vậy có thể nói họ ghét người mời không? Giải thích giới hạn.", "Không có chứng cứ về động cơ; nhiều khả năng, không khẳng định bất kỳ giả thuyết nào là thật."),
        ("new_negative_reinforcement", "Tiếng báo động khó chịu tắt khi người lái cài dây an toàn, và sau đó người đó cài dây thường xuyên hơn. Đây là củng cố âm tính hay trừng phạt? Giải thích theo thay đổi hành vi.", "Củng cố âm tính: loại bỏ kích thích khó chịu làm hành vi tăng; không phải trừng phạt."),
        ("new_observational_learning", "Một trẻ nhìn người lớn gấp giấy rồi thử làm theo. Có thể gọi đây là học qua quan sát không? Có phải mọi học tập đều cần được thưởng trực tiếp không?", "Ví dụ học qua quan sát/mô hình; không phải mọi học tập cần thưởng trực tiếp; không bảo đảm trẻ làm đúng ngay."),
        ("new_memory_types", "Nhớ lần sinh nhật của mình và biết cách đi xe đạp có cùng là trí nhớ tình tiết không? Phân biệt ngắn gọn.", "Sinh nhật cá nhân: tình tiết; kỹ năng đi xe: thủ tục; không đồng nhất, không bịa đoạn nguồn."),
        ("new_scope_translation", "Dịch nguyên câu sang tiếng Việt, giữ mức độ khẳng định: 'This strategy may help some learners, but it does not guarantee accurate recall for everyone.'", "Chiến lược có thể giúp một số người học; không bảo đảm nhớ lại chính xác cho mọi người. Không bỏ may/some/not/everyone."),
        ("new_cutoff_translation", "Chỉ dịch phần hiện có, không tự hoàn thành: 'The effect was observed in adults, but its duration may depend on'", "Hiệu ứng được quan sát ở người trưởng thành, nhưng thời gian kéo dài có thể phụ thuộc vào…; báo câu ngắt, không tự thêm yếu tố."),
        ("new_basic_retention", "Không có tài liệu đi kèm. Hãy cho biết thủ đô của Nhật Bản và kết quả 7 nhân 8. Trả lời một câu.", "Tokyo và 56; không viện dẫn đoạn đầu, không từ chối vì không có nguồn."),
        ("new_needed_evidence", "Một nhân viên báo khó tập trung trong chiều nay. Thông tin đó có đủ xác nhận ADHD không? Cần làm gì nếu khó khăn kéo dài?", "Không đủ chẩn đoán; không quy lỗi người hỏi; cần thời gian, bối cảnh/ảnh hưởng và đánh giá chuyên môn nếu kéo dài, không bịa tiêu chuẩn."),
    ]
    for name,question,reference in fresh:
        suite.append({"id":name,"kind":"new_transfer","messages":[{"role":"system","content":SYSTEM},{"role":"user","content":question}],"reference":reference})
    if path.exists() and json.loads(path.read_text())!=suite:raise ValueError("Frozen suite changed")
    write_json(path,suite)
    return suite


def evaluate(data, output, adapter=None, reuse=None):
    from mlx_lm import load, generate
    from mlx_lm.sample_utils import make_sampler
    approval=json.loads((data/"approval.json").read_text())
    data_hash=hashlib.sha256((data/"train.jsonl").read_bytes()+(data/"valid.jsonl").read_bytes()).hexdigest()
    if data_hash!=approval["dataset_sha256"]:raise ValueError("Dataset hash changed")
    verify_auxiliary_files(data,approval)
    suite=json.loads(Path("data/evaluation/v6-frozen-suite.json").read_text())
    suite_hash=hashlib.sha256(json.dumps(suite,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    reused=json.loads(reuse.read_text()) if reuse else None
    if reused and not reused.get("complete"):raise ValueError("Cannot reuse incomplete evaluation")
    cache={c["id"]:c for c in reused["cases"]} if reused else {}
    expected=adapter.name if adapter else "base-3b"
    if reused and reused["model"]!=expected:raise ValueError("Wrong model for reused outputs")
    model,tokenizer=load(str(MLX_MODEL_DIR),adapter_path=str(adapter) if adapter else None)
    result={"model":expected,"dataset_sha256":data_hash,"suite_sha256":suite_hash,"temperature":0,"max_tokens":700,
            "adapter_sha256":hashlib.sha256((adapter/"adapters.safetensors").read_bytes()).hexdigest() if adapter else None,
            "reused_output_file":str(reuse) if reuse else None,"complete":False,"cases":[]}
    for case in suite:
        old=cache.get(case["id"])
        if old:
            if old["messages"]!=case["messages"] or reused["temperature"]!=0 or reused["max_tokens"]!=700:raise ValueError("Reuse input/settings mismatch")
            answer=old["answer"];origin="reused_identical_input"
        else:
            prompt=tokenizer.apply_chat_template(case["messages"],tokenize=False,add_generation_prompt=True)
            answer=generate(model,tokenizer,prompt=prompt,max_tokens=700,sampler=make_sampler(0.0));origin="fresh_inference"
        result["cases"].append({**case,"answer":answer,"origin":origin,**plain_answer_metrics(answer)})
        write_json(output,result)
        print(f"{expected}: {len(result['cases'])}/{len(suite)} {case['id']} {origin}",flush=True)
    result["complete"]=True;write_json(output,result)


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--freeze",action="store_true");p.add_argument("--data",type=Path,default=Path("data/training/v6"));p.add_argument("--output",type=Path);p.add_argument("--adapter",type=Path);p.add_argument("--reuse",type=Path)
    a=p.parse_args()
    if a.freeze:print(len(freeze(Path("data/evaluation/v6-frozen-suite.json"))))
    else:evaluate(a.data,a.output,a.adapter,a.reuse)
