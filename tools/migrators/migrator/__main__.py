from lib.base_config import MIGRATING_FROM, PAGERDUTY, SPLUNK


if __name__ == "__main__":
    if MIGRATING_FROM == PAGERDUTY:
        from lib.pagerduty import migrate

        migrate()
    elif MIGRATING_FROM == SPLUNK:
        from lib.splunk import migrate

        migrate()
    else:
        raise ValueError("Invalid MIGRATING_FROM value")
