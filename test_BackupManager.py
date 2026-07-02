import os
import pytest
from unittest.mock import patch, MagicMock

import BackupManager as bm


# ----------------------------
# Version + Compare Logic
# ----------------------------

def test_version_current():
    assert bm.get_current_version() == bm.VERSION


def test_compare_versions_newer():
    assert bm.compare_versions("1.0.0", "1.0.1") is True


def test_compare_versions_older():
    assert bm.compare_versions("1.2.0", "1.1.9") is False


def test_compare_versions_equal():
    assert bm.compare_versions("1.0.0", "1.0.0") is False


# ----------------------------
# Needs Update Logic
# ----------------------------

def test_needs_update_no_target():
    assert bm.needs_update(100, 1000.0, None) is True


def test_needs_update_size_diff():
    assert bm.needs_update(100, 1000.0, (200, 1000.0)) is True


def test_needs_update_mtime_diff():
    assert bm.needs_update(100, 1000.0, (100, 9999.0)) is True


def test_needs_update_equal():
    assert bm.needs_update(100, 1000.0, (100, 1000.0)) is False


# ----------------------------
# Ignore logic
# ----------------------------

def test_should_ignore_flag():
    bm.IGNORE_EXCLUDE_LIST = True
    assert bm.should_ignore(MagicMock()) is False

    bm.IGNORE_EXCLUDE_LIST = False


# ----------------------------
# Logging (mock file system)
# ----------------------------

@patch("builtins.open", new_callable=MagicMock)
@patch("os.makedirs")
def test_log_function(mock_mkdir, mock_open):
    bm.log("test message")

    mock_mkdir.assert_called()
    mock_open.assert_called()


# ----------------------------
# stat_file
# ----------------------------

@patch("os.stat")
def test_stat_file_success(mock_stat):
    mock_stat.return_value.st_size = 123
    mock_stat.return_value.st_mtime = 456

    res = bm.stat_file("dummy.txt")

    assert res[0] == "dummy.txt"
    assert res[1] == 123
    assert res[2] == 456


@patch("os.stat", side_effect=Exception("fail"))
def test_stat_file_fail(mock_stat):
    assert bm.stat_file("dummy.txt") is None


# ----------------------------
# collect_files_multithread (light test)
# ----------------------------

@patch("os.scandir")
@patch("os.stat")
def test_collect_files_basic(mock_stat, mock_scandir):
    # fake file entry
    file_entry = MagicMock()
    file_entry.path = "file1.txt"
    file_entry.is_file.return_value = True
    file_entry.is_dir.return_value = False

    mock_scandir.return_value = [file_entry]

    mock_stat.return_value.st_size = 10
    mock_stat.return_value.st_mtime = 100

    results, size = bm.collect_files_multithread("base", "test")

    assert isinstance(results, list)
    assert size >= 0


# ----------------------------
# copy_file (mock filesystem)
# ----------------------------

@patch("os.makedirs")
@patch("shutil.copy2")
@patch("os.path.getsize", return_value=100)
def test_copy_file(mock_size, mock_copy, mock_mkdir):
    progress = MagicMock()

    bm.copy_file(
        "src.txt",
        "dst_base",
        "src_base",
        progress
    )

    mock_mkdir.assert_called()
    mock_copy.assert_called()
    progress.update.assert_called_with(100)