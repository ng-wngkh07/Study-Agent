from scripts.check_history import validate


OLD = "### LOG-20261009-qa-first\nFirst change\n"
NEW = OLD + "### LOG-20261010-lookup-fix\nFixed lookup and tested\n"


def test_code_change_without_log_is_rejected():
    assert validate(["app/server.py"], OLD, OLD)


def test_editing_only_old_log_is_not_a_new_entry():
    assert validate(["app/server.py", "LICH_SU_DU_AN.md"], OLD + "text", OLD)


def test_new_log_with_code_change_is_accepted():
    assert validate(["app/server.py", "LICH_SU_DU_AN.md"], NEW, OLD) == []


def test_old_entries_cannot_be_removed_or_ids_duplicated():
    assert validate(["LICH_SU_DU_AN.md"], NEW + OLD, OLD)
    assert validate(["LICH_SU_DU_AN.md"], "### LOG-new\n", OLD)
