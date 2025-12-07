# import sys
# from pathlib import Path

# # Add project root to path
# sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# import streamlit as st
# from src.agents.curriculum_planner_agent import CurriculumPlannerAgent
# from src.agents.language_tutor_agent import LanguageTutorAgent




# st.set_page_config(page_title="Language course", layout="wide")


# # ============================================================================
# # CURRICULUM PLANNER SECTION
# # ============================================================================
# # Allows students to generate a personalized 24-week learning curriculum
# # based on their proficiency level, goals, and target language.

# st.title("Language Learning Platform")


# # Student input fields for curriculum generation
# name = st.text_input("Student name")
# level = st.selectbox("Current proficiency level", ["A1", "A2", "B1", "B2", "C1"])
# weeks = st.slider("Curriculum duration (weeks)", 4, 24, 12)


# # Generate curriculum using the planner agent
# if st.button("Generate Learning Plan"):
#     try:
#         planner = CurriculumPlannerAgent(database_url="mongodb://localhost:27017")
#         result = planner.plan_curriculum(
#             student_id=name.lower().replace(" ", "_") if name else "default_student",
#             force_regenerate=True
#         )
#         st.success("✅ Curriculum generated successfully!")
#         st.json(result)
#     except Exception as e:
#         st.error(f"Curriculum generation failed: {e}")


# st.divider()


# # ============================================================================
# # LANGUAGE TUTOR CHATBOT SECTION
# # ============================================================================
# # Interactive chat interface powered by the Language Tutor Agent.
# # Provides personalized lessons, exercises, and dialogues based on student needs.

# st.header("Interactive Language Tutor")


# # Initialize tutor agent once per session
# if "tutor" not in st.session_state:
#     try:
#         st.session_state.tutor = LanguageTutorAgent()
#     except Exception as e:
#         st.error(f"Failed to initialize tutor agent: {e}")


# # Initialize chat history
# if "messages" not in st.session_state:
#     st.session_state.messages = []


# # Display conversation history
# for message in st.session_state.messages:
#     with st.chat_message(message["role"]):
#         st.markdown(message["content"])


# # Chat input and response handling
# if user_input := st.chat_input("Ask your tutor a question or request a lesson topic"):
#     # Add user message to history
#     st.session_state.messages.append({"role": "user", "content": user_input})
#     with st.chat_message("user"):
#         st.markdown(user_input)

#     # Generate tutor response
#     try:
#         tutor_response = st.session_state.tutor.chat(user_input)
#         st.session_state.messages.append({"role": "assistant", "content": tutor_response})
#         with st.chat_message("assistant"):
#             st.markdown(tutor_response)
#     except Exception as e:
#         st.error(f"Tutor encountered an error: {e}")


import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
from src.agents.language_tutor_agent import LanguageTutorAgent
from src.agents.curriculum_planner_agent import CurriculumPlannerAgent
from src.database.mongodb_adapter import LanguageLearningDB


st.set_page_config(page_title="Language Learning Platform", layout="wide")

st.title("Language Learning Platform")

# Initialize database connection
db = LanguageLearningDB(database_url="mongodb://localhost:27017")

# Initialize tutor and planner agents
if "tutor" not in st.session_state:
    try:
        st.session_state.tutor = LanguageTutorAgent()
        st.session_state.planner = CurriculumPlannerAgent(database_url="mongodb://localhost:27017")
    except Exception as e:
        st.error(f"Failed to initialize agents: {e}")
        st.stop()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

if "current_student" not in st.session_state:
    st.session_state.current_student = None

# ============================================================================
# STUDENT IDENTIFICATION SECTION
# ============================================================================

st.header("Student Information")

# Input field for student name
student_name = st.text_input("Enter your name", placeholder="e.g., John Doe")

if student_name:
    # Create student ID from name (lowercase, replace spaces with underscore)
    student_id = student_name.lower().replace(" ", "_")
    
    # Check if student exists in database
    existing_student = db.get_student(student_id)
    
    if existing_student:
        # Student found in database
        st.success(f"Welcome back, {student_name}!")
        st.session_state.current_student = existing_student
        
        # Display student information
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current Level", existing_student.get("current_level", "N/A"))
        with col2:
            st.metric("Target Language", existing_student.get("target_language", "N/A"))
        with col3:
            st.metric("Learning Style", existing_student.get("learning_style", "N/A"))
        
        # Display goals
        if existing_student.get("goals"):
            st.info(f"Goals: {existing_student.get('goals')}")
    else:
        # Student not found - create new student
        st.info(f"New student detected. Please complete your profile.")
        
        # Student profile form
        col1, col2 = st.columns(2)
        
        with col1:
            target_language = st.selectbox("Target Language", ["English", "Spanish", "French", "German", "Chinese", "Japanese"])
            current_level = st.selectbox("Current Proficiency Level", ["A1", "A2", "B1", "B2", "C1", "C2"])
        
        with col2:
            learning_style = st.text_input("Learning Style", placeholder="e.g., visual, conversational, grammar-focused")
            goals = st.text_area("Your Learning Goals", placeholder="What do you want to achieve?")
        
        # Create student button
        if st.button("Create My Profile", key="create_student"):
            new_student = {
                "student_id": student_id,
                "name": student_name,
                "target_language": target_language,
                "current_level": int(ord(current_level[0]) - ord('A')) + 1,  # Convert A1 to 1, B1 to 2, etc.
                "learning_style": learning_style or "general",
                "goals": goals or "General language learning"
            }
            
            # Save to database
            success = db.create_student(new_student)
            
            if success:
                st.success(f"Profile created successfully, {student_name}!")
                st.session_state.current_student = new_student
                st.rerun()
            else:
                st.error("Failed to create profile. Please try again.")

st.divider()

# ============================================================================
# LANGUAGE TUTOR CHATBOT SECTION
# ============================================================================

if st.session_state.current_student:
    st.header("Interactive Language Tutor")
    
    # Display current student info
    student_info = st.session_state.current_student
    st.caption(f"Student: {student_info.get('name')} | Level: {student_info.get('target_language')}")
    
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
            with st.spinner("Tutor is preparing your lesson..."):
                tutor_response = st.session_state.tutor.chat(user_input)
            st.session_state.messages.append({"role": "assistant", "content": tutor_response})
            with st.chat_message("assistant"):
                st.markdown(tutor_response)
        except Exception as e:
            st.error(f"Tutor encountered an error: {e}")
else:
    st.info("Please enter your name and create your profile to start learning.")
