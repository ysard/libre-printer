"""Gestion of files (creation and processing) and directories used by the project"""
# Standard imports
import os
import shutil
import glob
import itertools as it
# Custom imports
from libreprinter.commons import OUTPUT_DIRS, SHARED_MEM_NAME


def init_directories(output_path):
    """Init output directories (raw, png, pdf, txt, pcl)

    :param output_path: Path were directories will be created.
    :type output_path: str
    """
    # test if output path exists
    if not os.path.isdir(output_path):
        os.mkdir(output_path)

    for directory in OUTPUT_DIRS:
        try:
            os.mkdir(output_path + directory, mode=0o744)
        except FileExistsError:
            pass


def cleanup_directories(output_path):
    """Delete all directories initialised by this project in the given path

    Deletes also /dev/shm/ shared memory.

    :param output_path: Path were directories will be created.
    :type output_path: str
    """
    for directory in OUTPUT_DIRS:
        try:
            shutil.rmtree(output_path + directory)
        except FileNotFoundError:
            pass

    # Clean shared memory
    try:
        os.remove("/dev/shm/" + SHARED_MEM_NAME)
    except FileNotFoundError:
        pass


def get_job_number(output_path):
    """Return the number of the current job based on files found in output directories

    - Get only non empty files
    - Get only expected extensions (txt, raw, eps)
    - Search highest file number in all folders

    TODO: handle properly pdf dir data: page1-1.pdf, page1-2.pdf, page2-1.pdf, ...
    :return: Current job number
    :rtype: int
    """
    # Search files in folders with an extension which equals the folder's name
    # => temp/trash files are avoided
    g = it.chain(*(glob.glob(output_path + directory + "/*.*") for directory in OUTPUT_DIRS if directory != "pdf"))
    # Prune empty files, get basenames and filter extensions
    pruned = (
        os.path.splitext(filepath) for filepath in g
        if os.path.getsize(filepath) != 0
    )
    pruned = (
        os.path.basename(filename) for filename, extension in pruned
        if extension in (".txt", ".raw", ".eps")
    )
    pruned = sorted(int(val) for val in pruned if val.isnumeric())
    # Increment the value to get the current job number
    return int(pruned[-1]) + 1 if pruned else 1


def convert_data_line_ending(in_data, line_ending):
    r"""Replace line endings of in_data and return the result

    unix => windows: \n => \r\n
    windows => unix: \r\n => \n

    :param in_data: Data to be processed
    :param line_ending: Destination line ending.
    :type in_data: bytes
    :type line_ending: bytes
    :return: Processed data
    :rtype: bytes
    """
    conv_mapping = {
        b"\n": b"\r\n",
        b"\r\n": b"\n",
    }
    return in_data.replace(conv_mapping[line_ending], line_ending)


def convert_file_line_ending(in_file, out_file, line_ending):
    """Replace line endings of in_file and put data in out_file

    .. seealso:: :meth:convert_data_line_ending

    :param in_file: Path of processed but not modified file.
    :param out_file: Path of result file.
    :param line_ending: Destination line ending
    :type line_ending: str
    """
    # Convert to bytes for binary files
    line_ending = line_ending.encode()

    with open(in_file, "rb") as in_file_fd, open(out_file, "wb") as out_file_fd:
        out_file_fd.write(convert_data_line_ending(in_file_fd.read(), line_ending))
