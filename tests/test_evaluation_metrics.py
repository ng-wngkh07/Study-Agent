from app.evaluation_metrics import citation_metrics, plain_answer_metrics, has_repetition


def test_citation_metrics_require_every_source():
    sources = {"S1", "S2"}
    one = citation_metrics("Ý thứ nhất [S1]", sources)
    both = citation_metrics("Ý thứ nhất [S1], ý thứ hai [S2]", sources)
    unknown = citation_metrics("Ý thứ nhất [S1], nguồn lạ [S3]", sources)

    assert one["citation_tags_valid"] is True
    assert one["citation_valid"] is False
    assert both["citation_valid"] is True
    assert unknown["citation_tags_valid"] is False
    assert unknown["citation_valid"] is False


def test_citation_metrics_reject_empty_citations():
    assert citation_metrics("Không dẫn nguồn", {"S1", "S2"})["citation_valid"] is False


def test_plain_answer_metrics_reject_visible_reasoning_and_sources():
    assert plain_answer_metrics("Hai dữ kiện bổ sung cho nhau.")["format_valid"]
    assert not plain_answer_metrics("Suy nghĩ <think>nội bộ</think> Đáp án.")["format_valid"]
    assert not plain_answer_metrics("Đáp án [S1].")["format_valid"]


def test_repetition_is_a_separate_quality_signal_from_format():
    repeated = "Ký ức về một sự kiện có thể thay đổi qua thời gian. " * 4
    assert plain_answer_metrics(repeated)["format_valid"]
    assert plain_answer_metrics(repeated)["repetitive"]
    assert not has_repetition("Trí nhớ làm việc giữ thông tin tạm thời. Hồi hải mã tham gia tạo ký ức mới.")
