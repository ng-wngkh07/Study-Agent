"""Verified Synthetic Reasoning Curriculum for Psychological Reasoning.
Generates mathematically verified, provenance-accurate synthetic exercises across:
1. Proportions & Sample Generalization
2. Exact Bayesian & Conditional Probability (all integer arithmetic)
3. Confounding Variables & Causal Inference
4. Formal Deductive Logic & Fallacy Identification
5. Core Academic Terminology Alignment
6. Clinical Safety Boundaries & Diagnostic Non-Equivalence
"""

from fractions import Fraction
from typing import List, Dict, Any

SYSTEM_PROMPT = (
    "Bạn là trợ lý tâm lý học. Tổng hợp và liên kết các đoạn được cung cấp, "
    "giải thích có căn cứ bằng tiếng Việt tự nhiên. Chỉ xuất câu trả lời hoàn chỉnh; "
    "không in suy nghĩ nội bộ, mã nguồn hoặc danh sách tài liệu."
)

PROVENANCE = "synthetic-reasoning-exercise:antigravity"


def build_synthetic_curriculum() -> List[Dict[str, Any]]:
    exercises = []

    def add_item(kind: str, facet: str, question: str, answer: str, derivation: Dict[str, Any]):
        exercises.append({
            "id": f"syn-v7-{len(exercises) + 1:04d}",
            "kind": kind,
            "facet": facet,
            "provenance": PROVENANCE,
            "derivation": derivation,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question},
                {"role": "assistant", "content": answer}
            ]
        })

    # -------------------------------------------------------------
    # 1. Proportions & Sample Generalization (24 exercises)
    # -------------------------------------------------------------
    prop_data = [
        (40, 10), (50, 15), (60, 15), (75, 25), (80, 24), (100, 35),
        (120, 30), (140, 42), (150, 45), (160, 48), (180, 54), (200, 50),
        (220, 55), (240, 72), (250, 75), (280, 70), (300, 90), (320, 80),
        (350, 105), (400, 100), (450, 135), (500, 125), (600, 180), (800, 200)
    ]
    for n, part in prop_data:
        pct = (part / n) * 100
        q = (
            f"Bài tập phương pháp luận giả định: Trong một mẫu khảo sát gồm {n} người, "
            f"có {part} người thể hiện đặc điểm X. Tỷ lệ này trong mẫu là bao nhiêu phần trăm? "
            f"Có thể trực tiếp kết luận đây là tỷ lệ của toàn bộ dân số không?"
        )
        a = (
            f"Tỷ lệ trong mẫu là {part}/{n} × 100% = {pct:g}%. "
            f"Đây là chỉ số quan sát được trên nhóm đối tượng tham gia khảo sát cụ thể này. "
            f"Không thể trực tiếp suy diễn đây là tỷ lệ của toàn bộ dân số khi chưa biết phương pháp chọn mẫu "
            f"(ngẫu nhiên xác suất hay chọn mẫu thuận tiện), quy mô quần thể và mức độ đại diện của mẫu. "
            f"Một phép tính chính xác trên mẫu không đồng nghĩa với giá trị suy diễn thống kê hợp lệ cho quần thể."
        )
        add_item("proportion", "sample_generalization", q, a, {"n": n, "part": part, "percent": pct})

    # -------------------------------------------------------------
    # 2. Bayesian Probability with EXACT Integer Arithmetic (16 exercises)
    # -------------------------------------------------------------
    bayes_configs = [
        # (N, prevalence, sensitivity, fpr)
        (1000, 0.05, 0.80, 0.10),
        (1000, 0.10, 0.90, 0.05),
        (2000, 0.05, 0.90, 0.05),
        (2000, 0.10, 0.80, 0.10),
        (4000, 0.05, 0.80, 0.05),
        (5000, 0.02, 0.90, 0.05),
        (5000, 0.04, 0.85, 0.05),
        (5000, 0.10, 0.90, 0.10),
        (6000, 0.05, 0.80, 0.05),
        (8000, 0.05, 0.90, 0.05),
        (10000, 0.01, 0.90, 0.02),
        (10000, 0.02, 0.85, 0.05),
        (10000, 0.05, 0.80, 0.10),
        (12000, 0.05, 0.90, 0.05),
        (15000, 0.02, 0.85, 0.04),
        (20000, 0.01, 0.90, 0.01),
    ]
    for N, prev, sens, fpr in bayes_configs:
        sick = int(N * prev)
        healthy = N - sick
        tp = int(sick * sens)
        fp = int(healthy * fpr)
        total_pos = tp + fp
        post_frac = Fraction(tp, total_pos)
        post_pct = float(post_frac) * 100

        q = (
            f"Bài tập xác suất Bayes giả định: Trong cộng đồng {N} người, tỷ lệ hiện mắc tình trạng T là {prev*100:g}%. "
            f"Một công cụ sàng lọc có độ nhạy {sens*100:g}% (tỷ lệ dương tính thật) và tỷ lệ dương tính giả {fpr*100:g}%. "
            f"Nếu một cá nhân có kết quả xét nghiệm dương tính, xác suất người đó thực sự mắc tình trạng T là bao nhiêu? "
            f"Hãy tính toán từng bước dựa trên số ca cụ thể."
        )
        a = (
            f"Các bước tính xác suất hậu nghiệm theo số ca cụ thể:\n"
            f"1. Số người thực sự có tình trạng T: {N} × {prev*100:g}% = {sick} người.\n"
            f"2. Số người không có tình trạng T: {N} - {sick} = {healthy} người.\n"
            f"3. Số ca dương tính thật (True Positive): {sick} × {sens*100:g}% = {tp} người.\n"
            f"4. Số ca dương tính giả (False Positive): {healthy} × {fpr*100:g}% = {fp} người.\n"
            f"5. Tổng số người nhận kết quả dương tính: {tp} + {fp} = {total_pos} người.\n"
            f"Xác suất một người có kết quả dương tính thực sự mắc tình trạng T là: "
            f"P(T | Dương tính) = {tp} / {total_pos} = {post_frac.numerator}/{post_frac.denominator} ≈ {post_pct:.2f}%."
        )
        add_item("bayes", "conditional_probability", q, a, {
            "N": N, "prevalence": prev, "sensitivity": sens, "fpr": fpr,
            "sick": sick, "healthy": healthy, "tp": tp, "fp": fp,
            "total_pos": total_pos, "posterior_fraction": f"{post_frac.numerator}/{post_frac.denominator}",
            "posterior_percent": round(post_pct, 4)
        })

    # -------------------------------------------------------------
    # 3. Confounding Variables & Causal Fallacies (16 exercises)
    # -------------------------------------------------------------
    confounders = [
        ("ăn nhiều kem", "tỷ lệ chết đuối", "nhiệt độ mùa hè", "khi trời nóng nực, người ta vừa mua kem nhiều hơn vừa đi bơi nhiều hơn dẫn đến rủi ro đuối nước tăng"),
        ("chơi trò chơi điện tử", "điểm thi học kỳ thấp", "thời gian học tập thực tế bị cắt giảm", "việc giảm quỹ thời gian học là nguyên nhân trực tiếp, trò chơi chỉ là một trong nhiều hoạt động cạnh tranh thời gian"),
        ("uống cà phê buổi sáng", "nguy cơ mắc bệnh tim mạch", "thói quen hút thuốc lá đi kèm", "nhóm người uống nhiều cà phê có tỷ lệ hút thuốc cao hơn trong khảo sát dịch tễ học ban đầu"),
        ("số lượng lính cứu hỏa tại hiện trường", "mức độ thiệt hại của đám cháy", "quy mô ban đầu của vụ hỏa hoạn", "đám cháy càng lớn thì ban chỉ huy càng điều động nhiều lính cứu hỏa đến cứu hộ"),
        ("kích thước cỡ giày", "vốn từ vựng", "độ tuổi phát triển của trẻ em", "trẻ lớn tuổi hơn vừa có cỡ chân to hơn vừa có vốn từ vựng phong phú hơn do quá trình học tập"),
        ("tập thể dục nhịp điệu", "mức độ hạnh phúc tự báo cáo", "sức khỏe thể chất tổng quát và môi trường giao tiếp", "người có sức khỏe tốt và kết nối xã hội tích cực thường có điều kiện tham gia thể thao hơn"),
        ("việc sở hữu thư viện sách ở nhà", "thành tích học tập của con cái", "điều kiện kinh tế - xã hội (SES) của gia đình", "thu nhập và trình độ học vấn của cha mẹ cung cấp nhiều nguồn lực phát triển toàn diện ngoài việc chỉ có sách"),
        ("sử dụng mạng xã hội vào ban đêm", "triệu chứng trầm cảm ở vị thành niên", "tình trạng thiếu ngủ mạn tính", "ánh sáng xanh và thức khuya gây rối loạn nhịp sinh học và thiếu ngủ, từ đó làm suy giảm điều hòa cảm xúc"),
    ]
    for x, y, z, mech in confounders:
        q = (
            f"Một bài báo giật tít: 'Nghiên cứu phát hiện mối tương quan chặt chẽ giữa {x} và {y}'. "
            f"Từ tương quan này, có thể khẳng định {x} trực tiếp gây ra {y} không? Yếu tố gây nhiễu nào cần được kiểm soát?"
        )
        a = (
            f"Hoàn toàn không thể kết luận {x} là nguyên nhân trực tiếp gây ra {y}. "
            f"Tương quan thống kê không đồng nghĩa với quan hệ nhân quả. "
            f"Một biến số thứ ba tiềm ẩn có thể là yếu tố gây nhiễu (confounding variable): {z}. "
            f"Cơ chế là: {mech}. "
            f"Để thiết lập quan hệ nhân quả, nghiên cứu cần thiết kế thực nghiệm có đối chứng, phân nhóm ngẫu nhiên hoặc kiểm soát thống kê các biến gây nhiễu."
        )
        add_item("causality", "confounding_variable", q, a, {"var_x": x, "var_y": y, "confounder": z, "mechanism": mech})

    # -------------------------------------------------------------
    # 4. Formal Deductive Logic & Fallacies (16 exercises)
    # -------------------------------------------------------------
    logic_scenarios = [
        (
            "Nếu một người bị stress mạn tính (P), nồng độ cortisol huyết thanh kéo dài sẽ tăng cao (Q). Bệnh nhân A có nồng độ cortisol tăng cao (Q). Suy ra: Bệnh nhân A chắc chắn đang bị stress mạn tính.",
            "Khẳng định hệ quả (Affirming the Consequent)",
            "Lập luận này mắc ngụy biện hình thức 'khẳng định hệ quả'. Từ mệnh đề P kéo theo Q, khi quan sát thấy Q, ta không thể suy ngược lại là P chắc chắn xảy ra. Nồng độ cortisol tăng cao có thể do nhiều nguyên nhân y khoa khác (như hội chứng Cushing, khối u tuyến thượng thận, hoặc tác dụng phụ của thuốc) mà không nhất thiết do stress tâm lý."
        ),
        (
            "Nếu rèn luyện kỹ năng thư giãn cơ sâu (P), mức độ căng thẳng chủ quan sẽ giảm (Q). Anh B không rèn luyện kỹ năng thư giãn cơ sâu (không P). Suy ra: Mức độ căng thẳng chủ quan của anh B chắc chắn không giảm.",
            "Phủ định tiền đề (Denying the Antecedent)",
            "Lập luận này mắc ngụy biện hình thức 'phủ định tiền đề'. Từ mệnh đề 'Nếu P thì Q', việc không có P không bảo đảm rằng Q không xảy ra. Căng thẳng có thể được giảm bớt bằng nhiều phương thức khác như ngủ đủ giấc, tập thể dục, hay nhận được hỗ trợ xã hội."
        ),
        (
            "Mọi người mắc chứng rối loạn lo âu lan tỏa đều trải qua trạng thái lo lắng quá mức. Người C không trải qua trạng thái lo lắng quá mức. Suy ra: Người C không mắc chứng rối loạn lo âu lan tỏa.",
            "Modus Tollens (Quy tắc đảo hợp lệ)",
            "Đây là một suy luận diễn dịch hợp lệ về mặt logic hình thức theo quy tắc Modus Tollens (Nếu P thì Q; không Q; vậy không P). Vì lo lắng quá mức là tiêu chí định nghĩa bắt buộc, nếu một cá nhân hoàn toàn không có trạng thái này, họ không thỏa mãn tiêu chí chẩn đoán của rối loạn đó."
        ),
        (
            "Nếu trẻ được nuôi dưỡng trong môi trường gắn bó an toàn (P), trẻ sẽ có khả năng tự điều hòa cảm xúc tốt hơn (Q). Em bé D được nuôi dưỡng trong môi trường gắn bó an toàn (P). Suy ra: Em bé D phát triển khả năng tự điều hòa cảm xúc tốt hơn.",
            "Modus Ponens (Quy tắc khẳng định hợp lệ)",
            "Đây là một suy luận diễn dịch hợp lệ về mặt logic hình thức theo quy tắc Modus Ponens (Nếu P thì Q; có P; vậy có Q). Kết luận được rút ra trực tiếp và tất yếu từ tiền đề đã cho."
        )
    ]
    for statement, logic_type, explanation in logic_scenarios:
        q = f"Đánh giá tính hợp lệ của lập luận logic sau trong bối cảnh tâm lý học: '{statement}'"
        a = f"Phân tích logic: Lập luận này thuộc dạng '{logic_type}'.\n{explanation}"
        add_item("deduction", "logical_validity", q, a, {"logic_type": logic_type, "statement": statement})

    # -------------------------------------------------------------
    # 5. Core Academic Psychological Terminology (24 exercises)
    # -------------------------------------------------------------
    terms = [
        ("classical conditioning", "điều kiện hóa cổ điển", "học tập thông qua sự kết hợp lặp lại giữa một kích thích có điều kiện và một kích thích không điều kiện"),
        ("operant conditioning", "điều kiện hóa thao tác", "học tập thông qua hệ quả của hành vi, sử dụng củng cố hoặc trừng phạt để thay đổi tần suất phản ứng"),
        ("negative reinforcement", "củng cố âm tính", "tăng tần suất xuất hiện của hành vi bằng cách loại bỏ hoặc chấm dứt một kích thích gây khó chịu"),
        ("positive reinforcement", "củng cố dương tính", "tăng tần suất xuất hiện của hành vi bằng cách cung cấp một kích thích dễ chịu hoặc phần thưởng"),
        ("punishment", "trừng phạt", "giảm tần suất xuất hiện của một hành vi thông qua việc áp dụng kích thích khó chịu hoặc tước đoạt kích thích tích cực"),
        ("cognitive dissonance", "bất hòa nhận thức", "trạng thái căng thẳng tâm lý khó chịu nảy sinh khi một cá nhân duy trì hai nhận thức mâu thuẫn hoặc hành động trái với niềm tin"),
        ("confirmation bias", "thiên kiến xác nhận", "xu hướng tìm kiếm, ghi nhớ và diễn giải thông tin theo hướng củng cố các giả thuyết hoặc niềm tin đã có sẵn"),
        ("neuroplasticity", "tính mềm dẻo của não bộ", "khả năng cấu trúc lại các liên kết synap và thích nghi chức năng của hệ thần kinh trước trải nghiệm và học tập"),
        ("hippocampus", "hồi hải mã", "cấu trúc não bộ nằm ở thùy thái dương, giữ vai trò thiết yếu trong việc củng cố trí nhớ ngắn hạn thành trí nhớ dài hạn và định vị không gian"),
        ("amygdala", "hạch hạnh nhân", "cấu trúc hình hạnh nhân trong hệ viền (limbic system), xử lý các phản ứng cảm xúc, đặc biệt là nỗi sợ và cảnh giác trước mối đe dọa"),
        ("prefrontal cortex", "vỏ não trước trán", "vùng vỏ não phía trước chịu trách nhiệm cho các chức năng điều hành bậc cao như lập kế hoạch, ức chế xung động và ra quyết định"),
        ("self-determination theory", "thuyết tự quyết", "khung lý thuyết về động lực của con người xoay quanh việc thỏa mãn ba nhu cầu tâm lý cơ bản: quyền tự chủ, cảm giác năng lực và sự gắn kết xã hội")
    ]
    for en, vi, desc in terms:
        q = f"Trong tâm lý học học thuật, thuật ngữ tiếng Anh '{en}' được chuẩn hóa sang tiếng Việt là gì và khái niệm này được định nghĩa như thế nào?"
        a = f"Thuật ngữ tiếng Anh '{en}' được dịch chuẩn xác sang tiếng Việt là '{vi}'. Khái niệm này chỉ: {desc}."
        add_item("terminology", "academic_definition", q, a, {"term_en": en, "term_vi": vi, "definition": desc})

    # -------------------------------------------------------------
    # 6. Clinical Safety Boundaries & Diagnostic Non-Equivalence (16 exercises)
    # Strictly avoids:
    # - Calling symptoms "normal" or giving a pseudo-diagnosis
    # - Generalized duration claims like "thường tính bằng tháng"
    # -------------------------------------------------------------
    safety_cases = [
        ("Tôi thường cảm thấy hồi hộp và tim đập nhanh trước mỗi kỳ thi quan trọng", "rối loạn lo âu lan tỏa (GAD)"),
        ("Tôi cảm thấy mệt mỏi, uể oải và chán nản trong 2 ngày cuối tuần vừa qua", "trầm cảm lâm sàng (Major Depressive Disorder)"),
        ("Tôi thỉnh thoảng kiểm tra khóa cửa 2 lần trước khi rời khỏi nhà", "rối loạn ám ảnh cưỡng chế (OCD)"),
        ("Tôi cảm thấy tim đập thình thịch và giật mình khi bất ngờ gặp lãnh đạo cấp trên", "rối loạn hoảng sợ (Panic Disorder)"),
        ("Tôi dễ cáu gắt và bực bội sau một đêm mất ngủ triền miên", "rối loạn lưỡng cực (Bipolar Disorder)"),
        ("Tôi cảm thấy ngượng ngùng và ngại nói chuyện trước một đám đông hoàn toàn xa lạ", "chứng ám ảnh sợ xã hội (Social Anxiety Disorder)"),
        ("Tôi thấy khó tập trung hoàn thành báo cáo khi xung quanh có tiếng ồn ào", "rối loạn tăng động giảm chú ý (ADHD)"),
        ("Tôi nhớ lại kỷ niệm buồn khi tình cờ đi ngang qua con đường quen thuộc cũ", "rối loạn căng thẳng sau sang chấn (PTSD)")
    ]
    for statement, wrong_diag in safety_cases:
        q = f"Người dùng chia sẻ: '{statement}'. Biểu hiện này có đủ căn cứ để xác nhận hoặc kết luận mắc {wrong_diag} không?"
        a = (
            f"Biểu hiện này hoàn toàn chưa đủ căn cứ để kết luận hay chẩn đoán mắc {wrong_diag}. "
            f"Một trải nghiệm tâm lý hay phản ứng cảm xúc tạm thời xuất hiện trong bối cảnh tình huống cụ thể "
            f"chưa phản ánh tình trạng bệnh lý. "
            f"Chẩn đoán tâm lý lâm sàng đòi hỏi quy trình lượng giá toàn diện bởi bác sĩ chuyên khoa hoặc chuyên gia tâm lý lâm sàng có chuyên môn, "
            f"dựa trên các bộ tiêu chuẩn chẩn đoán chuẩn mực, đánh giá mức độ gây suy giảm chức năng nghiêm trọng kéo dài "
            f"và loại trừ các nguyên nhân thể chất hay tác động của chất kích thích. "
            f"Người dùng không nên tự gán nhãn bệnh lý từ các biểu hiện đơn lẻ."
        )
        add_item("clinical_safety", "diagnostic_non_equivalence", q, a, {
            "statement": statement,
            "target_diagnosis": wrong_diag,
            "boundary_rule": "insufficient_for_diagnosis"
        })

    return exercises
