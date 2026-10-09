import re
from typing import Dict, Any, Optional, Tuple
from app.config import CRISIS_HOTLINES

# Patterns indicating suicide, self-harm, or severe psychological crisis
CRISIS_PATTERNS = [
    r"(?i)\b(tự\s*tử|tự\s*sát|kết\s*liễu|muốn\s*chết|chán\s*sống|không\s*muốn\s*sống|tự\s*hại|rạch\s*tay|uống\s*thuốc\s*ngủ|nhảy\s*lầu|treo\s*cổ)\b",
    r"(?i)\b(suicide|kill\s*myself|end\s*my\s*life|self[\s-]harm|want\s*to\s*die|cut\s*myself)\b",
    r"(?i)(cách\s*nào\s*để\s*chết|muốn\s*biến\s*mất\s*khỏi\s*thế\s*giới|không\s*còn\s*lý\s*do\s*để\s*sống)",
]

# Patterns asking the AI to diagnose, prescribe, or roleplay as a therapist
ROLEPLAY_OR_DIAGNOSIS_PATTERNS = [
    r"(?i)\b(chẩn\s*đoán|kê\s*đơn|khám\s*bệnh|điều\s*trị\s*cho\s*tôi)\b",
    r"(?i)\b(đóng\s*vai\s*(?:như\s*)?(?:là\s*)?(?:bác\s*sĩ|nhà\s*trị\s*liệu|chuyên\s*gia\s*tâm\s*lý|chuyên\s*viên))\b",
    r"(?i)\b(tôi\s*đang\s*bị\s*bệnh\s*gì|tôi\s*có\s*bị\s*(?:tâm\s*thần|trầm\s*cảm|rối\s*loạn)\s*không)\b",
    r"(?i)\b(hãy\s*là\s*nhà\s*trị\s*liệu|hãy\s*làm\s*bác\s*sĩ\s*của\s*tôi)\b",
    r"(?i)\b(act\s+as\s+(?:my\s+)?(?:therapist|doctor|psychiatrist|psychologist)|diagnose\s+me)\b",
]

class SafetyGuard:
    @classmethod
    def check_crisis(cls, user_text: str) -> Tuple[bool, Optional[str]]:
        """
        Check if the input conveys self-harm or suicide crisis.
        Returns (is_crisis, formatted_crisis_response).
        """
        if not user_text:
            return False, None
            
        for pattern in CRISIS_PATTERNS:
            if re.search(pattern, user_text):
                response = cls.build_crisis_response()
                return True, response
                
        return False, None

    @classmethod
    def check_roleplay_or_diagnosis(cls, user_text: str) -> Tuple[bool, Optional[str]]:
        """
        Check if the user is asking the AI to act as a personal clinician or diagnose medical conditions.
        """
        if not user_text:
            return False, None
            
        for pattern in ROLEPLAY_OR_DIAGNOSIS_PATTERNS:
            if re.search(pattern, user_text):
                msg = (
                    "⚠️ **Tuyên bố miễn trừ trách nhiệm y tế & tâm lý:**\n\n"
                    "Tôi là trợ lý AI học thuật tra cứu tài liệu học tập, **không phải là bác sĩ y khoa hay chuyên gia tâm lý trị liệu được cấp phép**. "
                    "Tôi **không thể đưa ra chẩn đoán y khoa, không thể kê đơn thuốc và không thực hiện trị liệu lâm sàng**.\n\n"
                    "Nếu bạn hoặc người thân đang gặp các vấn đề về sức khỏe tinh thần hoặc thể chất, xin vui lòng đến thăm khám trực tiếp tại các cơ sở y tế chuyên khoa "
                    "(như Viện Sức khỏe Tâm thần - Bệnh viện Bạch Mai, Bệnh viện Tâm thần TP.HCM) hoặc liên hệ các chuyên gia y tế/tâm lý được chứng nhận."
                )
                return True, msg
        return False, None

    @classmethod
    def build_crisis_response(cls) -> str:
        """Construct an empathetic, supportive, and immediate emergency hotline response."""
        lines = [
            "🆘 **BẠN KHÔNG PHẢI ĐỐI MẶT VỚI ĐIỀU NÀY MỘT MÌNH**",
            "",
            "Tôi nhận thấy bạn đang trải qua những cảm xúc rất khó khăn và đau đớn. "
            "Vì sự an toàn và sức khỏe của bạn là điều quan trọng nhất, tôi **không thể thay thế sự trợ giúp chuyên môn từ người thật**.",
            "",
            "Nếu bạn có thể làm hại bản thân lúc này, hãy đến nơi có người khác, tránh xa những thứ có thể dùng để tự hại, gọi 115 hoặc đến khoa cấp cứu gần nhất. Hãy nhờ một người bạn tin tưởng ở bên và giúp bạn gọi điện.",
            ""
        ]
        
        for h in CRISIS_HOTLINES:
            lines.append(f"📞 **{h['name']}**")
            lines.append(f"   • Điện thoại: **{h['phone']}**")
            lines.append(f"   • Thời gian hoạt động: {h['hours']}")
            lines.append("")
            
        lines.append("Nếu bạn không ở Việt Nam, hãy gọi số cấp cứu tại nơi bạn đang ở. Bạn có thể cho tôi biết quốc gia của mình để tìm nguồn hỗ trợ phù hợp.")
        return "\n".join(lines)
