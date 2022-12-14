# Copyright (c) 2022 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#

"""OpenShift inspect task runner."""

from django.conf import settings
from django.db import transaction

from api.models import RawFact, ScanTask, SystemInspectionResult
from scanner.exceptions import ScanFailureError
from scanner.openshift.entities import OCPBaseEntity, OCPNode
from scanner.openshift.task import OpenShiftTaskRunner


class InspectTaskRunner(OpenShiftTaskRunner):
    """OpenShift inspect task runner."""

    SUCCESS_MESSAGE = "Inspected OpenShift host succesfully."
    PARTIAL_SUCCESS_MESSAGE = (
        "Inspected some data from OpenShift host. Check details report for errors."
    )
    FAILURE_MESSAGE = "Unable to inspect OpenShift host."

    def execute_task(self, manager_interrupt):
        """Scan satellite manager and obtain host facts."""
        self._check_prerequisites()

        ocp_client = self.get_ocp_client(self.scan_task)
        nodes_list = ocp_client.retrieve_nodes(
            timeout_seconds=settings.QPC_INSPECT_TASK_TIMEOUT,
        )

        self._init_stats(nodes_list)

        for node in nodes_list:
            # check if scanjob is paused or cancelled
            self.check_for_interrupt(manager_interrupt)
            self._save_results(node)

        self.log(f"Collected facts for {self.scan_task.systems_scanned} nodes.")
        self.log(f"Failed collecting facts for {self.scan_task.systems_failed} nodes.")

        # cluster = get_cluster()
        # project_list = ocp_client.retrieve_projects(
        #     retrieve_all=False,
        #     timeout_seconds=settings.QPC_INSPECT_TASK_TIMEOUT,
        # )
        # self._init_stats(project_list)
        # for project in project_list:
        #     # check if scanjob is paused or cancelled
        #     self.check_for_interrupt(manager_interrupt)
        #     ocp_client.add_deployments_to_project(
        #         project,
        #         timeout_seconds=settings.QPC_INSPECT_TASK_TIMEOUT,
        #     )
        # save_cluster(cluster, project_list)

        if self.scan_task.systems_scanned and self.scan_task.systems_failed:
            return self.PARTIAL_SUCCESS_MESSAGE, ScanTask.COMPLETED
        if self.scan_task.systems_scanned:
            return self.SUCCESS_MESSAGE, ScanTask.COMPLETED
        return self.FAILURE_MESSAGE, ScanTask.FAILED

    def _check_prerequisites(self):
        connect_scan_task = self.scan_task.prerequisites.first()
        if connect_scan_task.status != ScanTask.COMPLETED:
            raise ScanFailureError("Prerequisite scan have failed.")

    def _init_stats(self, nodes_list):
        return self.scan_task.update_stats(
            "INITIAL OCP INSPECT STATS.",
            sys_count=len(nodes_list),
            sys_scanned=0,
            sys_failed=0,
            sys_unreachable=0,
        )

    @transaction.atomic
    def _save_results(self, node: OCPNode):
        system_result = self._persist_facts(node)
        increment_kwargs = self._get_increment_kwargs(system_result.status)
        self.scan_task.increment_stats(node.name, **increment_kwargs)

    def _persist_facts(self, node: OCPNode) -> SystemInspectionResult:
        inspection_status = self._infer_inspection_status(node)
        sys_result = SystemInspectionResult(
            name=node.name,
            status=inspection_status,
            source=self.scan_task.source,
            task_inspection_result=self.scan_task.inspection_result,
        )
        sys_result.save()
        raw_fact = self._entity_as_raw_fact(node, sys_result)
        raw_fact.save()
        return sys_result

    def _entity_as_raw_fact(
        self, entity: OCPBaseEntity, inspection_result: SystemInspectionResult
    ) -> RawFact:
        return RawFact(
            name=entity.kind,
            value=entity.json(),
            system_inspection_result=inspection_result,
        )

    def _infer_inspection_status(self, node: OCPNode):
        if node.errors:
            return SystemInspectionResult.FAILED
        return SystemInspectionResult.SUCCESS

    def _get_increment_kwargs(self, inspection_status):
        return {
            SystemInspectionResult.SUCCESS: {
                "increment_sys_scanned": True,
                "prefix": "INSPECTED",
            },
            SystemInspectionResult.FAILED: {
                "increment_sys_failed": True,
                "prefix": "FAILED",
            },
        }[inspection_status]
