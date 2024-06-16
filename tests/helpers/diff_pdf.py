#  Libreprinter is a software allowing to use the Centronics and serial printing
#  functions of vintage computers on modern equipement through a tiny hardware
#  interface.
#  Copyright (C) 2020-2024  Ysard
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
# Standard imports
import subprocess
from pathlib import Path

# Custom imports
from libreprinter.commons import logger

LOGGER = logger()


def is_similar_pdfs(pdf_file_1, pdf_file_2):
    """Visually compare 2 pdf files for test purposes

    :return: True if the files are similar; otherwise, a diff file is placed
        next to the problematic file in `/tmp`.
    :rtype: bool
    """
    pdf_file_1_name = Path(pdf_file_1).stem
    pdf_file_2_name = Path(pdf_file_2).stem

    diff_output_file = Path(f"/tmp/diff_{pdf_file_1_name}_vs_{pdf_file_2_name}.pdf")
    diffpdf_cmd = [
        "/usr/bin/diff-pdf",
        f"--output-diff={diff_output_file}",
        pdf_file_1,
        pdf_file_2,
    ]

    # We are in a child thread, we can have blocking calls like run()
    # Capture all outputs from the command in case of error with PIPE
    ps = subprocess.Popen(diffpdf_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    ps.wait()
    # diff-pdf returns 0 if the files are the same
    returncode = not bool(ps.returncode)

    LOGGER.info("Similarity <%s> vs <%s>: %s", pdf_file_1, pdf_file_2, returncode)
    if not returncode:
        LOGGER.error("Diff is saved at <%s> for further study.", diff_output_file)
    else:
        diff_output_file.unlink()

    return returncode


if __name__ == "__main__":
    is_similar("/tmp/escp2_1_strip.ps_1.pdf", "/tmp/escp2_1_strip.txt_1.pdf")
    is_similar("/tmp/escp2_1_strip.ps_1.pdf", "/tmp/test_page_pcl.prn_1.pdf")
