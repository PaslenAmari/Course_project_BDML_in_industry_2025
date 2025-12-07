# app.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
from src.agents.language_tutor_agent import LanguageTutorAgent
from src.agents.curriculum_planner_agent import CurriculumPlannerAgent
from src.database.mongodb_adapter import LanguageLearningDB
import base64
import datetime


BACKGROUND_MAP = {
    "English": "background/England.jpg",
    "German": "background/German.jpg",
    "Japanese": "background/Japanese.jpg",
    "Spanish": "background/Spanish.jpg",
    "French": "background/French.jpg",
    "Chinese": "background/Chinese.jpg"
}

DEFAULT_BG = "background/Learning_room.jpg"

# # ============================================================================
# # CURRICULUM PLANNER SECTION
# # ============================================================================
# # Allows students to generate a personalized 24-week learning curriculum
# # based on their proficiency level, goals, and target language.

def set_background(image_path: str, overlay_opacity: float = 0.2):
    img_path = Path(image_path)
    ext = img_path.suffix.replace(".", "")
    with open(img_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    
    css = f"""
    <style>
    .stApp {{
        background-image: url("data:image/{ext};base64,{encoded}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
    }}
    .stApp::before {{
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, {overlay_opacity});
        pointer-events: none;
        z-index: 0;
    }}
    .stApp > * {{
        position: relative;
        z-index: 1;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


# ============================================================================
# INIT PAGE & AGENTS
# ============================================================================

st.set_page_config(page_title="Language Learning Platform", layout="wide")
set_background(DEFAULT_BG)
st.title("Language Learning Platform")

db = LanguageLearningDB(database_url="mongodb://localhost:27017")

if "tutor" not in st.session_state:
    try:
        st.session_state.tutor = LanguageTutorAgent()
        st.session_state.planner = CurriculumPlannerAgent(database_url="mongodb://localhost:27017")
    except Exception as e:
        st.error(f"Failed to initialize agents: {e}")
        st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_student" not in st.session_state:
    st.session_state.current_student = None
if "curriculum" not in st.session_state:
    st.session_state.curriculum = None
if "show_lang_picker" not in st.session_state:
    st.session_state.show_lang_picker = False


# ============================================================================
# STUDENT IDENTIFICATION
# ============================================================================

st.header("Student Information")
student_name = st.text_input("Enter your name", placeholder="e.g., John Doe")

if student_name:
    student_id = student_name.lower().replace(" ", "_")
    existing_student = db.get_student(student_id)
    
    if existing_student:
        st.success(f"Welcome back, {student_name}!")
        st.session_state.current_student = existing_student
        
        lang = existing_student.get("target_language", "English")
        bg_path = BACKGROUND_MAP.get(lang, DEFAULT_BG)
        set_background(bg_path, overlay_opacity=0.2)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current Level", existing_student.get("current_level", "N/A"))
        with col2:
            st.metric("Target Language", lang)
        with col3:
            st.metric("Learning Style", existing_student.get("learning_style", "N/A"))
        
        if existing_student.get("goals"):
            st.info(f"Goals: {existing_student.get('goals')}")
    else:
        st.info(f"New student detected. Please complete your profile.")
        
        col1, col2 = st.columns(2)
        with col1:
            target_language = st.selectbox("Target Language", 
                ["English", "Spanish", "French", "German", "Chinese", "Japanese"])
            current_level = st.selectbox("Current Proficiency Level", 
                ["A1", "A2", "B1", "B2", "C1", "C2"])
        
        with col2:
            learning_style = st.text_input("Learning Style", 
                placeholder="e.g., visual, conversational, grammar-focused")
            goals = st.text_area("Your Learning Goals", 
                placeholder="What do you want to achieve?")
        
        bg_path = BACKGROUND_MAP.get(target_language, DEFAULT_BG)
        set_background(bg_path, overlay_opacity=0.2)
        
        if st.button("Create My Profile", key="create_student"):
            new_student = {
                "student_id": student_id,
                "name": student_name,
                "target_language": target_language,
                "current_level": int(ord(current_level[0]) - ord('A')) + 1,
                "learning_style": learning_style or "general",
                "goals": goals or "General language learning"
            }
            
            success = db.create_student(new_student)
            if success:
                st.success(f"Profile created successfully, {student_name}!")
                st.session_state.current_student = new_student
                st.rerun()
            else:
                st.error("Failed to create profile.")

st.divider()

# ============================================================================
# MAIN INTERFACE WITH TABS
# ============================================================================

if st.session_state.current_student:
    student_info = st.session_state.current_student
    student_id = student_info["student_id"]
    
    # СМЕНА ЯЗЫКА
    col1, col2 = st.columns([4, 1])
    with col1:
        st.caption(f"Student: {student_info.get('name')} | "
                   f"Current: {student_info.get('target_language')} "
                   f"(Level {student_info.get('current_level')})")
    
    with col2:
        if st.button("Change Language", key="change_lang"):
            st.session_state.show_lang_picker = True
    
    if st.session_state.show_lang_picker:
        st.info("Start learning a new language")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            new_language = st.selectbox("New Language", 
                ["English", "Spanish", "French", "German", "Chinese", "Japanese"],
                key="new_lang_select")
        
        with col2:
            new_start_level = st.selectbox("Starting Level",
                ["A1", "A2", "B1", "B2", "C1", "C2"],
                key="new_start_level")
        
        with col3:
            new_target_level = st.selectbox("Target Level",
                ["A2", "B1", "B2", "C1", "C2"],
                key="new_target_level")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Confirm", key="confirm_lang"):
                updated_student = student_info.copy()
                updated_student["target_language"] = new_language
                updated_student["current_level"] = int(ord(new_start_level[0]) - ord('A')) + 1
                updated_student["target_level"] = int(ord(new_target_level[0]) - ord('A')) + 1
                
                db.db.students.update_one(
                    {"student_id": student_id},
                    {"$set": {
                        "target_language": new_language,
                        "current_level": updated_student["current_level"],
                        "target_level": updated_student["target_level"]
                    }}
                )
                
                st.session_state.curriculum = None
                st.session_state.current_student = updated_student
                st.session_state.show_lang_picker = False
                
                st.success(f"Now learning {new_language}!")
                st.rerun()
        
        with col2:
            if st.button("Cancel", key="cancel_lang"):
                st.session_state.show_lang_picker = False
                st.rerun()
    
    # ТАБЫ
    tab1, tab2, tab3, tab4 = st.tabs([
        "Learning Plan",
        "Progress",
        "Tutor",
        "Exercises"
    ])
    
    # TAB 1: LEARNING PLAN
    with tab1:
        st.header("Your Learning Plan")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            total_weeks = st.slider(
                "Course Duration (weeks)",
                min_value=4,
                max_value=52,
                value=24,
                step=4,
                help="Choose how many weeks for your curriculum"
            )
        
        with col2:
            if st.button("Regenerate", key="regen_plan"):
                st.session_state.curriculum = None
        
        if st.session_state.curriculum is None:
            with st.spinner("Generating your personalized curriculum..."):
                try:
                    plan_result = st.session_state.planner.plan_curriculum(
                        student_id=student_id,
                        force_regenerate=False,
                        total_weeks=total_weeks
                    )
                    st.session_state.curriculum = plan_result
                except Exception as e:
                    st.error(f"Error generating plan: {e}")
                    plan_result = None
        else:
            plan_result = st.session_state.curriculum
        
        if plan_result and "error" not in plan_result:
            st.success(f"Week {plan_result['next_week']}: {', '.join(plan_result['next_topics'])}")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Current Week", plan_result['next_week'])
            with col2:
                st.metric("Total Weeks", plan_result['total_weeks'])
            with col3:
                st.metric("Level From", plan_result['level_from'])
            with col4:
                st.metric("Level To", plan_result['level_to'])
            
            st.info(f"**Message:** {plan_result.get('message', 'Plan updated')}")
            
            with st.expander("View Full Curriculum"):
                st.json(plan_result)
        else:
            st.warning("No curriculum generated yet.")
    
    # TAB 2: PROGRESS
    with tab2:
        st.header("Your Progress")
        
        stats = {
            "lessons_completed": db.db.lesson_sessions.count_documents(
                {"student_id": student_id}
            ),
            "vocab_count": db.db.vocabulary.count_documents(
                {"student_id": student_id}
            ),
            "errors": db.db.student_errors.count_documents(
                {"student_id": student_id}
            ),
        }
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Lessons Completed", stats["lessons_completed"])
        with col2:
            st.metric("Vocabulary Learned", stats["vocab_count"])
        with col3:
            st.metric("Errors Tracked", stats["errors"])
        with col4:
            st.metric("Current Level", student_info.get("current_level", "N/A"))
        
        st.info("More detailed analytics coming soon...")
    
    # TAB 3: TUTOR
    with tab3:
        st.header("Interactive Language Tutor")
        st.caption(f"Student: {student_info.get('name')} | "
                   f"Level: {student_info.get('target_language')}")
        
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        if user_input := st.chat_input("Request a lesson, ask a question, or suggest a topic"):
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)
            
            try:
                with st.spinner("Tutor is preparing your lesson..."):
                    lesson_result = st.session_state.tutor.teach(
                        student_id=student_id,
                        topic=user_input
                    )
                
                response_text = f"""
**Lesson: {lesson_result.get('topic', 'N/A')}**

**Outline:**
{chr(10).join(['- ' + item for item in lesson_result.get('outline', [])])}

**Selected Tools:** {', '.join(lesson_result.get('selected_tools', []))}

**Duration:** {lesson_result.get('lesson_metadata', {}).get('duration_minutes', 'N/A')} minutes

**Phase:** {lesson_result.get('lesson_metadata', {}).get('phase', 'N/A')}
"""
                
                if lesson_result.get('exercise'):
                    response_text += f"\n\n**Exercise:**\n{lesson_result['exercise'].get('task', 'N/A')}"
                
                st.session_state.messages.append(
                    {"role": "assistant", "content": response_text}
                )
                
                with st.chat_message("assistant"):
                    st.markdown(response_text)
                
                db.save_chat_interaction(
                    student_id=student_id,
                    question=user_input,
                    answer=response_text
                )
                
            except Exception as e:
                st.error(f"Tutor encountered an error: {e}")
    
    # TAB 4: EXERCISES
    with tab4:
        st.header("Practice Exercises")
        
        col1, col2 = st.columns(2)
        with col1:
            exercise_type = st.selectbox("Exercise Type", 
                ["vocabulary", "grammar", "dialogue", "listening"])
        with col2:
            if st.button("Generate New Exercise", key="gen_exercise"):
                st.session_state.current_exercise = None
        
        if "current_exercise" not in st.session_state:
            st.session_state.current_exercise = None
        
        if st.button("Generate", key="do_gen") or st.session_state.current_exercise is None:
            with st.spinner("Generating exercise..."):
                try:
                    import asyncio
                    
                    exercise = asyncio.run(
                        st.session_state.tutor.tools.generate_exercise(
                            topic=f"{student_info.get('target_language')} {exercise_type}",
                            exercise_type=exercise_type,
                            level=student_info.get('current_level', 3)
                        )
                    )
                    
                    st.session_state.current_exercise = exercise
                    st.session_state.exercise_answered = False
                    
                except Exception as e:
                    st.error(f"Error generating exercise: {e}")
        
        if st.session_state.current_exercise:
            ex = st.session_state.current_exercise
            
            if "error" in ex:
                st.error(f"Exercise generation error: {ex['error']}")
            else:
                st.write(f"### **{ex.get('type', 'Exercise').upper()}**")
                st.write(f"**Task:** {ex.get('task', 'N/A')}")
                st.write(f"**Instructions:** {ex.get('instructions', 'N/A')}")
                
                if 'options' in ex and ex['options']:
                    st.write("**Choose your answer:**")
                    answer = st.radio(
                        label="Options:",
                        options=ex['options'],
                        key="exercise_answer"
                    )
                    answer_type = "choice"
                else:
                    st.write("**Your answer:**")
                    answer = st.text_area(
                        label="Type your answer here:",
                        key="exercise_answer",
                        height=100
                    )
                    answer_type = "text"
                
                if st.button("Check Answer", key="check_ans"):
                    correct = ex.get('correct_answer', '')
                    
                    if answer_type == "choice":
                        is_correct = answer == correct
                    else:
                        is_correct = answer.lower().strip() == correct.lower().strip()
                    
                    if is_correct:
                        st.success("Correct!")
                        st.balloons()
                        
                        db.db.exercise_results.insert_one({
                            "student_id": student_id,
                            "exercise_id": ex.get('exercise_id', 'unknown'),
                            "exercise_type": exercise_type,
                            "correct": True,
                            "student_answer": answer,
                            "created_at": datetime.datetime.utcnow()
                        })
                        
                        st.session_state.exercise_answered = True
                    else:
                        st.error("Incorrect!")
                        st.info(f"**Correct answer:** {correct}")
                        
                        db.db.exercise_results.insert_one({
                            "student_id": student_id,
                            "exercise_id": ex.get('exercise_id', 'unknown'),
                            "exercise_type": exercise_type,
                            "correct": False,
                            "student_answer": answer,
                            "correct_answer": correct,
                            "created_at": datetime.datetime.utcnow()
                        })
                    
                    st.info(f"**Explanation:** {ex.get('explanation', 'N/A')}")
                    
                    if st.button("Next Exercise", key="next_ex"):
                        st.session_state.current_exercise = None
                        st.rerun()

else:
    st.info("Please enter your name and create your profile to start learning.")
