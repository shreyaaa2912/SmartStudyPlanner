import streamlit as st
import pandas as pd
import os
from datetime import date

st.set_page_config(page_title="Smart Study Planner", page_icon="📚", layout="wide")

FILE = "study_tasks.csv"

st.title("📚 Smart Study Planner")
st.caption("Plan smarter. Study better!")

name = st.text_input("Enter your name:")
if name:
    st.success(f"Welcome, {name}!")

# Load saved tasks
if "tasks" not in st.session_state:
    if os.path.exists(FILE):
        st.session_state.tasks = pd.read_csv(FILE).to_dict("records")
    else:
        st.session_state.tasks = []

def save_tasks():
    pd.DataFrame(st.session_state.tasks).to_csv(FILE, index=False)

st.subheader("➕ Add a Study Task")

with st.form("task_form"):
    subject = st.text_input("Subject name")
    task = st.text_input("What do you need to study?")
    deadline = st.date_input("Deadline", min_value=date.today())
    priority = st.selectbox("Priority", ["High", "Medium", "Low"])
    submitted = st.form_submit_button("Add Task")

if submitted:
    if subject.strip() and task.strip():
        st.session_state.tasks.append({
            "Subject": subject.strip(),
            "Task": task.strip(),
            "Deadline": str(deadline),
            "Priority": priority,
            "Completed": False
        })
        save_tasks()
        st.success("Task added and saved!")
        st.rerun()
    else:
        st.warning("Please enter both subject and task.")

st.divider()
st.subheader("📋 Your Study Tasks")

tasks = st.session_state.tasks

if tasks:
    completed_count = sum(bool(t["Completed"]) for t in tasks)
    total = len(tasks)
    progress = completed_count / total

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Tasks", total)
    c2.metric("Completed", completed_count)
    c3.metric("Remaining", total - completed_count)

    st.progress(progress, text=f"Study progress: {progress:.0%}")

    for i, item in enumerate(tasks):
        with st.container(border=True):
            left, right = st.columns([4, 1])

            with left:
                st.write(f"**{item['Subject']}** — {item['Task']}")
                st.write(f"📅 Deadline: {item['Deadline']}  |  Priority: {item['Priority']}")

                checked = st.checkbox(
                    "Completed",
                    value=bool(item["Completed"]),
                    key=f"completed_{i}"
                )

                if checked != bool(item["Completed"]):
                    st.session_state.tasks[i]["Completed"] = checked
                    save_tasks()
                    st.rerun()

            with right:
                if st.button("🗑️ Delete", key=f"delete_{i}"):
                    st.session_state.tasks.pop(i)
                    save_tasks()
                    st.rerun()

    st.subheader("📊 Subject-wise Task Summary")
    df = pd.DataFrame(tasks)
    summary = df.groupby("Subject").agg(
        Total_Tasks=("Task", "count"),
        Completed=("Completed", "sum")
    )
    st.bar_chart(summary[["Total_Tasks", "Completed"]])

    st.download_button(
        "⬇️ Download Tasks as CSV",
        data=pd.DataFrame(tasks).to_csv(index=False),
        file_name="my_study_tasks.csv",
        mime="text/csv"
    )
else:
    st.info("No tasks yet. Add your first study task above!")