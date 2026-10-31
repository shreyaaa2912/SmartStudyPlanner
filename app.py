import streamlit as st
import pandas as pd
import os
from datetime import date
from dotenv import load_dotenv
from supabase import create_client

st.set_page_config(
    page_title="Smart Study Planner",
    page_icon="📚",
    layout="wide"
)

# Supabase connection
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Supabase URL or Key is missing in your .env file.")
    st.stop()

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("📚 Smart Study Planner")
st.caption("Plan smarter. Study better!")

# Login session
if "user" not in st.session_state:
    st.session_state.user = None
    st.session_state.access_token = None
    st.session_state.refresh_token = None

if st.session_state.user is None:
    st.subheader("Login / Sign Up")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Login"):
            try:
                response = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                st.session_state.user = response.user
                st.session_state.access_token = response.session.access_token
                st.session_state.refresh_token = response.session.refresh_token
                st.rerun()
            except Exception as e:
                st.error(f"Login failed: {e}")

    with col2:
        if st.button("Sign Up"):
            try:
                response = supabase.auth.sign_up({
                    "email": email,
                    "password": password
                })
                st.success("Sign-up request submitted.")
                st.info("Check your email to verify your account.")
            except Exception as e:
                st.error(f"Sign-up failed: {e}")

    st.stop()

# Logged-in user
user_id = st.session_state.user.id

if st.button("Logout"):
    supabase.auth.sign_out()
    st.session_state.user = None
    st.session_state.pop("tasks", None)
    st.rerun()

# Load tasks from Supabase
def load_tasks():
    response = (
        supabase.table("study_tasks")
        .select("*")
        .eq("user_id", user_id)
        .execute()
    )

    tasks = []
    for row in response.data:
        tasks.append({
            "id": row["id"],
            "Subject": row["title"],
            "Task": row["description"] or "",
            "Deadline": row["due_date"],
            "Priority": row.get("priority") or "Medium",
            "Completed": row["completed"]
        })

    return tasks


if "tasks" not in st.session_state:
    try:
        st.session_state.tasks = load_tasks()
    except Exception as e:
        st.error(f"Could not load tasks: {e}")
        st.stop()

st.subheader("➕ Add a Study Task")

with st.form("task_form"):
    subject = st.text_input("Subject name")
    task = st.text_input("What do you need to study?")
    deadline = st.date_input("Deadline", min_value=date.today())
    priority = st.selectbox("Priority", ["High", "Medium", "Low"])
    submitted = st.form_submit_button("Add Task")

if submitted:
    if subject.strip() and task.strip():
        try:
            supabase.table("study_tasks").insert({
                "user_id": user_id,
                "title": subject.strip(),
                "description": task.strip(),
                "due_date": str(deadline),
                "priority": priority,
                "completed": False
            }).execute()

            st.session_state.tasks = load_tasks()
            st.success("Task added successfully!")
            st.rerun()

        except Exception as e:
            st.error(f"Could not save task: {e}")
    else:
        st.warning("Please enter both subject and task.")

st.divider()
st.subheader("📋 Your Study Tasks")

tasks = st.session_state.tasks

if tasks:
    completed_count = sum(bool(t["Completed"]) for t in tasks)
    total = len(tasks)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Tasks", total)
    c2.metric("Completed", completed_count)
    c3.metric("Remaining", total - completed_count)

    st.progress(
        completed_count / total,
        text=f"Study progress: {completed_count / total:.0%}"
    )

    for i, item in enumerate(tasks):
        with st.container(border=True):
            left, right = st.columns([4, 1])

            with left:
                st.write(f"**{item['Subject']}** — {item['Task']}")
                st.write(
                    f"📅 Deadline: {item['Deadline']} | "
                    f"Priority: {item['Priority']}"
                )

                checked = st.checkbox(
                    "Completed",
                    value=bool(item["Completed"]),
                    key=f"completed_{item['id']}"
                )

                if checked != bool(item["Completed"]):
                    try:
                        supabase.table("study_tasks").update({
                            "completed": checked
                        }).eq("id", item["id"]).eq(
                            "user_id", user_id
                        ).execute()

                        st.session_state.tasks = load_tasks()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Could not update task: {e}")

            with right:
                if st.button("🗑️ Delete", key=f"delete_{item['id']}"):
                    try:
                        supabase.table("study_tasks").delete().eq(
                            "id", item["id"]
                        ).eq("user_id", user_id).execute()

                        st.session_state.tasks = load_tasks()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Could not delete task: {e}")

    st.subheader("📊 Subject-wise Task Summary")

    df = pd.DataFrame(tasks)
    summary = df.groupby("Subject").agg(
        Total_Tasks=("Task", "count"),
        Completed=("Completed", "sum")
    )
    st.bar_chart(summary[["Total_Tasks", "Completed"]])

    st.download_button(
        "⬇️ Download Tasks as CSV",
        data=df.drop(columns=["id"]).to_csv(index=False),
        file_name="my_study_tasks.csv",
        mime="text/csv"
    )

else:
    st.info("No tasks yet. Add your first study task above!")
import pandas as pd
import os
from datetime import date
from dotenv import load_dotenv
from supabase import create_client

st.set_page_config(
    page_title="Smart Study Planner",
    page_icon="📚",
    layout="wide"
)

# Supabase connection
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Supabase URL or Key is missing in your .env file.")
    st.stop()

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("📚 Smart Study Planner")
st.caption("Plan smarter. Study better!")

# Login session
if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.subheader("Login / Sign Up")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Login"):
            try:
                response = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                st.session_state.user = response.user
                st.rerun()
            except Exception as e:
                st.error(f"Login failed: {e}")

    with col2:
        if st.button("Sign Up"):
            try:
                response = supabase.auth.sign_up({
                    "email": email,
                    "password": password
                })
                st.success("Sign-up request submitted.")
                st.info("Check your email to verify your account.")
            except Exception as e:
                st.error(f"Sign-up failed: {e}")

    st.stop()

# Logged-in user
user_id = st.session_state.user.id

if st.button("Logout", key="logout_button"):
    supabase.auth.sign_out()
    st.session_state.user = None
    st.session_state.pop("tasks", None)
    st.rerun()

# Load tasks from Supabase
def load_tasks():
    response = (
        supabase.table("study_tasks")
        .select("*")
        .eq("user_id", user_id)
        .execute()
    )

    tasks = []
    for row in response.data:
        tasks.append({
            "id": row["id"],
            "Subject": row["title"],
            "Task": row["description"] or "",
            "Deadline": row["due_date"],
            "Priority": row.get("priority") or "Medium",
            "Completed": row["completed"]
        })

    return tasks


if "tasks" not in st.session_state:
    try:
        st.session_state.tasks = load_tasks()
    except Exception as e:
        st.error(f"Could not load tasks: {e}")
        st.stop()

st.subheader("➕ Add a Study Task")

with st.form("study_task_entry_form"):
    subject = st.text_input("Subject name")
    task = st.text_input("What do you need to study?")
    deadline = st.date_input("Deadline", min_value=date.today())
    priority = st.selectbox("Priority", ["High", "Medium", "Low"])
    submitted = st.form_submit_button("Add Task")

if submitted:
    if subject.strip() and task.strip():
        try:
            supabase.table("study_tasks").insert({
                "user_id": user_id,
                "title": subject.strip(),
                "description": task.strip(),
                "due_date": str(deadline),
                "priority": priority,
                "completed": False
            }).execute()

            st.session_state.tasks = load_tasks()
            st.success("Task added successfully!")
            st.rerun()

        except Exception as e:
            st.error(f"Could not save task: {e}")
    else:
        st.warning("Please enter both subject and task.")

st.divider()
st.subheader("📋 Your Study Tasks")

tasks = st.session_state.tasks

if tasks:
    completed_count = sum(bool(t["Completed"]) for t in tasks)
    total = len(tasks)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Tasks", total)
    c2.metric("Completed", completed_count)
    c3.metric("Remaining", total - completed_count)

    st.progress(
        completed_count / total,
        text=f"Study progress: {completed_count / total:.0%}"
    )

    for i, item in enumerate(tasks):
        with st.container(border=True):
            left, right = st.columns([4, 1])

            with left:
                st.write(f"**{item['Subject']}** — {item['Task']}")
                st.write(
                    f"📅 Deadline: {item['Deadline']} | "
                    f"Priority: {item['Priority']}"
                )

                checked = st.checkbox(
                    "Completed",
                    value=bool(item["Completed"]),
                    key=f"completed_{item['id']}"
                )

                if checked != bool(item["Completed"]):
                    try:
                        supabase.table("study_tasks").update({
                            "completed": checked
                        }).eq("id", item["id"]).eq(
                            "user_id", user_id
                        ).execute()

                        st.session_state.tasks = load_tasks()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Could not update task: {e}")

            with right:
                if st.button("🗑️ Delete", key=f"delete_{item['id']}"):
                    try:
                        supabase.table("study_tasks").delete().eq(
                            "id", item["id"]
                        ).eq("user_id", user_id).execute()

                        st.session_state.tasks = load_tasks()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Could not delete task: {e}")

    st.subheader("📊 Subject-wise Task Summary")

    df = pd.DataFrame(tasks)
    summary = df.groupby("Subject").agg(
        Total_Tasks=("Task", "count"),
        Completed=("Completed", "sum")
    )
    st.bar_chart(summary[["Total_Tasks", "Completed"]])

    st.download_button(
        "⬇️ Download Tasks as CSV",
        data=df.drop(columns=["id"]).to_csv(index=False),
        file_name="my_study_tasks.csv",
        mime="text/csv"
    )

else:
    st.info("No tasks yet. Add your first study task above!")
