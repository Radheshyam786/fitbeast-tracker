import os
import time
from datetime import date, datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st


DATA_FILE = "fitbeast_pro.csv"
YOUTUBE_URL = "https://www.youtube.com/watch?v=3UGteR9aihw"
DIFFICULTY_MET = {"Easy": 3.0, "Medium": 5.5, "High": 8.0}
CULT_BANDS = {"Yellow": 10, "Blue": 20, "Green": 30, "Black": 40, "Red": 50}

FITBEAST_ROUTINE = {
    "Monday": {
        "focus": "Chest/Shoulders",
        "exercises": [
            ("Double Arm Press", 66),
            ("One Arm Press", 146),
            ("Fly", 171),
            ("Incline", 190),
            ("Decline", 203),
            ("Shoulder Press", 222),
            ("Front Raise", 243),
            ("Lateral Raise", 265),
            ("Rear Fly", 284),
        ],
    },
    "Tuesday": {
        "focus": "Back/Obliques",
        "exercises": [
            ("Lat Pull", 325),
            ("One Arm Lat", 341),
            ("Bent Row", 366),
            ("Standing Row", 383),
            ("Good Morning", 403),
            ("Side Bend", 427),
            ("Torso Rotation", 453),
            ("Wood Chopper", 485),
        ],
    },
    "Wednesday": {
        "focus": "Legs",
        "exercises": [
            ("Squats", 537),
            ("Narrow Squats", 565),
            ("Lunges", 593),
            ("Deadlift", 639),
            ("Hip Extension", 671),
            ("Glutes", 715),
        ],
    },
    "Thursday": {
        "focus": "Arms",
        "exercises": [
            ("Skull Crunchers", 765),
            ("OH Tricep", 781),
            ("Standing Tricep", 798),
            ("Kickbacks", 826),
            ("Bicep ISO", 850),
            ("Preacher Curls", 877),
            ("Crucifix", 899),
        ],
    },
    "Friday": {
        "focus": "Core/Abs",
        "exercises": [
            ("OH Crunches", 952),
            ("Kneeling Crunches", 973),
            ("Bicycles", 992),
            ("Torso Rotation", 1010),
        ],
    },
}

CSV_COLUMNS = [
    "record_type",
    "timestamp",
    "date",
    "weight_kg",
    "height_cm",
    "exercise_name",
    "muscle_group",
    "selected_bands",
    "total_resistance_lbs",
    "sets",
    "reps",
    "difficulty",
    "duration_min",
    "met",
    "calories_burned",
    "session_status",
    "draft_payload",
    "session_elapsed_sec",
]


def initialize_data_file() -> None:
    if not os.path.exists(DATA_FILE):
        pd.DataFrame(columns=CSV_COLUMNS).to_csv(DATA_FILE, index=False)
        return
    existing = pd.read_csv(DATA_FILE)
    missing = [col for col in CSV_COLUMNS if col not in existing.columns]
    if missing:
        for col in missing:
            existing[col] = None
        existing.to_csv(DATA_FILE, index=False)


def load_data() -> pd.DataFrame:
    initialize_data_file()
    df = pd.read_csv(DATA_FILE)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


def append_rows(rows: list[dict]) -> None:
    initialize_data_file()
    current_df = pd.read_csv(DATA_FILE)
    out_df = pd.concat([current_df, pd.DataFrame(rows)], ignore_index=True)
    out_df.to_csv(DATA_FILE, index=False)


def latest_profile(df: pd.DataFrame) -> tuple[float, float]:
    if df.empty:
        return 70.0, 170.0
    profile_df = df[df["record_type"] == "profile"]
    if profile_df.empty:
        return 70.0, 170.0
    latest_row = profile_df.sort_values("date").iloc[-1]
    return float(latest_row["weight_kg"]), float(latest_row["height_cm"])


def calculate_calories(weight_kg: float, met: float, duration_min: float) -> float:
    return ((met * weight_kg * 3.5) / 200) * duration_min


def calculate_streak(workout_df: pd.DataFrame) -> int:
    if workout_df.empty:
        return 0
    unique_days = {
        d.date() for d in pd.to_datetime(workout_df["date"], errors="coerce").dropna().dt.normalize()
    }
    streak = 0
    probe = date.today()
    while probe in unique_days:
        streak += 1
        probe -= timedelta(days=1)
    return streak


def session_key() -> str:
    return f"fitbeast_session_{date.today().isoformat()}"


def workout_day() -> str:
    today_name = datetime.today().strftime("%A")
    if today_name not in FITBEAST_ROUTINE:
        return "Monday"
    return today_name


def initialize_session() -> None:
    key = session_key()
    if key in st.session_state:
        return
    day = workout_day()
    focus = FITBEAST_ROUTINE[day]["focus"]
    st.session_state[key] = [
        {
            "exercise_name": name,
            "muscle_group": focus,
            "start_sec": start_sec,
            "cult_band": "Blue",
            "difficulty": "Medium",
            "sets": 3,
            "reps": 12,
            "duration_min": 8,
            "selected": True,
        }
        for name, start_sec in FITBEAST_ROUTINE[day]["exercises"]
    ]


def ensure_stopwatch_state() -> None:
    if "workout_elapsed" not in st.session_state:
        st.session_state["workout_elapsed"] = 0.0
    if "workout_running" not in st.session_state:
        st.session_state["workout_running"] = False
    if "workout_visible" not in st.session_state:
        st.session_state["workout_visible"] = False


def update_stopwatch() -> float:
    if st.session_state.get("workout_running", False):
        elapsed = time.time() - st.session_state.get("workout_start_ts", time.time())
        st.session_state["workout_elapsed"] = elapsed
    return float(st.session_state.get("workout_elapsed", 0.0))


st.set_page_config(page_title="FitBeast Accessible Dashboard", layout="wide")

st.markdown(
    """
    <style>
        .stApp {
            background: radial-gradient(circle at 0% 0%, #1f2937 0%, #0b1220 45%, #05090f 100%);
            color: #f8fafc;
        }
        .main .block-container {
            max-width: 95%;
            padding-top: 1rem;
            padding-right: 1rem;
            padding-left: 1rem;
        }
        html, body, [class*="css"] {
            font-size: 20px;
        }
        h1 { font-size: 3rem !important; }
        h2 { font-size: 2.2rem !important; }
        h3 { font-size: 1.8rem !important; }
        .stButton > button {
            height: 4em;
            font-size: 24px !important;
        }
        .glass-card {
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.25);
            border-radius: 24px;
            padding: 1rem 1.2rem;
            margin-bottom: 1rem;
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
        }
        .exercise-title {
            font-size: 2.15rem;
            font-weight: 800;
            line-height: 1.1;
            color: #ffffff;
            margin-bottom: 0.25rem;
        }
        .focus-subtitle {
            color: #93c5fd;
            font-size: 1.2rem;
            margin-bottom: 0.5rem;
        }
        .stopwatch {
            font-size: 3.25rem;
            font-weight: 900;
            text-align: center;
            letter-spacing: 2px;
            color: #f8fafc;
            margin: 0.5rem 0;
        }
        .icon-button button {
            font-size: 1.05rem !important;
            font-weight: 800 !important;
            border-radius: 12px !important;
            border: 2px solid rgba(255, 255, 255, 0.55) !important;
        }
        .save-button button {
            font-size: 1.2rem !important;
            font-weight: 900 !important;
            min-height: 3rem !important;
            background: #0ea5e9 !important;
            color: #041019 !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

data_df = load_data()
profile_weight, profile_height = latest_profile(data_df)
workout_df = data_df[data_df["record_type"] == "workout"].copy() if not data_df.empty else pd.DataFrame()

total_burn = float(workout_df["calories_burned"].fillna(0).sum()) if not workout_df.empty else 0.0
current_streak = calculate_streak(workout_df)
bmi = profile_weight / ((profile_height / 100) ** 2)

st.markdown("<div style='padding: 0.8rem 1.2rem;'>", unsafe_allow_html=True)
st.title("FitBeast Pro Dashboard")
st.caption("Accessible, full-width resistance band planner with guided video cards.")

metric_a, metric_b, metric_c = st.columns(3)
metric_a.metric("Total Burn", f"{total_burn:.1f} kcal")
metric_b.metric("Current Streak", f"{current_streak} day(s)")
metric_c.metric("BMI", f"{bmi:.1f}")
st.markdown("</div>", unsafe_allow_html=True)

with st.sidebar:
    st.header("Profile")
    weight_kg = st.number_input(
        "Weight (kg)", min_value=30.0, max_value=250.0, value=float(profile_weight), step=0.1
    )
    height_cm = st.number_input(
        "Height (cm)", min_value=120.0, max_value=230.0, value=float(profile_height), step=0.1
    )
    if st.button("Update Profile", use_container_width=True):
        append_rows(
            [
                {
                    "record_type": "profile",
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "date": date.today().isoformat(),
                    "weight_kg": weight_kg,
                    "height_cm": height_cm,
                    "exercise_name": "",
                    "muscle_group": "",
                    "selected_bands": "",
                    "total_resistance_lbs": None,
                    "sets": None,
                    "reps": None,
                    "difficulty": "",
                    "duration_min": None,
                    "met": None,
                    "calories_burned": None,
                    "session_status": "",
                    "draft_payload": "",
                    "session_elapsed_sec": None,
                }
            ]
        )
        st.success("Profile saved to fitbeast_pro.csv")
        st.rerun()

tab_workout, tab_analytics = st.tabs(["Workout", "Analytics"])

with tab_workout:
    initialize_session()
    ensure_stopwatch_state()
    day = workout_day()
    day_focus = FITBEAST_ROUTINE[day]["focus"]
    key = session_key()
    session_exercises = st.session_state[key]

    top_left, top_right = st.columns([2, 1])
    with top_left:
        st.subheader(f"{day}: {day_focus}")
    with top_right:
        if st.button("▶ START WORKOUT", use_container_width=True):
            st.session_state["workout_visible"] = True
            st.session_state["workout_running"] = True
            st.session_state["workout_start_ts"] = time.time() - st.session_state["workout_elapsed"]

    if st.session_state.get("workout_visible", False):
        elapsed = update_stopwatch()
        mins, secs = divmod(int(elapsed), 60)
        st.markdown(
            f"<div class='glass-card'><div class='stopwatch'>⏱ {mins:02d}:{secs:02d}</div></div>",
            unsafe_allow_html=True,
        )
        sw1, sw2 = st.columns(2)
        with sw1:
            if st.button("⏸ PAUSE", use_container_width=True):
                st.session_state["workout_running"] = False
                update_stopwatch()
        with sw2:
            if st.button("↺ RESET", use_container_width=True):
                st.session_state["workout_running"] = False
                st.session_state["workout_elapsed"] = 0.0
        if st.session_state.get("workout_running", False):
            time.sleep(1)
            st.rerun()

    for idx, ex in enumerate(session_exercises):
        if "selected" not in ex:
            ex["selected"] = True
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        video_col, control_col = st.columns([3, 2])

        with video_col:
            st.video(
                YOUTUBE_URL,
                start_time=int(ex["start_sec"]),
                width="stretch",
            )

        with control_col:
            st.markdown(f"<div class='exercise-title'>{ex['exercise_name']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='focus-subtitle'>{ex['muscle_group']}</div>", unsafe_allow_html=True)

            ex["cult_band"] = st.selectbox(
                "Cult Band",
                options=list(CULT_BANDS.keys()),
                index=list(CULT_BANDS.keys()).index(ex.get("cult_band", "Blue")),
                key=f"band_{idx}_{key}",
            )
            ex["difficulty"] = st.radio(
                "Difficulty",
                options=list(DIFFICULTY_MET.keys()),
                index=list(DIFFICULTY_MET.keys()).index(ex.get("difficulty", "Medium")),
                horizontal=True,
                key=f"difficulty_{idx}_{key}",
            )

            set_col, rep_col = st.columns(2)
            with set_col:
                ex["sets"] = st.number_input(
                    "Sets",
                    min_value=1,
                    max_value=12,
                    value=int(ex.get("sets", 3)),
                    key=f"sets_{idx}_{key}",
                )
            with rep_col:
                ex["reps"] = st.number_input(
                    "Reps",
                    min_value=1,
                    max_value=50,
                    value=int(ex.get("reps", 12)),
                    key=f"reps_{idx}_{key}",
                )

            ex["duration_min"] = st.number_input(
                "Duration (min)",
                min_value=3,
                max_value=60,
                value=int(ex.get("duration_min", 8)),
                key=f"duration_{idx}_{key}",
            )

            act1, act2, act3 = st.columns(3)
            with act1:
                st.markdown("<div class='icon-button'>", unsafe_allow_html=True)
                if st.button("⏭ SKIP", key=f"skip_{idx}_{key}", use_container_width=True):
                    ex["selected"] = False
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            with act2:
                st.markdown("<div class='icon-button'>", unsafe_allow_html=True)
                if st.button("➕ ADD SET", key=f"add_set_{idx}_{key}", use_container_width=True):
                    ex["sets"] = min(int(ex.get("sets", 3)) + 1, 12)
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            with act3:
                st.markdown("<div class='icon-button'>", unsafe_allow_html=True)
                if st.button("🧬 DOUBLE", key=f"double_{idx}_{key}", use_container_width=True):
                    session_exercises.insert(idx + 1, ex.copy())
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

            if not ex.get("selected", True):
                st.warning("Marked as skipped.")

        st.markdown("</div>", unsafe_allow_html=True)

    active_ex = [x for x in session_exercises if x.get("selected", True)]
    total_resistance = sum(CULT_BANDS[x["cult_band"]] * int(x.get("sets", 1)) for x in active_ex)
    total_volume = sum(
        CULT_BANDS[x["cult_band"]] * int(x.get("sets", 1)) * int(x.get("reps", 1)) for x in active_ex
    )
    session_calories = sum(
        calculate_calories(weight_kg, DIFFICULTY_MET[x["difficulty"]], float(x["duration_min"]))
        for x in active_ex
    )

    s1, s2, s3 = st.columns(3)
    s1.metric("Session Calories (Est.)", f"{session_calories:.1f} kcal")
    s2.metric("Total Resistance", f"{total_resistance:.0f} lbs")
    s3.metric("Training Volume", f"{total_volume:.0f} lb-reps")

    st.markdown("<div class='save-button'>", unsafe_allow_html=True)
    save_clicked = st.button("💾 SAVE WORKOUT", type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if save_clicked:
        if not active_ex:
            st.warning("No active exercises to save.")
        else:
            rows = []
            elapsed_sec = float(st.session_state.get("workout_elapsed", 0.0))
            for ex in active_ex:
                resistance = CULT_BANDS[ex["cult_band"]]
                met_value = DIFFICULTY_MET[ex["difficulty"]]
                duration = float(ex["duration_min"])
                calories = calculate_calories(weight_kg, met_value, duration)
                rows.append(
                    {
                        "record_type": "workout",
                        "timestamp": datetime.now().isoformat(timespec="seconds"),
                        "date": date.today().isoformat(),
                        "weight_kg": weight_kg,
                        "height_cm": height_cm,
                        "exercise_name": ex["exercise_name"],
                        "muscle_group": ex["muscle_group"],
                        "selected_bands": ex["cult_band"],
                        "total_resistance_lbs": resistance,
                        "sets": int(ex["sets"]),
                        "reps": int(ex["reps"]),
                        "difficulty": ex["difficulty"],
                        "duration_min": duration,
                        "met": met_value,
                        "calories_burned": round(calories, 2),
                        "session_status": "closed",
                        "draft_payload": "",
                        "session_elapsed_sec": elapsed_sec,
                    }
                )
            append_rows(rows)
            st.success(f"Workout saved to {DATA_FILE} ({len(rows)} records).")
            st.session_state["workout_running"] = False
            st.session_state["workout_elapsed"] = 0.0
            st.rerun()

with tab_analytics:
    refreshed_df = load_data()
    workout_logs = (
        refreshed_df[refreshed_df["record_type"] == "workout"].copy()
        if not refreshed_df.empty
        else pd.DataFrame()
    )
    profile_logs = (
        refreshed_df[refreshed_df["record_type"] == "profile"].copy()
        if not refreshed_df.empty
        else pd.DataFrame()
    )

    st.download_button(
        "Download CSV",
        data=refreshed_df.to_csv(index=False).encode("utf-8"),
        file_name="fitbeast_pro_export.csv",
        mime="text/csv",
        use_container_width=True,
    )

    if workout_logs.empty:
        st.info("No workout logs found yet.")
    else:
        workout_logs["date"] = pd.to_datetime(workout_logs["date"], errors="coerce")
        workout_logs["week"] = workout_logs["date"].dt.to_period("W").astype(str)
        weekly_burn = (
            workout_logs.groupby("week", as_index=False)["calories_burned"].sum().sort_values("week")
        )

        if not profile_logs.empty:
            profile_logs["date"] = pd.to_datetime(profile_logs["date"], errors="coerce")
            monthly_source = profile_logs[["date", "weight_kg"]].dropna()
        else:
            monthly_source = workout_logs[["date", "weight_kg"]].dropna()

        monthly_source["month"] = monthly_source["date"].dt.to_period("M").astype(str)
        monthly_weight = (
            monthly_source.groupby("month", as_index=False)["weight_kg"].mean().sort_values("month")
        )

        weekly_fig = px.bar(
            weekly_burn,
            x="week",
            y="calories_burned",
            title="Weekly Burn",
            template="plotly_dark",
        )
        weekly_fig.update_layout(
            paper_bgcolor="#0b1220",
            plot_bgcolor="#0b1220",
            font_color="#f8fafc",
            margin=dict(l=20, r=20, t=60, b=20),
        )
        st.plotly_chart(weekly_fig, use_container_width=True)

        monthly_fig = px.line(
            monthly_weight,
            x="month",
            y="weight_kg",
            markers=True,
            title="Monthly Weight Trend",
            template="plotly_dark",
        )
        monthly_fig.update_layout(
            paper_bgcolor="#0b1220",
            plot_bgcolor="#0b1220",
            font_color="#f8fafc",
            margin=dict(l=20, r=20, t=60, b=20),
        )
        st.plotly_chart(monthly_fig, use_container_width=True)
