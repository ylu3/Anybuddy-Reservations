import json
import os
from datetime import timedelta, datetime
from typing import TypedDict
from zoneinfo import ZoneInfo

from check_reservations import send_request, SlotBookingStatus
from send_mails import send_email

LOG_FILE = "badminton/script.log"
LAST_RUN_RESULT_FILE = "badminton/last_run_result.json"


class RunResult(TypedDict):
    today: str
    timestamp: str
    next_saturday: str
    next_saturday_21h_slot_booking_status: str
    next_saturday_21h_slot_count: int
    next_saturday_22h_slot_booking_status: str
    next_saturday_22h_slot_count: int
    body: str


def log(message: str) -> None:
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(message.rstrip("\n") + "\n")


def read_last_run_result(path: str) -> RunResult | None:
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def write_run_result(path: str, result: RunResult):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)


def should_notify(current: RunResult, last: RunResult | None) -> bool:
    if not last:
        return True

    if (current["next_saturday_21h_slot_booking_status"] == "opened" and (
            current["next_saturday"] != last["next_saturday"] or current["next_saturday_21h_slot_booking_status"] != last["next_saturday_21h_slot_booking_status"]
            or current["next_saturday_21h_slot_count"] != last["next_saturday_21h_slot_count"])) \
            or (current["next_saturday_22h_slot_booking_status"] == "opened" and (
            current["next_saturday"] != last["next_saturday"] or current["next_saturday_22h_slot_booking_status"] != last["next_saturday_22h_slot_booking_status"]
            or current["next_saturday_22h_slot_count"] != last["next_saturday_22h_slot_count"])):
        return True

    return False


def main():
    paris = ZoneInfo("Europe/Paris")
    today = datetime.now(paris).date()
    log(f"-- Debug timestamp(Europe/Paris): {datetime.now(paris).isoformat()} --")
    log(f"Today is {today}, {today.strftime('%A')}")

    # 5=Saturday, 6=Sunday
    next_saturday = today + timedelta((5 - today.weekday()) % 7)
    next_sunday = today + timedelta((6 - today.weekday()) % 7)

    log(f"Next Saturday is {next_saturday}, checking...")
    api_response_sat = send_request(next_saturday)
    log(f"{api_response_sat}")

    if api_response_sat["status"] != "succeeded":
        log("API requests failed, skipped.")
        return

    def get_status_description(status: SlotBookingStatus, slot_count: int) -> str:
        match status:
            case "not_opened":
                return "尚未开放预订"
            case "opened":
                return f"剩余 {slot_count} 个场地"
            case "outdated":
                return "已过期"
            case "not_applicable":
                return "不适用"

    body_sat = (
        f"—— {'下' if next_saturday > next_sunday else ''}周六 ({next_saturday.isoformat()}) ——\n"
        f"21:00 - {get_status_description(api_response_sat['slot21h_booking_status'], api_response_sat['slot21h_count'])}\n"
        f"22:00 - {get_status_description(api_response_sat['slot22h_booking_status'], api_response_sat['slot22h_count'])}"
    )
    body = body_sat

    run_result: RunResult = {
        "today": today.isoformat(),
        "timestamp": datetime.now(paris).isoformat(),
        "next_saturday": next_saturday.isoformat(),
        "next_saturday_21h_slot_booking_status": api_response_sat["slot21h_booking_status"],
        "next_saturday_21h_slot_count": api_response_sat["slot21h_count"],
        "next_saturday_22h_slot_booking_status": api_response_sat["slot22h_booking_status"],
        "next_saturday_22h_slot_count": api_response_sat["slot22h_count"],
        "body": body
    }

    last_run_result = read_last_run_result(LAST_RUN_RESULT_FILE)

    if should_notify(run_result, last_run_result):
        send_email("📅 羽毛球场地更新", body)
        log("Mail sent.")

    write_run_result(LAST_RUN_RESULT_FILE, run_result)
    log("Run result saved.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"Error: {e}")
    log("\n")
