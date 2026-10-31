import os
from datetime import date

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from supabase import create_client


# -------------------- PAGE SETTINGS --------------------

st.set_page_config(
    page_title="Smart Study Planner",
    page_icon="📚",
    layout="wide",
)

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Streamlit Cloud secrets support
if not SUPABASE_URL or not SUPABASE_KEY:
    try:
        SUPABASE_URL = st.secrets["SUPABASE_URL"]
        SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    except Exception:
        st.error(
            "Supabase settings missing. Please check SUPABASE_URL "
            "and SUPABASE_KEY in Streamlit Secrets."
        )
        st.stop()

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"Could not connect to Supabase: {e}")
    st.stop()


# -------------------- APP HEADER --------------------

st.title("📚 Smart Study Planner")
st.caption("Plan smarter. Study better!")


# -------------------- SESSION STATE --------------------

if "user" not in st.session_state:
    st.session_state.user = None

if "access_token" not in st.session_state:
    st.session_state.access_token = None

if "tasks" not in st.session_state:
    st.session_state.tasks = []


# -------------------- LOGIN / SIGN UP --------------------

if (
    st.session_state.user is None
    or st.session_state.access_token is None
):
    st.subheader("🔐 Login / Sign Up")

    email = st.text_input("Email", key="login_email")
    password = st.text_input(
        "Password",
        type="password",
        key="login_password",
    )

    login_col, signup_col = st.columns(2)

    with login_col:
        if st.button("Login", key="login_button"):
            if not email.strip() or not password:
                st.warning("Please enter your email and password.")
            else:
                try:
                    response = supabase.auth.sign_in_with_password(
                        {
                            "email": email.strip(),
                            "password": password,
                        }
                    )

                    if not response.session or not response.user:
                        st.error(
                            "Login did not create a session. "
                            "Please check your email and password."
                        )
                    else:
                        st.session_state.user = response.user
                        st.session_state.access_token = (
                            response.session.access_token
                        )
                        st.session_state.tasks = []

                        st.rerun()

                except Exception as e:
                    st.error(f"Login failed: {e}")

    with signup_col:
        if st.button("Sign Up", key="signup_button"):
            if not email.strip() or not password:
                st.warning("Please enter your email and password.")
            elif len(password) < 6:
                st.warning("Password must be at least 6 characters.")
            else:
                try:
                    response = supabase.auth.sign_up(
                        {
                            "email": email.strip(),
                            "password": password,
                        }
                    )

                    if response.session and response.user:
                        st.success(
                            "Account created successfully. "
                            "You can now use the planner."
                        )
                    else:
                        st.success(
                            "Sign-up request submitted. "
                            "If email confirmation is enabled, "
                            "verify your email before logging in."
                        )

                except Exception as e:
                    st.error(f"Sign-up failed: {e}")

    st.stop()


# -------------------- AUTHENTICATE DATABASE REQUESTS --------------------

user_id = st.session_state.user.id
supabase.postgrest.auth(st.session_state.access_token)


# -------------------- LOGOUT --------------------

if st.button("Logout", key="logout_button"):
    try:
        supabase.auth.sign_out()
    except Exception:
        pass

    st.session_state.user = None
    st.session_state.access_token = None
    st.session_state.tasks = []

    st.rerun()


st.divider()


# -------------------- LOAD TASKS --------------------

def load_tasks():
    response = (
        supabase.table("study_tasks")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )

    loaded_tasks = []

    for row in response.data:
        loaded_tasks.append(
            {
                "id": row["id"],
                "Subject": row["title"],
                "Task": row.get("description") or "",
                "Deadline": str(row["due_date"]),
                "Priority": row.get("priority") or "Medium",
                "Completed": bool(row.get("completed", False)),
            }
        )

    return loaded_tasks


# Load from database at the start of each login session.
if not st.session_state.get("tasks_loaded", False):
    try:
        st.session_state.tasks = load_tasks()
        st.session_state.tasks_loaded = True
    except Exception as e:
        st.error(f"Could not load tasks from Supabase: {e}")
        st.info(
            "Check that the study_tasks table exists and that "
            "its SELECT policy allows the logged-in user to read their tasks."
        )
        st.stop()


# -------------------- ADD TASK --------------------

st.subheader("➕ Add a Study Task")

with st.form("study_task_form"):
    subject = st.text_input(
        "Subject name",
        placeholder="Example: Mathematics",
    )

    task_description = st.text_input(
        "What do you need to study?",
        placeholder="Example: Complete Chapter 3",
    )

    deadline = st.date_input(
        "Deadline",
        value=date.today(),
        min_value=date.today(),
    )

    priority = st.selectbox(
        "Priority",
        ["High", "Medium", "Low"],
    )

    submitted = st.form_submit_button("Add Task")


if submitted:
    if not subject.strip() or not task_description.strip():
        st.warning("Please enter both subject name and study task.")
    else:
        try:
            new_task = {
                "user_id": user_id,
                "title": subject.strip(),
                "description": task_description.strip(),
                "due_date": str(deadline),
                "priority": priority,
                "completed": False,
            }

            # Save task in Supabase database.
            supabase.table("study_tasks").insert(new_task).execute()

            # Read the saved task back from the database.
            st.session_state.tasks = load_tasks()

            st.success("✅ Task saved successfully!")
            st.rerun()

        except Exception as e:
            st.error(f"❌ Could not save task: {e}")
            st.info(
                "If the error mentions Row Level Security or code 42501, "
                "check the INSERT policy on the study_tasks table."
            )


# -------------------- TASK LIST AND PROGRESS --------------------

st.divider()
st.subheader("📋 Your Study Tasks")

tasks = st.session_state.tasks

if tasks:
    total_tasks = len(tasks)
    completed_tasks = sum(task["Completed"] for task in tasks)
    remaining_tasks = total_tasks - completed_tasks

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Tasks", total_tasks)
    col2.metric("Completed", completed_tasks)
    col3.metric("Remaining", remaining_tasks)

    st.progress(
        completed_tasks / total_tasks,
        text=f"Study progress: {completed_tasks / total_tasks:.0%}",
    )

    for item in tasks:
        with st.container(border=True):
            left_col, right_col = st.columns([4, 1])

            with left_col:
                st.markdown(f"### {item['Subject']}")
                st.write(item["Task"])

                st.write(
                    f"📅 Deadline: {item['Deadline']}  |  "
                    f"Priority: {item['Priority']}"
                )

                is_completed = st.checkbox(
                    "Mark as completed",
                    value=item["Completed"],
                    key=f"completed_{item['id']}",
                )

                if is_completed != item["Completed"]:
                    try:
                        (
                            supabase.table("study_tasks")
                            .update({"completed": is_completed})
                            .eq("id", item["id"])
                            .eq("user_id", user_id)
                            .execute()
                        )

                        st.session_state.tasks = load_tasks()
                        st.rerun()

                    except Exception as e:
                        st.error(f"Could not update task: {e}")

            with right_col:
                if st.button(
                    "🗑️ Delete",
                    key=f"delete_{item['id']}",
                ):
                    try:
                        (
                            supabase.table("study_tasks")
                            .delete()
                            .eq("id", item["id"])
                            .eq("user_id", user_id)
                            .execute()
                        )

                        st.session_state.tasks = load_tasks()
                        st.rerun()

                    except Exception as e:
                        st.error(f"Could not delete task: {e}")

    # -------------------- SUBJECT SUMMARY --------------------

    st.divider()
    st.subheader("📊 Subject-wise Task Summary")

    df = pd.DataFrame(tasks)

    summary = df.groupby("Subject").agg(
        Total_Tasks=("Task", "count"),
        Completed=("Completed", "sum"),
    )

    st.bar_chart(summary)

    # -------------------- CSV DOWNLOAD --------------------

    csv_data = df.drop(columns=["id"]).to_csv(index=False)

    st.download_button(
        label="⬇️ Download Tasks as CSV",
        data=csv_data,
        file_name="my_study_tasks.csv",
        mime="text/csv",
        key="download_tasks_button",
    )

else:
    st.info("No tasks yet. Add your first study task above!")
