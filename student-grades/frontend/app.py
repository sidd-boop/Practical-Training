import os

import pandas as pd
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="Student Grade Calculator", page_icon="🎓", layout="wide")
st.title("🎓 Student Grade Calculator")


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
with st.sidebar:
    st.header("Grading policy")
    for name, w in cfg["weights"].items():
        st.write(f"**{name}**: {w * 100:.0f}%")
    st.caption("All marks are out of 100.")
    st.subheader("Grade scale")
    for row in cfg["grade_scale"]:
        st.write(f"`{row['grade']}` — score ≥ {row['min_score']}")

tab_add, tab_view, tab_edit = st.tabs(["➕ Add student", "📋 All students", "✏️ Edit / Delete"])

# ---- Add ---------------------------------------------------------------------
with tab_add:
    with st.form("add_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        name = c1.text_input("Name")
        roll = c2.text_input("Roll number")
        c3, c4, c5, c6 = st.columns(4)
        t1 = c3.number_input("Test 1", 0.0, 100.0, step=0.5)
        t2 = c4.number_input("Test 2", 0.0, 100.0, step=0.5)
        mid = c5.number_input("Midsem", 0.0, 100.0, step=0.5)
        end = c6.number_input("Endsem", 0.0, 100.0, step=0.5)
        submitted = st.form_submit_button("Save student", type="primary")

    if submitted:
        if not name.strip() or not roll.strip():
            st.warning("Name and roll number are required.")
        else:
            resp = api(
                "POST",
                "/students",
                json={"name": name, "roll_number": roll, "test1": t1, "test2": t2,
                      "midsem": mid, "endsem": end},
            )
            if resp.ok:
                s = resp.json()
                st.success(f"Saved {s['name']} ({s['roll_number']})")
                m1, m2 = st.columns(2)
                m1.metric("Final score", s["final_score"])
                m2.metric("Grade", s["grade"])
            else:
                st.error(error_text(resp))

# ---- View --------------------------------------------------------------------
with tab_view:
    students = fetch_students()
    if not students:
        st.info("No students yet. Add one in the first tab.")
    else:
        df = pd.DataFrame(students).rename(columns={
            "roll_number": "Roll No", "name": "Name", "test1": "Test 1", "test2": "Test 2",
            "midsem": "Midsem", "endsem": "Endsem", "final_score": "Final Score", "grade": "Grade",
        })
        q = st.text_input("Search by name or roll number")
        if q:
            mask = df["Name"].str.contains(q, case=False) | df["Roll No"].str.contains(q, case=False)
            df = df[mask]
        st.dataframe(df, use_container_width=True, hide_index=True)

        k1, k2, k3 = st.columns(3)
        k1.metric("Students", len(df))
        if len(df):
            k2.metric("Average score", round(df["Final Score"].mean(), 2))
            k3.metric("Highest score", df["Final Score"].max())
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
            new_name = st.text_input("Name", s["name"])
            c3, c4, c5, c6 = st.columns(4)
            n1 = c3.number_input("Test 1", 0.0, 100.0, s["test1"], step=0.5)
            n2 = c4.number_input("Test 2", 0.0, 100.0, s["test2"], step=0.5)
            nm = c5.number_input("Midsem", 0.0, 100.0, s["midsem"], step=0.5)
            ne = c6.number_input("Endsem", 0.0, 100.0, s["endsem"], step=0.5)
            save = st.form_submit_button("Update", type="primary")
        if save:
            resp = api("PUT", f"/students/{s['roll_number']}", json={
                "name": new_name, "test1": n1, "test2": n2, "midsem": nm, "endsem": ne})
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