import json
from pathlib import Path
import pytest


def test_registered_table_recovers_every_lecture_and_practical_session():
    from app.timetable_table import parse_registered_table
    root=Path('data/evaluation/user-feedback-20261005')
    lines=json.loads((root/'hk3-apple-ocr-live.json').read_text())['lines']
    expected=json.loads((root/'hk3-oracle.json').read_text())
    # Independent OCR corroboration for the three visually ambiguous room glyphs.
    corrected={'(1.44)':'(I.44)','(1.11E)':'(I.11E)','(1.52)':'(I.52)'}
    result=parse_registered_table(lines, room_reader=lambda l:corrected.get(l['text'],l['text']))
    assert result is not None
    actual=[{k:e.get(k) for k in ('course','weekday','start_time','end_time','room')} for e in result['entries'] if e['start_time']]
    assert actual==expected['expected_scheduled']
    unscheduled=[e for e in result['entries'] if not e['start_time']]
    assert len(unscheduled)==1 and unscheduled[0]['course']==expected['unscheduled_course']
    assert unscheduled[0]['weekday'] is None and unscheduled[0]['end_time'] is None
    assert any('1.44' in u and 'I.44' in u for u in result['uncertainties'])


def test_unknown_layout_does_not_invent_a_registered_table():
    from app.timetable_table import parse_registered_table
    assert parse_registered_table([{'text':'Monday 08:00 Math','bounds':[0.1,0.5,0.8,0.1]}]) is None


def test_ambiguous_or_invalid_clock_time_is_not_silently_scheduled():
    from app.timetable_table import parse_registered_table
    lines=json.loads(Path('data/evaluation/user-feedback-20261005/hk3-apple-ocr-live.json').read_text())['lines']
    for line in lines:
        if line['text']=='T5 07:30-': line['text']='T5 27:30-'
    result=parse_registered_table(lines)
    course=[r for r in result['entries'] if r['course']=='Kinh tế đại cương'][0]
    assert course['start_time'] is None and course['end_time'] is None
    assert result['uncertainties']
