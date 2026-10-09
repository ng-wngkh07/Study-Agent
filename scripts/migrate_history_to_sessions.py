#!/usr/bin/env python3
"""Database migration script: converts legacy single-question searches to multi-turn sessions.

Features:
- SQLite-consistent atomic backup before any modification (fail-closed).
- Read-only dry-run mode (URI mode=ro) that does not create tables, files, or modify permissions.
- 100% idempotent: does not duplicate or re-create deleted sessions.
- Non-destructive: preserves existing 'searches' table exactly.
- Supports dry-run and custom database path for isolated testing.
"""

import argparse
import sqlite3
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def main():
    parser = argparse.ArgumentParser(description="Migrate legacy searches table to multi-turn conversation sessions")
    parser.add_argument("--db", type=Path, default=PROJECT_ROOT / "data" / "history.db", help="Path to history.db")
    parser.add_argument("--dry-run", action="store_true", help="Inspect without modifying (read-only)")
    args = parser.parse_args()

    db_path = args.db.resolve()
    print("=" * 60)
    print("📦 CÔNG CỤ DI TRÚ LỊCH SỬ SANG PHIÊN TRÒ CHUYỆN (SESSIONS)")
    print(f"   Đường dẫn CSDL: {db_path}")
    print(f"   Chế độ thử nghiệm (dry-run): {args.dry_run}")
    print("=" * 60)

    if not db_path.exists():
        print(f"❌ Không tìm thấy tệp CSDL tại {db_path}")
        sys.exit(1)

    if args.dry_run:
        # Strictly read-only connection without modifying schema, permissions, or creating tables
        uri = f"file:{db_path}?mode=ro"
        try:
            conn = sqlite3.connect(uri, uri=True)
            cur = conn.cursor()
            tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]

            legacy_count = cur.execute("SELECT COUNT(*) FROM searches").fetchone()[0] if "searches" in tables else 0
            session_count = cur.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] if "sessions" in tables else 0
            meta = (
                cur.execute("SELECT value FROM history_meta WHERE key='legacy_searches_migrated'").fetchone()
                if "history_meta" in tables
                else None
            )
            conn.close()

            print(f"• Số lượt tra cứu legacy (bảng searches): {legacy_count}")
            print(f"• Số phiên hiện tại (bảng sessions):      {session_count}")
            print(f"• Trạng thái đã di trú trước đó:         {'ĐÃ DI TRÚ' if meta and meta[0] == '1' else 'CHƯA DI TRÚ'}")
            print("Dry-run hoàn tất (mode=ro). Không có dữ liệu hay cấu trúc nào bị thay đổi.")
            return
        except Exception as e:
            print(f"❌ Lỗi khi đọc CSDL ở chế độ read-only: {e}")
            sys.exit(1)

    # Real migration
    from app.history import HistoryStore
    store = HistoryStore(db_path, auto_init=False)
    try:
        result = store.migrate_legacy_searches(backup=True)
        print("\n✅ KẾT QUẢ DI TRÚ:")
        print(f"   • Trạng thái:           {result['status']}")
        print(f"   • Số lượt đã chuyển:    {result['migrated_count']}")
        if result.get("backup_path"):
            print(f"   • Tệp sao lưu an toàn:  {result['backup_path']}")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Lỗi trong quá trình di trú: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
