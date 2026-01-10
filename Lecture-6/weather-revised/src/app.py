import flet as ft
import sqlite3

DB_NAME = "/Users/takahashikoudai/Lecture/dsprog2/Lecture-6/weather-revised/weather.db"

# =========================
# 天気アイコンと背景色
# =========================
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

# =========================
# DBから天気情報を取得
# =========================
def fetch_weather_from_db(center_code, day_index):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # center_codeからoffice_code一覧を取得
    cur.execute("""
        SELECT office_code, office_name
        FROM offices
        WHERE center_code = ?
        ORDER BY office_name
    """, (center_code,))
    offices = cur.fetchall()

    result = []
    for office_code, office_name in offices:
        cur.execute("""
            SELECT weather, temp_max, temp_min
            FROM forecasts
            WHERE office_code = ? AND forecast_date = ?
        """, (office_code, day_index))
        row = cur.fetchone()
        if row:
            weather, t_max, t_min = row
            result.append((office_name, weather, t_max, t_min))

    conn.close()
    return result

# =========================
# Fletアプリ本体
# =========================
def main(page: ft.Page):
    page.title = "地方別 天気予報（DB版）"
    page.bgcolor = "#EEF6FF"

    page.appbar = ft.AppBar(
        title=ft.Text("天気予報", size=20, weight=ft.FontWeight.BOLD),
        bgcolor="#1976D2",
        color=ft.Colors.WHITE,
    )

    # ドロップダウン・ボタン
    center_dd = ft.Dropdown(label="地方を選択", width=200)
    day_index = 0
    result_row = ft.Row(wrap=True, spacing=20)

    # centersをDBから取得
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT center_code, center_name FROM centers ORDER BY center_name")
    centers = {row[0]: row[1] for row in cur.fetchall()}
    conn.close()

    for c_code, c_name in centers.items():
        center_dd.options.append(ft.dropdown.Option(c_code, c_name))

    # =========================
    # 天気情報表示
    # =========================
    def render_weather():
        result_row.controls.clear()
        if not center_dd.value:
            page.update()
            return

        rows = fetch_weather_from_db(center_dd.value, day_index)
        for office_name, weather, t_max, t_min in rows:
            result_row.controls.append(
                ft.Container(
                    width=260,
                    padding=20,
                    bgcolor=weather_color(weather),
                    border_radius=16,
                    content=ft.Column(
                        [
                            ft.Text(office_name, weight=ft.FontWeight.BOLD),
                            ft.Text(weather_icons(weather), size=40),
                            ft.Text(f"{t_max}℃ / {t_min}℃", size=20),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                )
            )
        page.update()

    # =========================
    # ボタン処理
    # =========================
    def on_today(e):
        nonlocal day_index
        day_index = 0
        render_weather()

    def on_tomorrow(e):
        nonlocal day_index
        day_index = 1
        render_weather()

    center_dd.on_change = lambda e: render_weather()

    # =========================
    # ページ追加
    # =========================
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

