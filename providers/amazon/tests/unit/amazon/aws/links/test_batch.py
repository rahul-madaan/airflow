# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
from __future__ import annotations

import pytest

from airflow.providers.amazon.aws.links.batch import (
    BatchJobDefinitionLink,
    BatchJobDetailsLink,
    BatchJobQueueLink,
)

from tests_common.test_utils.version_compat import AIRFLOW_V_3_0_PLUS
from unit.amazon.aws.links.test_base_aws import BaseAwsLinksTestCase

if AIRFLOW_V_3_0_PLUS:
    from airflow.sdk.execution_time.comms import XComResult

pytestmark = pytest.mark.db_test


class TestBatchJobDefinitionLink(BaseAwsLinksTestCase):
    link_class = BatchJobDefinitionLink

    def test_extra_link(self, mock_supervisor_comms):
        if AIRFLOW_V_3_0_PLUS and mock_supervisor_comms:
            mock_supervisor_comms.send.return_value = XComResult(
                key=self.link_class.key,
                value={
                    "region_name": "eu-west-1",
                    "aws_domain": self.link_class.get_aws_domain("aws"),
                    "aws_partition": "aws",
                    "job_definition_arn": "arn:fake:jd",
                },
            )
        self.assert_extra_link_url(
            expected_url=(
                "https://console.aws.amazon.com/batch/home?region=eu-west-1#job-definition/detail/arn:fake:jd"
            ),
            region_name="eu-west-1",
            aws_partition="aws",
            job_definition_arn="arn:fake:jd",
        )


class TestBatchJobDetailsLink(BaseAwsLinksTestCase):
    link_class = BatchJobDetailsLink

    def test_extra_link(self, mock_supervisor_comms):
        if AIRFLOW_V_3_0_PLUS and mock_supervisor_comms:
            mock_supervisor_comms.send.return_value = XComResult(
                key=self.link_class.key,
                value={
                    "region_name": "cn-north-1",
                    "aws_domain": self.link_class.get_aws_domain("aws-cn"),
                    "aws_partition": "aws-cn",
                    "job_id": "fake-id",
                },
            )
        self.assert_extra_link_url(
            expected_url="https://console.amazonaws.cn/batch/home?region=cn-north-1#jobs/detail/fake-id",
            region_name="cn-north-1",
            aws_partition="aws-cn",
            job_id="fake-id",
        )


class TestBatchJobQueueLink(BaseAwsLinksTestCase):
    link_class = BatchJobQueueLink

    def test_extra_link(self, mock_supervisor_comms):
        if AIRFLOW_V_3_0_PLUS and mock_supervisor_comms:
            mock_supervisor_comms.send.return_value = XComResult(
                key=self.link_class.key,
                value={
                    "region_name": "us-east-1",
                    "aws_domain": self.link_class.get_aws_domain("aws"),
                    "aws_partition": "aws",
                    "job_queue_arn": "arn:fake:jq",
                },
            )
        self.assert_extra_link_url(
            expected_url=(
                "https://console.aws.amazon.com/batch/home?region=us-east-1#queues/detail/arn:fake:jq"
            ),
            region_name="us-east-1",
            aws_partition="aws",
            job_queue_arn="arn:fake:jq",
        )
