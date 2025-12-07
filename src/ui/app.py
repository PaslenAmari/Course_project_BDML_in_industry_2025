import streamlit as st
from src.agents.curriculum_planner_agent import CurriculumPlannerAgent
from src.agents.language_tutor_agent import LanguageTutorAgent


st.set_page_config(page_title="Language course", layout="wide")


# ============================================================================
# CURRICULUM PLANNER SECTION
# ============================================================================
# Allows students to generate a personalized 24-week learning curriculum
# based on their proficiency level, goals, and target language.

st.title("Language Learning Platform")


# Student input fields for curriculum generation
name = st.text_input("Student name")
level = st.selectbox("Current proficiency level", ["A1", "A2", "B1", "B2", "C1"])
weeks = st.slider("Curriculum duration (weeks)", 4, 24, 12)


# Generate curriculum using the planner agent
if st.button("Generate Learning Plan"):
    try:
        planner = CurriculumPlannerAgent(database_url="mongodb://localhost:27017")
        result = planner.plan_curriculum(
            student_id=name.lower().replace(" ", "_") if name else "default_student",
            force_regenerate=True
        )
        st.success("✅ Curriculum generated successfully!")
        st.json(result)
    except Exception as e:
        st.error(f"Curriculum generation failed: {e}")


st.divider()


# ============================================================================
# LANGUAGE TUTOR CHATBOT SECTION
# ============================================================================
# Interactive chat interface powered by the Language Tutor Agent.
# Provides personalized lessons, exercises, and dialogues based on student needs.

st.header("Interactive Language Tutor")


# Initialize tutor agent once per session
if "tutor" not in st.session_state:
    try:
        st.session_state.tutor = LanguageTutorAgent()
    except Exception as e:
        st.error(f"Failed to initialize tutor agent: {e}")


# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []


# Display conversation history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# Chat input and response handling
if user_input := st.chat_input("Ask your tutor a question or request a lesson topic"):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Generate tutor response
    try:
        tutor_response = st.session_state.tutor.chat(user_input)
        st.session_state.messages.append({"role": "assistant", "content": tutor_response})
        with st.chat_message("assistant"):
            st.markdown(tutor_response)
    except Exception as e:
        st.error(f"Tutor encountered an error: {e}")
