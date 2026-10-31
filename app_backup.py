import streamlit as st
st.set_page_config(page_title="Smart Study Planner", page_icon=":books:")

st.title("Smart Study Planner")
st.write("Plan smarter,Study better!")

name=st.text_input("Enter your name:")
if name:
    st.success(f"Welcome, {name}!")

st.subheader("Add a Study Task")

subject = st.text_input("Subject name")
task=st.text_input("what we need to study?")

if st.button("Add Task"):
    if subject and task:
        st.success(f"Task added for {subject}: {task}")
    else:
        st.error("Please fill in both subject and task fields.")