from constants import DataSources
from scanner.acs.runner import ACSTaskRunner
from scanner.acs.connect import ConnectTaskRunner
from tests.factories import ScanTaskFactory
from rest_framework import status
import pytest
from api.models import ScanTask


@pytest.fixture
def scan_task():
    """Return a ScanTask for testing."""
    return ScanTaskFactory(
        source__source_type=DataSources.ACS,
        source__hosts=["1.2.3.4"],
        source__port=4321,
        scan_type=ScanTask.SCAN_TYPE_CONNECT,
    )


@pytest.fixture
def mock_client(mocker):
    return mocker.patch.object(ACSTaskRunner, "get_client")


@pytest.mark.django_db
def test_green_path(mock_client, scan_task: ScanTask):

    runner = ConnectTaskRunner(scan_task=scan_task, scan_job=scan_task.job)
    mock_client.return_value.get.return_value.status_code = 200
    message, status = runner.execute_task(mock_client)
    assert message == runner.success_message
    assert status == ScanTask.COMPLETED
    assert scan_task.systems_count == 1
    assert scan_task.systems_scanned == 1
    assert scan_task.systems_failed == 0
    assert scan_task.systems_unreachable == 0
