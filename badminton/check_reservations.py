import requests
from datetime import date, timedelta

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


def get_params(target_date: date):
    return {
        "date.from": target_date.strftime("%Y-%m-%d"),
        "date.to": target_date.strftime("%Y-%m-%d"),
        "activities": "badminton",
        "partySize": 0
    }


def get_reservations(response_json):
    result = {}
    data = response_json.get("data")
    for slot in data:
        start_time = slot.get("startDateTime", "")
        result[start_time] = []
        for svc in slot.get("services", []):
            result[start_time].append(f"编号：{svc['id']}, 价格：{svc['price'] / 100}€")
    return result


def send_request(day):
    return requests.get(url, params=get_params(day), headers=headers)


def format_response(response, day):
    if response.status_code != 200:
        return format_failed_response(response)

    result = get_reservations(response.json())

    if not result:
        return "未找到可用场地"

    formatted_result = ""

    slot21h_key = slot21h.format(day.strftime("%Y-%m-%d"))
    if slot21h_key in result:
        formatted_result += f"21点：剩余 {len(result[slot21h_key])} 个场地\n"
    else:
        formatted_result += "21点：无可用场地\n"

    slot22h_key = slot22h.format(day.strftime("%Y-%m-%d"))
    if slot22h_key in result:
        formatted_result += f"22点：剩余 {len(result[slot22h_key])} 个场地"
    else:
        formatted_result += "22点：无可用场地"

    return formatted_result

def format_failed_response(response):
    return f"请求失败：{str(response.status_code)} {response.text}"