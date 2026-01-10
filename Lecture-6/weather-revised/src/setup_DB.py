import sqlite3
import requests
import os
import time

# =========================
# 設定（★絶対パスで統一）
# =========================
DB_NAME = "/Users/takahashikoudai/Lecture/dsprog2/Lecture-6/weather-revised/weather.db"

AREA_URL = "https://www.jma.go.jp/bosai/common/const/area.json"
FORECAST_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/{code}.json"

# =========================
# DB初期化
# =========================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS centers (
        center_code TEXT PRIMARY KEY,
        center_name TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS offices (
        office_code TEXT PRIMARY KEY,
        office_name TEXT,
        center_code TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS forecasts (
        office_code TEXT,
        forecast_date INTEGER,
        weather TEXT,
        temp_min TEXT,
        temp_max TEXT,
        PRIMARY KEY (office_code, forecast_date)
    )
    """)

    conn.commit()
    conn.close()

# =========================
# 地域データ保存
# =========================
def save_areas_to_db():
    res = requests.get(AREA_URL)
    res.raise_for_status()

    data = res.json()
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    for c, info in data["centers"].items():
        cur.execute(
            "INSERT OR IGNORE INTO centers VALUES (?, ?)",
            (c, info["name"])
        )

    for o, info in data["offices"].items():
        cur.execute(
            "INSERT OR IGNORE INTO offices VALUES (?, ?, ?)",
            (o, info["name"], info["parent"])
        )

    conn.commit()
    conn.close()

# =========================
# 天気予報保存
# =========================
def save_forecast_to_db(office_code, data):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    area = data[0]["timeSeries"][0]["areas"][0]

    temps = (
        data[0]["timeSeries"][2]["areas"][0]["temps"]
        if len(data[0]["timeSeries"]) > 2
        else []
    )

    for day in range(2):  # 今日・明日
        weather = area["weathers"][day]
        t_min = temps[day * 2] if len(temps) > day * 2 else "-"
        t_max = temps[day * 2 + 1] if len(temps) > day * 2 + 1 else "-"

        cur.execute("""
            REPLACE INTO forecasts
            (office_code, forecast_date, weather, temp_min, temp_max)
            VALUES (?, ?, ?, ?, ?)
        """, (office_code, day, weather, t_min, t_max))

    conn.commit()
    conn.close()

# =========================
# 実行
# =========================
init_db()
save_areas_to_db()

area_data = requests.get(AREA_URL).json()
OFFICE_CODES = list(area_data["offices"].keys())

for code in OFFICE_CODES:
    url = FORECAST_URL.format(code=code)
    res = requests.get(url)

    print(code, res.status_code)

    # ★ ここが JSONDecodeError 対策の本体
    if res.headers.get("Content-Type", "").startswith("application/json"):
        forecast = res.json()
        save_forecast_to_db(code, forecast)
    else:
        print("⚠ JSONではないレスポンス:", code)
        print(res.text[:100])

    time.sleep(0.2)  # ★ アクセス間隔（重要）

print("✅ DB 完全セットアップ完了")
print("DB:", DB_NAME)
print("exists:", os.path.exists(DB_NAME))
