# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for the cloudlib.billing module."""

from absl.testing import absltest

from django_cloud_deploy.cloudlib import billing
from django_cloud_deploy.tests.unit.cloudlib.lib import http_fake

PROJECT_ID = 'fake_project_id'
BILLING_ACCOUNT_NAME = 'fake_billing_account'

BILLING_INFO_ENABLED = {
    'billingEnabled': True,
}

BILLING_INFO_DISABLED = {
    'billingEnabled': False,
}

BILLING_ACCOUNT_LIST_RESPONSE = {
    'billingAccounts': [
        {
            'name': 'billingAccounts/1',
            'displayName': 'Fake Account 1',
            'open': True
        },
        {
            'name': 'billingAccounts/2',
            'displayName': 'Fake Account 2',
            'open': False
        },
    ]
}


class BillingAccountsFake(object):

    def list(self):
        return http_fake.HttpRequestFake(BILLING_ACCOUNT_LIST_RESPONSE)


class ProjectsFake(object):

    def __init__(self):
        self.project_billing_map = {}

    def getBillingInfo(self, name):
        if name in self.project_billing_map:
            return http_fake.HttpRequestFake(BILLING_INFO_ENABLED)
        else:
            return http_fake.HttpRequestFake(BILLING_INFO_DISABLED)

    def updateBillingInfo(self, name, body):
        self.project_billing_map[name] = body['billingAccountName']
        if 'invalid' in name:
            return http_fake.HttpRequestFake({})
        else:
            return http_fake.HttpRequestFake(BILLING_INFO_ENABLED)


class CloudBillingServiceFake(object):

    def __init__(self, query_times=1):
        self.projects_fake = ProjectsFake()
        self.billing_accounts_fake = BillingAccountsFake()

    def projects(self):
        return self.projects_fake

    def billingAccounts(self):
        return self.billing_accounts_fake


class BillingClientTestCase(absltest.TestCase):
    """Test case for billing.BillingClient."""

    def setUp(self):
        self._cloudbillingservice_fake = CloudBillingServiceFake()
        self._billing_client = billing.BillingClient(
            self._cloudbillingservice_fake)

    def test_check_billing_disabled(self):
        self.assertFalse(self._billing_client.check_billing_enabled(PROJECT_ID))

    def test_enable_project_billing(self):
        self._billing_client.enable_project_billing(PROJECT_ID,
                                                    BILLING_ACCOUNT_NAME)
        self.assertIn(
            'projects/{}'.format(PROJECT_ID),
            self._cloudbillingservice_fake.projects().project_billing_map)
        self.assertTrue(self._billing_client.check_billing_enabled(PROJECT_ID))

    def test_enable_project_billing_fail(self):
        with self.assertRaises(billing.BillingError):
            self._billing_client.enable_project_billing('invalid-project-id',
                                                        BILLING_ACCOUNT_NAME)

    def test_list_billing_accounts(self):
        accounts = self._billing_client.list_billing_accounts()
        self.assertEqual(
            len(BILLING_ACCOUNT_LIST_RESPONSE['billingAccounts']),
            len(accounts))

    def test_list_billing_accounts_only_open(self):
        accounts = self._billing_client.list_billing_accounts(
            only_open_accounts=True)
        self.assertNotEqual(
            len(BILLING_ACCOUNT_LIST_RESPONSE['billingAccounts']),
            len(accounts))
        for account in accounts:
            self.assertTrue(account['open'])


if __name__ == '__main__':
    absltest.main()
