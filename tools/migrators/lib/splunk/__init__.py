from lib.oncall_api_client import OnCallAPIClient
from lib.splunk.api_client import SplunkOnCallAPIClient
from lib.splunk.config import SPLUNK_API_ID, SPLUNK_API_KEY


def migrate():
    splunk_client = SplunkOnCallAPIClient(SPLUNK_API_ID, SPLUNK_API_KEY)

    splunk_users = splunk_client.fetch_users()
    oncall_users = OnCallAPIClient.list_users_with_notification_rules()

    print(oncall_users)
