"""Test interprocess communication module"""
import pytest
from libreprinter.legacy_interprocess_com import *


@pytest.fixture()
def init_interprocess():
    # Erase shm file to purge previous jobs
    if os.path.exists("/dev/shm/" + cm.SHARED_MEM_NAME):
        os.remove("/dev/shm/" + cm.SHARED_MEM_NAME)

    initialize_interprocess_com()


def test_send_receive_messages(init_interprocess):
    """Send a message and retreive it in shared memory object"""
    send_status_message(200, 1)

    found_val = get_status_message(200)

    assert 1 == found_val
