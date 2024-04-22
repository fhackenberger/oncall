import logging

from celery.utils.log import get_task_logger

from apps.google import constants
from apps.google.client import GoogleCalendarAPIClient
from apps.google.models import GoogleOAuth2User
from apps.schedules.models import OnCallSchedule, ShiftSwapRequest
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

logger = get_task_logger(__name__)
logger.setLevel(logging.DEBUG)


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True)
def sync_out_of_office_calendar_events_for_user(google_oauth2_user_pk: int) -> None:
    google_oauth2_user = GoogleOAuth2User.objects.get(pk=google_oauth2_user_pk)
    google_api_client = GoogleCalendarAPIClient(google_oauth2_user.access_token, google_oauth2_user.refresh_token)

    user = google_oauth2_user.user
    user_id = user.pk

    logger.info(f"Syncing out of office Google Calendar events for user {user_id}")

    users_schedules = OnCallSchedule.objects.related_to_user(user)
    user_google_calendar_settings = user.google_calendar_settings
    oncall_schedules_to_consider_for_shift_swaps = user_google_calendar_settings[
        "oncall_schedules_to_consider_for_shift_swaps"
    ]

    if oncall_schedules_to_consider_for_shift_swaps:
        users_schedules = users_schedules.filter(public_primary_key__in=oncall_schedules_to_consider_for_shift_swaps)

    for out_of_office_event in google_api_client.fetch_out_of_office_events():
        raw_event = out_of_office_event.raw_event

        event_title = raw_event["summary"]
        event_id = raw_event["id"]
        start_time_utc = out_of_office_event.start_time_utc
        end_time_utc = out_of_office_event.end_time_utc

        logger.info(
            f"Processing out of office event {event_id} starting at {start_time_utc} and ending at "
            f"{end_time_utc} for user {user_id}"
        )

        if constants.EVENT_SUMMARY_IGNORE_KEYWORD in event_title.lower():
            logger.info(
                f"Skipping out of office event {event_id} because it contains the ignore keyword "
                f"'{constants.EVENT_SUMMARY_IGNORE_KEYWORD}'"
            )
            continue

        for schedule in users_schedules:
            _, current_shifts, upcoming_shifts = schedule.shifts_for_user(
                user,
                start_time_utc,
                datetime_end=end_time_utc,
            )

            if current_shifts or upcoming_shifts:
                logger.info(
                    f"Found {len(current_shifts)} current shift(s) and {len(upcoming_shifts)} upcoming shift(s) "
                    f"for user {user_id} during the out of office event {event_id}"
                )

                shift_swap_request_exists = ShiftSwapRequest.objects.filter(
                    beneficiary=user,
                    schedule=schedule,
                    swap_start=start_time_utc,
                    swap_end=end_time_utc,
                ).exists()

                if not shift_swap_request_exists:
                    logger.info(
                        f"Creating shift swap request for user {user_id} schedule {schedule.pk} "
                        f"due to the out of office event {event_id}"
                    )

                    ssr = ShiftSwapRequest.objects.create(
                        beneficiary=user,
                        schedule=schedule,
                        swap_start=start_time_utc,
                        swap_end=end_time_utc,
                        description=f"{user.name or user.email} will be out of office during this time according to Google Calendar",
                    )

                    logger.info(f"Created shift swap request {ssr.pk}")
                else:
                    logger.info(f"Shift swap request already exists for user {user_id} schedule {schedule.pk}")
            else:
                logger.info(
                    f"No current or upcoming shifts found for user {user_id} during the out of office event {event_id}"
                )


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True)
def sync_out_of_office_calendar_events_for_all_users() -> None:
    for google_oauth2_user in GoogleOAuth2User.objects.all():
        sync_out_of_office_calendar_events_for_user.apply_async(args=(google_oauth2_user.pk,))
