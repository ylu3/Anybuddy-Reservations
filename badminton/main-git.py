import os
from datetime import date, timedelta, datetime

from check_reservations import send_request, format_response
from send_mails import send_email

LOG_FILE = "badminton/script.log"
LAST_RESULT_FILE = "badminton/last_result.txt"


def log(message: str) -> None:
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(message.rstrip("\n") + "\n")


def read_last_result(path: str) -> str:
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_last_result(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    today = date.today()
    log(f"-- Debug timestamp: {datetime.now().isoformat()} --")
    log(f"今天是 {today}, {today.strftime('%A')}")

    # 5=Saturday, 6=Sunday
    next_saturday = today + timedelta((5 - today.weekday()) % 7)
    next_sunday = today + timedelta((6 - today.weekday()) % 7)

    log(f"下周六是 {next_saturday}, 正在检查...")
    response_sat = send_request(next_saturday)
    res_sat = format_response(response_sat, next_saturday)
    log(f"{res_sat}")

    log(f"下周日是 {next_sunday}, 正在检查...")
    response_sun = send_request(next_sunday)
    res_sun = format_response(response_sun, next_sunday)
    log(f"{res_sun}")

    body = (
        f"—— 周六 ({next_saturday}) ——\n"
        f"{res_sat}\n"
        f"—— 周日 ({next_sunday}) ——\n"
        f"{res_sun}"
    )

    last_body = read_last_result(LAST_RESULT_FILE)

    if response_sat.status_code != 200 or response_sun.status_code != 200:
        log("请求失败，跳过")
    elif body != last_body:
        write_last_result(LAST_RESULT_FILE, body)
        send_email("📅 羽毛球场地更新", body)
        log("已发送邮件")
    else:
        log("暂无更新")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"发生错误: {e}")
    log("\n")
