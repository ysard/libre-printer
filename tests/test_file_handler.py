"""Test file handler module"""
# Standard imports
import os
import shutil
import pathlib
import tempfile
import pytest
from unittest.mock import patch

# Custom imports
from libreprinter.file_handler import (
    init_directories,
    cleanup_directories,
    get_job_number,
    convert_data_line_ending,
    convert_file_line_ending,
)
from libreprinter.commons import OUTPUT_DIRS


@pytest.fixture()
def temp_dir():
    """Create temp directory (with trailing "/")

    :rtype: Iterator[str]
    """
    # Setup: Create temp dir
    temp_dir = tempfile.mkdtemp() + "/"

    yield temp_dir

    # Tear down: Clean
    shutil.rmtree(temp_dir)


def test_init_directories(temp_dir):
    """Test the creation of default directories

    .. seealso:: Directories listed in :meth:`libreprinter.commons.OUTPUT_DIRS`
    """
    init_directories(temp_dir)

    found_paths = {path for path in pathlib.Path(temp_dir).glob("*")}
    found_dir_names = {path.name for path in found_paths}

    print("temp_dir:", temp_dir, "found:", found_dir_names)
    assert set(OUTPUT_DIRS) == found_dir_names

    # Double init should not raise any error
    init_directories(temp_dir)

    # Init in directory that doesn't exist should not raise any error
    init_directories(temp_dir + "test/")

    # Check rights
    for path in found_paths:
        found_permissions = path.stat().st_mode
        assert "0o40755" == oct(found_permissions)


@patch("libreprinter.file_handler.SHARED_MEM_NAME", "test")
def test_cleanup_directories(temp_dir):
    """Test the deletion of directories

    libreprinter.commons.SHARED_MEM_NAME is patched with a value "test"

    .. seealso:: Directories listed in :meth:`libreprinter.commons.OUTPUT_DIRS`
    """
    init_directories(temp_dir)

    # Fake file in dir
    os.mknod(temp_dir + "1.raw")
    # Fake shared memory file
    # libreprinter.commons.SHARED_MEM_NAME is patched as "test"
    os.mknod("/dev/shm/test")

    cleanup_directories(temp_dir)

    for directory in OUTPUT_DIRS:
        assert not os.path.exists(temp_dir + directory)

    assert not os.path.exists("/dev/shm/test")

    # Double deletion should not raise any error
    cleanup_directories(temp_dir)


def test_get_job_number(temp_dir):
    """Test the search of the highest file name recursively through project's dirs

    Example of files::

        - raw/1.raw: File with data
        - raw/10.raw: File without data
        - pcl/2.raw: File with data
        - txt_jobs/3.txt: File with data

        :meth:`libreprinter.file_handler.get_job_number` should return 4 (int)
    """
    # Empty dir
    found_val = get_job_number(temp_dir)
    print(found_val)
    # assert found_val == 1

    # Populated dir
    init_directories(temp_dir)
    # Create test files
    with open(temp_dir + "raw/1.raw", "w") as f_d:
        f_d.write("hello world")

    with open(temp_dir + "pcl/2.raw", "w") as f_d:
        f_d.write("hello world")

    with open(temp_dir + "txt_jobs/3.txt", "w") as f_d:
        f_d.write("hello world")

    os.mknod(temp_dir + "raw/10.raw")

    found_val = get_job_number(temp_dir)
    print(found_val)

    assert found_val == 4


def test_convert_data_line_ending():
    """Test conversion of line endings"""
    unix_text = b"hello world\n"
    windows_text = b"hello world\r\n"

    # Same line ending
    found = convert_data_line_ending(unix_text, b"\n")
    assert unix_text == found

    # Unix => Windows
    found = convert_data_line_ending(unix_text, b"\r\n")
    assert windows_text == found

    # Windows => Unix
    found = convert_data_line_ending(windows_text, b"\n")
    assert unix_text == found

    # Not bytes data
    with pytest.raises(TypeError, match=r".*argument 1 must be str, not bytes"):
        _ = convert_data_line_ending(windows_text.decode(), b"\n")


def test_convert_file_line_ending(temp_dir):
    """Test conversion of line endings in files"""

    input_file = pathlib.Path(temp_dir + "windows_file")
    output_file = pathlib.Path(temp_dir + "unix_file")

    # Windows => Unix
    input_file.write_text("hello\r\nworld")
    convert_file_line_ending(input_file, output_file, "\n")
    expected = b"hello\nworld"
    # Use binary mode to avoid line ending change by encoding setting...
    assert output_file.read_bytes() == expected
