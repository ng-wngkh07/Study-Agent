"""Sample substantive, non-holdout source chunks from knowledge_base.db
across diverse psychology domains (cognition, learning, social, personality, clinical, research methods).
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
    extract_complete_source_text
)

DOMAIN_BOOKS = {
    "cognition": [
        "E. Bruce Goldstein (2008, 2005) - Cognitive Psychology Connecting Mind, Research, and Everyday Experience (Second Edition).pdf",
        "phi_ly_tri.pdf",
        "5600-tu-duy-nhanh-va-cham-pdf-khoahoctamlinh.vn.pdf"
    ],
    "learning": [
        "5446-suc-manh-cua-thoi-quen-pdf-khoahoctamlinh.vn.pdf"
    ],
    "social": [
        "Amir Levine, M.D., & Rachel Heller, M.A. (2010) - Attached The New Science of Adult Attachment and How It Can Help You Find and Keep Love.pdf"
    ],
    "personality": [
        "Gregory J. Feist, Tomi-Ann Roberts & Jess Feist (2021) - Theories of Personality (Tenth Edition).pdf",
        "Carol Dweck (2006, 2016) - Mindset The New Psychology of Success.pdf"
    ],
    "clinical": [
        "473711314-Tam-lý-học-dị-thường-va-lam-sang-Paul-Bennett-pdf.pdf",
        "The Body Keeps the Score Brain, Mind,  Body in the Healing of Trauma_Bessel van der Kolk_2014.pdf",
        "di-tim-le-song-viktor-emil-frankl.pdf",
        "dai_duong_den.pdf",
        "Lori Gottlieb (2019) - Maybe You Should Talk to Someone.pdf"
    ],
    "research_methods": [
        "Elizabeth A. Phelps, Elliot Berkman, Michael Gazzaniga, Diane Halpern (2022) - Psychological Science (Seventh Edition).pdf",
        "Hal Blumenfeld (2022, 2010, 2002) - Neuroanatomy through Clinical Cases (3rd Edition).pdf",
        "Abigail A. Baird & Anjanie McCarthy (2014, 2012) - Think Psychology (Second Canadian Edition).pdf"
    ]
}

def find_candidate_chunks():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Get holdout hashes
    c.execute("SELECT filename, file_hash FROM documents")
    docs = c.fetchall()
    holdout_hashes = {r["file_hash"] for r in docs if r["filename"] in FROZEN_HOLDOUT_BOOKS}
    holdout_aliases = {r["filename"] for r in docs if r["file_hash"] in holdout_hashes or r["filename"] in FROZEN_HOLDOUT_BOOKS}

    print(f"Total documents: {len(docs)}, Holdouts/aliases: {len(holdout_aliases)}")

    candidates_by_domain = {d: [] for d in DOMAIN_BOOKS}

    for domain, book_list in DOMAIN_BOOKS.items():
        for book in book_list:
            if book in holdout_aliases:
                continue
            query = """
                SELECT c.id, c.doc_id, c.book_title, c.filename, c.page_num, c.chunk_index, c.text, d.file_hash
                FROM chunks c
                JOIN documents d ON c.doc_id = d.id
                WHERE c.filename = ? AND LENGTH(c.text) >= 400 AND LENGTH(c.text) <= 1200
                ORDER BY c.page_num ASC
            """
            c.execute(query, (book,))
            rows = c.fetchall()
            for r in rows:
                raw_text = r["text"]
                complete_text = extract_complete_source_text(raw_text, max_chars=900)
                if len(complete_text) < 300:
                    continue
                is_sub, reason = is_substantive_psychology_source(complete_text)
                if not is_sub:
                    continue
                candidates_by_domain[domain].append({
                    "chunk_id": r["id"],
                    "book": r["filename"],
                    "book_title": r["book_title"],
                    "page": r["page_num"],
                    "domain": domain,
                    "text": complete_text,
                    "source_sha256": hashlib.sha256(complete_text.encode("utf-8")).hexdigest(),
                    "partition": assign_group_partition(r["filename"], r["page_num"])
                })

    print("Substantive candidates found per domain:")
    for d, cands in candidates_by_domain.items():
        print(f"  {d}: {len(cands)}")

if __name__ == "__main__":
    find_candidate_chunks()
