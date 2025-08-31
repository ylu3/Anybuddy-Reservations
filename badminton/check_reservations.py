from datetime import date, timedelta, datetime
from typing import Literal, TypedDict
from zoneinfo import ZoneInfo

import requests

today = date.today()
next_saturday = today + timedelta((5 - today.weekday()) % 7)  # 5 is Saturday
next_sunday = today + timedelta((6 - today.weekday()) % 7)  # 6 is Sunday

slot21h = "{}T21:00"
slot22h = "{}T22:00"

# Forest Hill Aquaboulevard badminton
url = "https://api-booking.anybuddyapp.com/v2/centers/aquaboulevard-de-paris/availabilities"

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

SlotBookingStatus = Literal["not_opened", "opened", "outdated", "not_applicable"]
paris = ZoneInfo("Europe/Paris")


class ApiResponse(TypedDict):
    status: Literal["succeeded", "failed"]
    slot21h_booking_status: SlotBookingStatus
    slot21h_count: int
    slot22h_booking_status: SlotBookingStatus
    slot22h_count: int
    error_message: str


def get_params(target_date: date):
    return {
        "date.from": target_date.strftime("%Y-%m-%d"),
        "date.to": target_date.strftime("%Y-%m-%d"),
        "activities": "badminton",
        "partySize": 0
    }


def get_slot_count_by_time(response_json):
    slot_count = {}
    data = response_json.get("data")
    for slot in data:
        start_time = slot.get("startDateTime", "")
        slot_count[start_time] = len(slot.get("services", []))
    return slot_count


def send_request(target_day: date) -> ApiResponse:
    response = requests.get(url, params=get_params(target_day), headers=headers)
    now = datetime.now(paris)
    if response.status_code != 200:
        return {
            "status": "failed",
            "slot21h_booking_status": "not_applicable",
            "slot21h_count": -1,
            "slot22h_booking_status": "not_applicable",
            "slot22h_count": -1,
            "error_message": f"Error: {response.status_code} {response.text}"
        }

    slot_count = get_slot_count_by_time(response.json())
    slot21h_key = slot21h.format(target_day.strftime("%Y-%m-%d"))
    slot22h_key = slot22h.format(target_day.strftime("%Y-%m-%d"))

    target_day_21h = datetime(target_day.year, target_day.month, target_day.day, 21, tzinfo=paris)
    target_day_22h = datetime(target_day.year, target_day.month, target_day.day, 22, tzinfo=paris)
    target_day_23h = datetime(target_day.year, target_day.month, target_day.day, 23, tzinfo=paris)

    slot21h_booking_status: SlotBookingStatus = "outdated" if now > target_day_22h else ("not_opened" if target_day_21h - now > timedelta(hours=144) else "opened")
    slot22h_booking_status: SlotBookingStatus = "outdated" if now > target_day_23h else ("not_opened" if target_day_22h - now > timedelta(hours=144) else "opened")

    slot21h_count = slot_count.get(slot21h_key, 0)
    slot22h_count = slot_count.get(slot22h_key, 0)
    return {
        "status": "succeeded",
        "slot21h_booking_status": "opened" if slot21h_count > 0 else slot21h_booking_status,
        "slot21h_count": slot21h_count,
        "slot22h_booking_status": "opened" if slot22h_count > 0 else slot22h_booking_status,
        "slot22h_count": slot22h_count,
        "error_message": ""
    }


if __name__ == "__main__":
    today = datetime.now(paris).date()

    # 5=Saturday, 6=Sunday
    next_saturday = today + timedelta((5 - today.weekday()) % 7)
    next_sunday = today + timedelta((6 - today.weekday()) % 7)

    print(send_request(next_saturday))
    print(send_request(next_sunday))
