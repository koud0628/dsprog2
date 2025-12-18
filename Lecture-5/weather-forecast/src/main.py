import flet as ft
import requests

AREA_URL = "https://www.jma.go.jp/bosai/common/const/area.json"
FORECAST_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/"

# 天気アイコンを取得する関数
# 天気を最大2つまで表示
def weather_icons(text: str) -> str:
    icons = []
    if "晴" in text:
        icons.append("☀️")
    if "曇" in text:
        icons.append("☁️")
    if "雨" in text:
        icons.append("☔")
    if "雪" in text:
        icons.append("❄️")

    unique = []
    for i in icons:
        if i not in unique:
            unique.append(i)

    return " / ".join(unique[:2])

# 天気に応じた背景色を取得する関数
def weather_color(text: str) -> str:
    if "雪" in text:
        return "#E3F2FD"
    if "雨" in text:
        return "#D0E7F9"
    if "曇" in text:
        return "#ECEFF1"
    if "晴" in text:
        return "#FFF8E1"
    return "#FFFFFF"

# アプリのメイン関数
def main(page: ft.Page):
    page.title = "地方別 天気予報"
    page.bgcolor = "#EEF6FF"

    page.appbar = ft.AppBar(
        title=ft.Text("天気予報", size=20, weight=ft.FontWeight.BOLD),
        bgcolor="#1976D2",
        color=ft.Colors.WHITE,
    )

    center_dd = ft.Dropdown(label="地方を選択", width=200)
    day_index = 0
    result_row = ft.Row(wrap=True, spacing=20)

    centers = {}
    offices = {}

    # 地域データを読み込む関数
    def load_areas():
        nonlocal centers, offices
        data = requests.get(AREA_URL).json()
        centers = data["centers"]
        offices = data["offices"]
        for c, info in centers.items():
            center_dd.options.append(ft.dropdown.Option(c, info["name"]))
        page.update()

    # 天気情報を表示する関数
    def render_weather():
        result_row.controls.clear()
        if not center_dd.value:
            return

        for office_code in centers[center_dd.value]["children"]:
            try:
                data = requests.get(
                    f"{FORECAST_URL}{office_code}.json", timeout=5
                ).json()

                office_name = offices[office_code]["name"]
                weather_text = data[0]["timeSeries"][0]["areas"][0]["weathers"][day_index]

                temp_series = (
                    data[0]["timeSeries"][2]["areas"][0]
                    if len(data[0]["timeSeries"]) > 2
                    else {}
                )
                temps = temp_series.get("temps", [])
                t_min = temps[day_index * 2] if len(temps) > day_index * 2 else "-"
                t_max = temps[day_index * 2 + 1] if len(temps) > day_index * 2 + 1 else "-"

                result_row.controls.append(
                    ft.Container(
                        width=260,
                        padding=20,
                        bgcolor=weather_color(weather_text),
                        border_radius=16,
                        content=ft.Column(
                            [
                                ft.Text(office_name, weight=ft.FontWeight.BOLD),
                                ft.Text(weather_icons(weather_text), size=40),
                                ft.Text(f"{t_max}℃ / {t_min}℃", size=20),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    )
                )
            except Exception:
                continue

        page.update()

    def on_today(e):
        nonlocal day_index
        day_index = 0
        render_weather()

    def on_tomorrow(e):
        nonlocal day_index
        day_index = 1
        render_weather()

    center_dd.on_change = lambda e: render_weather()
    load_areas()

    page.add(
        ft.Row(
            expand=True,
            controls=[
                # 左：5分の1
                ft.Container(
                    expand=1,
                    padding=10,
                    bgcolor="#E3F2FD",
                    content=ft.Column(
                        [
                            center_dd,
                            ft.ElevatedButton("今日", on_click=on_today),
                            ft.ElevatedButton("明日", on_click=on_tomorrow),
                        ],
                        spacing=10,
                    ),
                ),
                # 右：5分の4
                ft.Container(
                    expand=4,
                    padding=20,
                    content=result_row,
                ),
            ],
        )
    )

ft.app(target=main)
