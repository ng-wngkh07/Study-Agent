"""Find exact 16 substantive, non-holdout chunks with rich psychology content."""

import sqlite3
import json
import hashlib
import sys
from pathlib import Path

BASE_DIR_PATH = Path(__file__).resolve().parent.parent
if str(BASE_DIR_PATH) not in sys.path:
    sys.path.insert(0, str(BASE_DIR_PATH))

from app.config import BASE_DIR, DB_PATH
from app.curate_dataset_v7 import (
    is_substantive_psychology_source,
    is_truncated_source_text,
    extract_complete_source_text,
    segment_text_into_sentences,
    assign_group_partition
)

TARGET_SPECS = [
    # 1. Cognition: Kahneman (mental effort / pupil dilation during Add-1)
    {"domain": "cognition", "book": "5600-tu-duy-nhanh-va-cham-pdf-khoahoctamlinh.vn.pdf", "page_start": 40, "page_end": 50, "topic": "Kahneman Attention & Mental Effort"},
    # 2. Cognition: Ariely (decoy effect in Economist pricing)
    {"domain": "cognition", "book": "phi_ly_tri.pdf", "page_start": 15, "page_end": 25, "topic": "Ariely Decoy Effect"},
    # 3. Cognition: Goldstein (selective attention / dichotic listening)
    {"domain": "cognition", "book": "E. Bruce Goldstein (2008, 2005) - Cognitive Psychology Connecting Mind, Research, and Everyday Experience (Second Edition).pdf", "page_start": 80, "page_end": 120, "topic": "Goldstein Attention"},
    
    # 4. Learning: Duhigg (dopamine craving & habit loop)
    {"domain": "learning", "book": "5446-suc-manh-cua-thoi-quen-pdf-khoahoctamlinh.vn.pdf", "page_start": 40, "page_end": 55, "topic": "Duhigg Dopamine Habit Loop"},
    # 5. Learning: Duhigg (keystone habits & organizational routines)
    {"domain": "learning", "book": "5446-suc-manh-cua-thoi-quen-pdf-khoahoctamlinh.vn.pdf", "page_start": 105, "page_end": 125, "topic": "Duhigg Keystone Habits"},
    # 6. Learning: Duhigg (willpower & self-regulation)
    {"domain": "learning", "book": "5446-suc-manh-cua-thoi-quen-pdf-khoahoctamlinh.vn.pdf", "page_start": 140, "page_end": 160, "topic": "Duhigg Willpower Muscle"},

    # 7. Social: Attached (Bowlby attachment theory history)
    {"domain": "social", "book": "Amir Levine, M.D., & Rachel Heller, M.A. (2010) - Attached The New Science of Adult Attachment and How It Can Help You Find and Keep Love.pdf", "page_start": 25, "page_end": 35, "topic": "Attached Attachment Theory Roots"},
    # 8. Social: Attached (adult attachment styles & dependency)
    {"domain": "social", "book": "Amir Levine, M.D., & Rachel Heller, M.A. (2010) - Attached The New Science of Adult Attachment and How It Can Help You Find and Keep Love.pdf", "page_start": 36, "page_end": 60, "topic": "Attached Dependency Paradox"},

    # 9. Personality: Feist (Freud provinces of mind: id, ego, superego)
    {"domain": "personality", "book": "Gregory J. Feist, Tomi-Ann Roberts & Jess Feist (2021) - Theories of Personality (Tenth Edition).pdf", "page_start": 48, "page_end": 56, "topic": "Feist Freud Structural Model"},
    # 10. Personality: Feist (Carl Rogers actualizing tendency)
    {"domain": "personality", "book": "Gregory J. Feist, Tomi-Ann Roberts & Jess Feist (2021) - Theories of Personality (Tenth Edition).pdf", "page_start": 310, "page_end": 330, "topic": "Feist Rogers Person-Centered"},
    # 11. Personality: Dweck (fixed vs growth mindset)
    {"domain": "personality", "book": "Carol Dweck (2006, 2016) - Mindset The New Psychology of Success.pdf", "page_start": 15, "page_end": 35, "topic": "Dweck Mindset Dichotomy"},

    # 12. Clinical: Paul Bennett (4 paradigms of mental health)
    {"domain": "clinical", "book": "473711314-Tam-lý-học-dị-thường-va-lam-sang-Paul-Bennett-pdf.pdf", "page_start": 35, "page_end": 42, "topic": "Bennett 4 Clinical Paradigms"},
    # 13. Clinical: Van der Kolk (trauma & limbic system)
    {"domain": "clinical", "book": "The Body Keeps the Score Brain, Mind,  Body in the Healing of Trauma_Bessel van der Kolk_2014.pdf", "page_start": 50, "page_end": 75, "topic": "Van der Kolk Trauma & Amygdala"},
    # 14. Clinical: Viktor Frankl (will to meaning & existential frustration)
    {"domain": "clinical", "book": "di-tim-le-song-viktor-emil-frankl.pdf", "page_start": 30, "page_end": 50, "topic": "Frankl Will to Meaning"},

    # 15. Research Methods: Phelps (mind, brain, behavior definition)
    {"domain": "research_methods", "book": "Elizabeth A. Phelps, Elliot Berkman, Michael Gazzaniga, Diane Halpern (2022) - Psychological Science (Seventh Edition).pdf", "page_start": 50, "page_end": 65, "topic": "Phelps Mind Brain & Behavior"},
    # 16. Research Methods: Blumenfeld (clinical case presentation & neurological exam)
    {"domain": "research_methods", "book": "Hal Blumenfeld (2022, 2010, 2002) - Neuroanatomy through Clinical Cases (3rd Edition).pdf", "page_start": 35, "page_end": 60, "topic": "Blumenfeld Neurologic Exam"},
]

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    chosen = []
    seen_ids = set()

    for idx, spec in enumerate(TARGET_SPECS, 1):
        c.execute("""
            SELECT id, filename, book_title, page_num, text
            FROM chunks
            WHERE filename = ? AND page_num BETWEEN ? AND ?
              AND LENGTH(text) BETWEEN 450 AND 1000
              AND text NOT LIKE '%thuviensach.vn%'
              AND text NOT LIKE '%http%'
            ORDER BY page_num ASC
        """, (spec["book"], spec["page_start"], spec["page_end"]))
        rows = c.fetchall()

        matched = False
        for r in rows:
            if r["id"] in seen_ids:
                continue
            text = extract_complete_source_text(r["text"], max_chars=800)
            if len(text) < 350 or is_truncated_source_text(text):
                continue
            is_sub, reason = is_substantive_psychology_source(text)
            if not is_sub:
                continue
            sents = segment_text_into_sentences(text, "S1")
            if len(sents) < 3:
                continue

            seen_ids.add(r["id"])
            source_id = f"src-{r['filename'][:12].replace(' ', '_')}-{r['id']}"
            partition = assign_group_partition(r["filename"], r["page_num"])
            source_sha = hashlib.sha256(text.encode("utf-8")).hexdigest()

            chosen.append({
                "item_index": idx,
                "domain": spec["domain"],
                "topic": spec["topic"],
                "source_id": source_id,
                "chunk_id": r["id"],
                "book": r["filename"],
                "book_title": r["book_title"],
                "page": r["page_num"],
                "partition": partition,
                "source_text": text,
                "source_sha256": source_sha,
                "sentence_count": len(sents),
                "sentences": sents
            })
            matched = True
            break

        if not matched:
            print(f"FAILED to find match for spec {idx}: {spec['topic']}")

    print(f"Matched {len(chosen)}/16 specs.")
    out_path = BASE_DIR / "data" / "training" / "v7_pending_review" / "verified_16_sources.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(chosen, f, ensure_ascii=False, indent=2)
    print(f"Saved to {out_path}")

if __name__ == "__main__":
    main()
