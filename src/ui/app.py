import streamlit as st
from src.agents.language_tutor_agent import CurriculumPlannerAgent
from src.agents.language_tutor_agent import LanguageTutorAgent

st.set_page_config(page_title="Language course", layout="wide")

# ---------- Planner UI ----------
st.title("Language course – demo UI")

name = st.text_input("Student name")
level = st.selectbox("Current level", ["A1", "A2", "B1", "B2", "C1"])
weeks = st.slider("Number of weeks", 4, 24, 12)

if st.button("Generate plan"):
    # TODO: здесь вместо f-string вызвать твой CurriculumPlannerAgent
    st.write(f"Plan for {name} for {weeks} weeks (level {level})")

st.write("---")  # разделитель

# ---------- Tutor chat UI ----------
st.header("Language Tutor")

# создаём агента один раз
if "tutor" not in st.session_state:
    st.session_state.tutor = LanguageTutorAgent()  # подставь нужные параметры

# храним историю диалога
if "messages" not in st.session_state:
    st.session_state.messages = []

# выводим историю
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):  # "user" или "assistant"
        st.markdown(msg["content"])

# поле ввода снизу
if prompt := st.chat_input("Type your message to the tutor"):
    # сообщение студента
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # ответ LLM‑тьютора
    reply = st.session_state.tutor.chat(prompt)  # или другой метод

    with st.chat_message("assistant"):
        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
