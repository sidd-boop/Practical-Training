import os
import re

import pandas as pd
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="Student Grade Calculator", page_icon="🎓", layout="wide")
st.title("🎓 Student Grade Calculator")

ROLL_NUMBER_REGEX = r"^\d{3}[A-Z]{2}\d{3}$"
NAME_REGEX = r"^[A-Za-z][A-Za-z \-]*$"


def api(method: str, path: str, **kwargs):
    try:
        return requests.request(method, f"{API_URL}{path}", timeout=10, **kwargs)
    except requests.RequestException as e:
        st.error(f"Cannot reach backend at {API_URL}: {e}")
        st.stop()


def error_text(resp: requests.Response) -> str:
    try:
        detail = resp.json().get("detail", resp.text)
    except ValueError:
        return resp.text
    if isinstance(detail, list):  # pydantic validation errors
        return "; ".join(f"{'.'.join(map(str, d['loc'][1:]))}: {d['msg']}" for d in detail)
    return str(detail)


def fetch_students() -> list[dict]:
    resp = api("GET", "/students")
    return resp.json() if resp.ok else []


# ---- Sidebar: current policy -------------------------------------------------
cfg = api("GET", "/config").json()
max_marks = cfg["max_marks"]

with st.sidebar:
    st.header("Grading policy")
    for name, w in cfg["weights"].items():
        st.write(f"**{name}**: {w * 100:.0f}%")
    st.subheader("Maximum marks")
    st.write(f"Each Quiz: **{max_marks['quiz']}**")
    st.write(f"Midsem: **{max_marks['midsem']}**")
    st.write(f"Endsem: **{max_marks['endsem']}**")
    st.subheader("Grade scale")
    for row in cfg["grade_scale"]:
        st.write(f"`{row['grade']}` — score ≥ {row['min_score']}")

tab_add, tab_view, tab_edit = st.tabs(["➕ Add student", "📋 All students", "✏️ Edit / Delete"])

# ---- Add ---------------------------------------------------------------------
with tab_add:
    if "clear_add_form" not in st.session_state:
        st.session_state.clear_add_form = False

    if st.session_state.clear_add_form:
        st.session_state.add_name = ""
        st.session_state.add_roll = ""
        st.session_state.add_q1 = 0.0
        st.session_state.add_q2 = 0.0
        st.session_state.add_mid = 0.0
        st.session_state.add_end = 0.0
        st.session_state.clear_add_form = False

    with st.form("add_form"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Name", key="add_name", help="Letters, spaces, and hyphens only")
        roll = c2.text_input(
            "Roll number", key="add_roll",
            help="Pattern: 3 digits + 2 uppercase letters + 3 digits (e.g. 241DS030)",
        )
        c3, c4, c5, c6 = st.columns(4)
        q1 = c3.number_input("Quiz 1", min_value=0.0, max_value=float(max_marks["quiz"]), step=0.5, key="add_q1", help=f"Max marks: {max_marks['quiz']}")
        q2 = c4.number_input("Quiz 2", min_value=0.0, max_value=float(max_marks["quiz"]), step=0.5, key="add_q2", help=f"Max marks: {max_marks['quiz']}")
        mid = c5.number_input("Midsem", min_value=0.0, max_value=float(max_marks["midsem"]), step=0.5, key="add_mid", help=f"Max marks: {max_marks['midsem']}")
        end = c6.number_input("Endsem", min_value=0.0, max_value=float(max_marks["endsem"]), step=0.5, key="add_end", help=f"Max marks: {max_marks['endsem']}")
        submitted = st.form_submit_button("Save student", type="primary")

    if submitted:
        errors = []
        if not name.strip():
            errors.append("Name is required.")
        elif not re.match(NAME_REGEX, name.strip()):
            errors.append("Name must contain only letters, spaces, and hyphens.")
        if not roll.strip():
            errors.append("Roll number is required.")
        elif not re.match(ROLL_NUMBER_REGEX, roll.strip().upper()):
            errors.append("Roll number must follow the pattern like 241DS030 (3 digits, 2 uppercase letters, 3 digits).")

        if errors:
            for e in errors:
                st.warning(e)
        else:
            resp = api(
                "POST",
                "/students",
                json={
                    "name": name,
                    "roll_number": roll,
                    "quiz1": q1,
                    "quiz2": q2,
                    "midsem": mid,
                    "endsem": end,
                },
            )
            if resp.ok:
                s = resp.json()
                st.success(f"Saved {s['name']} ({s['roll_number']})")
                m1, m2 = st.columns(2)
                m1.metric("Final score", s["final_score"])
                m2.metric("Grade", s["grade"])
                st.session_state.clear_add_form = True
                st.rerun()
            else:
                st.error(error_text(resp))

# ---- View --------------------------------------------------------------------
with tab_view:
    students = fetch_students()
    if not students:
        st.info("No students yet. Add one in the first tab.")
    else:
        df = pd.DataFrame(students).rename(columns={
            "roll_number": "Roll No", "name": "Name",
            "quiz1": f"Quiz 1 (/{max_marks['quiz']})",
            "quiz2": f"Quiz 2 (/{max_marks['quiz']})",
            "midsem": f"Midsem (/{max_marks['midsem']})",
            "endsem": f"Endsem (/{max_marks['endsem']})",
            "final_score": "Final Score", "grade": "Grade",
        })
        q = st.text_input("Search by name or roll number")
        if q:
            mask = df["Name"].str.contains(q, case=False) | df["Roll No"].str.contains(q, case=False)
            df = df[mask]
        st.dataframe(df, use_container_width=True, hide_index=True)

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Students", len(df))
        if len(df):
            k2.metric("Average score", round(df["Final Score"].mean(), 2))
            k3.metric("Highest score", df["Final Score"].max())
            k4.metric("Lowest score", df["Final Score"].min())
            order = [r["grade"] for r in cfg["grade_scale"]]
            dist = df["Grade"].value_counts().reindex(order, fill_value=0)
            st.bar_chart(dist)
        st.download_button("Download CSV", df.to_csv(index=False), "students.csv", "text/csv")

# ---- Edit / Delete -----------------------------------------------------------
with tab_edit:
    students = fetch_students()
    if not students:
        st.info("Nothing to edit yet.")
    else:
        options = {f"{s['roll_number']} — {s['name']}": s for s in students}
        s = options[st.selectbox("Select student", list(options))]
        with st.form(f"edit_{s['roll_number']}"):
            new_name = st.text_input("Name", s["name"], help="Letters, spaces, and hyphens only")
            c3, c4, c5, c6 = st.columns(4)
            n1 = c3.number_input("Quiz 1", min_value=0.0, max_value=float(max_marks["quiz"]), value=s["quiz1"], step=0.5, help=f"Max marks: {max_marks['quiz']}")
            n2 = c4.number_input("Quiz 2", min_value=0.0, max_value=float(max_marks["quiz"]), value=s["quiz2"], step=0.5, help=f"Max marks: {max_marks['quiz']}")
            nm = c5.number_input("Midsem", min_value=0.0, max_value=float(max_marks["midsem"]), value=s["midsem"], step=0.5, help=f"Max marks: {max_marks['midsem']}")
            ne = c6.number_input("Endsem", min_value=0.0, max_value=float(max_marks["endsem"]), value=s["endsem"], step=0.5, help=f"Max marks: {max_marks['endsem']}")
            save = st.form_submit_button("Update", type="primary")

        if save:
            edit_errors = []
            if new_name.strip() and not re.match(NAME_REGEX, new_name.strip()):
                edit_errors.append("Name must contain only letters, spaces, and hyphens.")
            if edit_errors:
                for e in edit_errors:
                    st.warning(e)
            else:
                resp = api("PUT", f"/students/{s['roll_number']}", json={
                    "name": new_name, "quiz1": n1, "quiz2": n2, "midsem": nm, "endsem": ne})
                if resp.ok:
                    u = resp.json()
                    st.success(f"Updated. Final score: {u['final_score']} · Grade: {u['grade']}")
                else:
                    st.error(error_text(resp))

        st.divider()
        if st.button(f"🗑️ Delete {s['roll_number']}"):
            resp = api("DELETE", f"/students/{s['roll_number']}")
            if resp.ok:
                st.success("Deleted. Refresh the page to update the list.")
            else:
                st.error(error_text(resp))
