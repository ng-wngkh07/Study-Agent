"""Select 16 diverse substantive excerpts from knowledge_base.db
across 6 domains and save for drafting.
"""

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
    FROZEN_HOLDOUT_BOOKS,
    assign_group_partition,
    extract_complete_source_text,
    segment_text_into_sentences
)

TARGET_SPECS = [
    # 1. Cognition (3)
    {"domain": "cognition", "book": "5600-tu-duy-nhanh-va-cham-pdf-khoahoctamlinh.vn.pdf", "min_page": 20, "max_page": 100},
    {"domain": "cognition", "book": "phi_ly_tri.pdf", "min_page": 15, "max_page": 80},
    {"domain": "cognition", "book": "E. Bruce Goldstein (2008, 2005) - Cognitive Psychology Connecting Mind, Research, and Everyday Experience (Second Edition).pdf", "min_page": 20, "max_page": 120},
    # 2. Learning / Habit (3)
    {"domain": "learning", "book": "5446-suc-manh-cua-thoi-quen-pdf-khoahoctamlinh.vn.pdf", "min_page": 15, "max_page": 50},
    {"domain": "learning", "book": "5446-suc-manh-cua-thoi-quen-pdf-khoahoctamlinh.vn.pdf", "min_page": 60, "max_page": 110},
    {"domain": "learning", "book": "5446-suc-manh-cua-thoi-quen-pdf-khoahoctamlinh.vn.pdf", "min_page": 130, "max_page": 190},
    # 3. Social (2)
    {"domain": "social", "book": "Amir Levine, M.D., & Rachel Heller, M.A. (2010) - Attached The New Science of Adult Attachment and How It Can Help You Find and Keep Love.pdf", "min_page": 20, "max_page": 60},
    {"domain": "social", "book": "Amir Levine, M.D., & Rachel Heller, M.A. (2010) - Attached The New Science of Adult Attachment and How It Can Help You Find and Keep Love.pdf", "min_page": 70, "max_page": 140},
    # 4. Personality (3)
    {"domain": "personality", "book": "Gregory J. Feist, Tomi-Ann Roberts & Jess Feist (2021) - Theories of Personality (Tenth Edition).pdf", "min_page": 25, "max_page": 90},
    {"domain": "personality", "book": "Gregory J. Feist, Tomi-Ann Roberts & Jess Feist (2021) - Theories of Personality (Tenth Edition).pdf", "min_page": 100, "max_page": 200},
    {"domain": "personality", "book": "Carol Dweck (2006, 2016) - Mindset The New Psychology of Success.pdf", "min_page": 20, "max_page": 80},
    # 5. Clinical (3)
    {"domain": "clinical", "book": "473711314-Tam-lý-học-dị-thường-va-lam-sang-Paul-Bennett-pdf.pdf", "min_page": 20, "max_page": 80},
    {"domain": "clinical", "book": "The Body Keeps the Score Brain, Mind,  Body in the Healing of Trauma_Bessel van der Kolk_2014.pdf", "min_page": 30, "max_page": 100},
    {"domain": "clinical", "book": "di-tim-le-song-viktor-emil-frankl.pdf", "min_page": 15, "max_page": 70},
    # 6. Research Methods / Neuroscience (2)
    {"domain": "research_methods", "book": "Elizabeth A. Phelps, Elliot Berkman, Michael Gazzaniga, Diane Halpern (2022) - Psychological Science (Seventh Edition).pdf", "min_page": 25, "max_page": 90},
    {"domain": "research_methods", "book": "Hal Blumenfeld (2022, 2010, 2002) - Neuroanatomy through Clinical Cases (3rd Edition).pdf", "min_page": 35, "max_page": 110},
]

def select_excerpts():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    selected = []
    seen_chunk_ids = set()

    for idx, spec in enumerate(TARGET_SPECS, 1):
        book = spec["book"]
        min_p = spec["min_page"]
        max_p = spec["max_page"]
        domain = spec["domain"]

        query = """
            SELECT c.id, c.doc_id, c.book_title, c.filename, c.page_num, c.chunk_index, c.text
            FROM chunks c
            WHERE c.filename = ? AND c.page_num >= ? AND c.page_num <= ?
              AND LENGTH(c.text) >= 450 AND LENGTH(c.text) <= 1000
            ORDER BY c.page_num ASC, c.chunk_index ASC
        """
        c.execute(query, (book, min_p, max_p))
        rows = c.fetchall()

        found = False
        for r in rows:
            if r["id"] in seen_chunk_ids:
                continue
            text = extract_complete_source_text(r["text"], max_chars=850)
            if len(text) < 350 or is_truncated_source_text(text):
                continue
            is_sub, reason = is_substantive_psychology_source(text)
            if not is_sub:
                continue

            sents = segment_text_into_sentences(text, prefix="S1")
            if len(sents) < 3:
                continue

            seen_chunk_ids.add(r["id"])
            source_id = f"src-{r['filename'][:12]}-{r['id']}"
            source_sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
            partition = assign_group_partition(r["filename"], r["page_num"])

            selected.append({
                "index": idx,
                "domain": domain,
                "source_id": source_id,
                "chunk_id": r["id"],
                "book": r["filename"],
                "book_title": r["book_title"],
                "page": r["page_num"],
                "text": text,
                "source_sha256": source_sha,
                "partition": partition,
                "sentence_count": len(sents),
                "sentences": sents
            })
            found = True
            break

        if not found:
            print(f"WARNING: Could not find suitable chunk for spec {idx}: {spec}")

    out_file = BASE_DIR / "data" / "training" / "v7_pending_review" / "sampled_16_sources.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(selected, f, ensure_ascii=False, indent=2)

    print(f"Successfully selected {len(selected)} substantive excerpts. Saved to {out_file}")

if __name__ == "__main__":
    select_excerpts()
