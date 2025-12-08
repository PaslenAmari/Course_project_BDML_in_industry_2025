# app.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
from src.agents.language_tutor_agent import LanguageTutorAgent
from src.agents.curriculum_planner_agent import CurriculumPlannerAgent
from src.agents.unified_teacher_agent import UnifiedTeacherAgent
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

def set_background(image_path: str, overlay_opacity: float = 0.5):
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
        background-attachment: fixed;
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
    .stApp > header {{
        background-color: transparent !important;
    }}
    /* Main content text styling for high contrast */
    h1, h2, h3, h4, h5, h6, p, li, label, .stMarkdown, .stText, .stMetricLabel, .stMetricValue {{
        color: #ffffff !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
    }}
    
    /* Inputs and Selectboxes - Solid Backgrounds */
    .stTextInput > div > div, 
    .stSelectbox > div > div, 
    .stTextArea > div > div, 
    .stNumberInput > div > div {{
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 2px solid #e0e0e0;
        border-radius: 8px;
    }}
    
    /* Ensure text inside inputs is black and no shadow */
    input, textarea {{
        color: #000000 !important;
        text-shadow: none !important;
    }}
    
    /* Placeholder text styling */
    input::placeholder, textarea::placeholder {{
        color: #666666 !important;
        opacity: 1; /* Firefox */
    }}
    ::-webkit-input-placeholder {{
        color: #666666 !important;
    }}
    
    /* Selectbox dropdown text */
    div[data-baseweb="select"] span {{
        color: #000000 !important;
        text-shadow: none !important;
    }}
    
    /* Buttons - Solid and Visible */
    .stButton > button {{
        background-color: #ff4b4b !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px;
        font-weight: bold;
        padding: 0.5rem 1rem;
        text-shadow: none !important;
    }}
    
    /* Chat messages */
    .stChatMessage {{
        background-color: rgba(0, 0, 0, 0.7) !important;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 0.5rem;
    }}
    
    /* Expander and other containers */
    /* Expander and other containers */
    .streamlit-expanderHeader {{
        background-color: rgba(255, 255, 255, 0.9) !important;
        color: #000000 !important;
        border-radius: 5px;
        text-shadow: none !important;
    }}
    .streamlit-expanderContent {{
        background-color: rgba(0, 0, 0, 0.6) !important;
        color: #ffffff !important;
    }}
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        background-color: rgba(0,0,0,0.5);
        border-radius: 10px;
        padding: 5px;
    }}
    .stTabs [data-baseweb="tab"] {{
        color: #ffffff !important;
        text-shadow: 1px 1px 2px black;
    }}
    .stTabs [data-baseweb="tab"][aria-selected="true"] {{
        background-color: #ff4b4b !important;
        color: white !important;
        border-radius: 5px;
    }}
    
    /* Chat Input */
    .stChatInputContainer {{
        padding-bottom: 20px;
    }}
    div[data-testid="stChatInput"] {{
        background-color: transparent !important;
    }}
    div[data-testid="stChatInput"] > div {{
        background-color: #ffffff !important;
        color: #000000 !important;
        border-radius: 20px;
        border: 2px solid #e0e0e0;
    }}
    div[data-testid="stChatInput"] textarea {{
        background-color: #ffffff !important;
        color: #000000 !important;
        caret-color: #000000 !important;
        -webkit-text-fill-color: #000000 !important; /* Force text color on WebKit */
    }}
    div[data-testid="stChatInput"] button {{
        color: #000000 !important;
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

# --- RESET LOGIC FOR CODE UPDATES ---
# Increment this version whenever you modify agent code to force a reload
SYSTEM_VERSION = "1.8" 

if "system_version" not in st.session_state or st.session_state.system_version != SYSTEM_VERSION:
    st.info("System updated. Reloading modules and agents...")
    
    # Force reload of backend modules to pick up code changes
    import importlib
    import src.agents.language_tools
    import src.agents.language_tutor_agent
    import src.database.mongodb_adapter
    
    importlib.reload(src.agents.language_tools)
    importlib.reload(src.agents.language_tutor_agent)
    importlib.reload(src.database.mongodb_adapter)
    
    # Re-import classes from reloaded modules
    from src.agents.language_tutor_agent import LanguageTutorAgent
    from src.database.mongodb_adapter import LanguageLearningDB
    
    # Re-initialize global DB with fresh class
    db = LanguageLearningDB(database_url="mongodb://localhost:27017")
    
    keys_to_reset = ["tutor", "planner", "unified_agent", "quiz_session"]
    for k in keys_to_reset:
        if k in st.session_state:
            del st.session_state[k]
            
    st.session_state.system_version = SYSTEM_VERSION
    st.rerun()

if "tutor" not in st.session_state:
    try:
        # Re-import locally to ensure we use the fresh class definition
        from src.agents.language_tutor_agent import LanguageTutorAgent
        
        st.session_state.tutor = LanguageTutorAgent()
        st.session_state.planner = CurriculumPlannerAgent(database_url="mongodb://localhost:27017")
        st.session_state.unified_agent = UnifiedTeacherAgent(database_url="mongodb://localhost:27017")
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
        set_background(bg_path, overlay_opacity=0.5)
        
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
        set_background(bg_path, overlay_opacity=0.5)
        
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
        
        all_levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
        
        with col1:
            new_language = st.selectbox("New Language", 
                ["English", "Spanish", "French", "German", "Chinese", "Japanese"],
                key="new_lang_select")
        
        with col2:
            new_start_level = st.selectbox("Starting Level",
                all_levels,
                key="new_start_level")
        
        # Calculate valid target levels (must be > start level)
        try:
            start_idx = all_levels.index(new_start_level)
            valid_targets = all_levels[start_idx + 1:]
            if not valid_targets:
                valid_targets = [new_start_level] # Fallback if C2 is selected
        except ValueError:
            valid_targets = all_levels

        with col3:
            new_target_level = st.selectbox("Target Level",
                valid_targets,
                key="new_target_level")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Confirm", key="confirm_lang"):
                # CEFR Mapping
                LEVEL_MAP = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}
                
                updated_student = student_info.copy()
                updated_student["target_language"] = new_language
                updated_student["current_level"] = LEVEL_MAP.get(new_start_level, 1)
                updated_student["target_level"] = LEVEL_MAP.get(new_target_level, 6)
                
                db.db.students.update_one(
                    {"student_id": student_id},
                    {"$set": {
                        "target_language": new_language,
                        "current_level": updated_student["current_level"],
                        "target_level": updated_student["target_level"]
                    }}
                )
                
                st.session_state.curriculum = None
                st.session_state.force_regen_flag = True # Force new plan calculation
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
        "Unified Tutor",
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
                st.session_state.force_regen_flag = True
        
        if st.session_state.curriculum is None:
            with st.spinner("Generating your personalized curriculum..."):
                try:
                    # Check if we need to force regenerate
                    should_force = st.session_state.get("force_regen_flag", False)
                    
                    plan_result = st.session_state.planner.plan_curriculum(
                        student_id=student_id,
                        force_regenerate=should_force,
                        total_weeks=total_weeks
                    )
                    st.session_state.curriculum = plan_result
                    
                    # Reset flag after successful generation
                    if should_force:
                        st.session_state.force_regen_flag = False
                        
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
            
            with st.expander("View Full Curriculum", expanded=True):
                # Fallback: if 'topics_by_week' is missing (due to stale agent), fetch from DB
                display_topics = plan_result.get("topics_by_week")
                if not display_topics:
                    current_lang = student_info.get("target_language", "English")
                    full_curr = db.get_curriculum(student_id, language=current_lang)
                    if full_curr:
                        display_topics = full_curr.get("topics_by_week")
                
                if display_topics:
                    for week in display_topics:
                        st.markdown(f"""
                        <div style="background-color: rgba(255,255,255,0.05); padding: 10px; border-radius: 5px; margin-bottom: 5px; border-left: 4px solid #ff4b4b;">
                            <strong style="color: #ffffff;">Week {week['week']}</strong>: <span style="color: #cccccc;">{', '.join(week['topics'])}</span>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.json(plan_result)
        else:
            st.warning("No curriculum generated yet.")
    
    # TAB 2: PROGRESS
    with tab2:
        st.header("Your Progress")
        
        # Calculate Weekly Progress
        current_lang = student_info.get("target_language", "English")
        curriculum_data = db.get_curriculum(student_id, language=current_lang)
        
        current_week_display = 1
        total_weeks_display = 24
        
        if curriculum_data:
            completed = curriculum_data.get("completed_weeks", 0)
            total = curriculum_data.get("total_weeks", 24)
            current_week_display = completed + 1
            total_weeks_display = total
        
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
            st.metric("Current Week", f"{current_week_display} / {total_weeks_display}")
        with col2:
            st.metric("Vocabulary Learned", stats["vocab_count"])
        with col3:
            st.metric("Errors Tracked", stats["errors"])
        with col4:
            st.metric("Current Level", student_info.get("current_level", "N/A"))
        
        # Progress Bar for Weeks
        st.write("### Weekly Progression")
        progress_val = min(1.0, (current_week_display - 1) / total_weeks_display)
        st.progress(progress_val)
        st.caption(f"You have completed {current_week_display - 1} out of {total_weeks_display} weeks in {current_lang}.")

        st.divider()
        st.info("Complete the 'Weekly Exam' in the Exercises tab to advance to the next week!")
    
    # TAB 3: UNIFIED TUTOR
    with tab3:
        st.header("Unified Teacher Agent")
        
        # Determine Current Week
        curr_week = 1
        curr_topics = []
        if st.session_state.curriculum:
            curr_week = st.session_state.curriculum.get("next_week", 1)
            # Find topics
            if "topics_by_week" in st.session_state.curriculum:
                for w in st.session_state.curriculum["topics_by_week"]:
                    if w["week"] == curr_week:
                        curr_topics = w["topics"]
                        break
        
        st.info(f"🔒 **Current Locked Week:** {curr_week} | **Topics:** {', '.join(curr_topics)}")
        
        tab_uni_1, tab_uni_2 = st.tabs(["Chat Evaluation", "Content Generation"])
        
        # --- SUB-TAB 1: CHAT EVALUATION ---
        with tab_uni_1:
            st.subheader("Evaluate Recent Chat Interaction")
            st.caption("The agent will analyze your recent conversation history to provide detailed feedback and scoring.")
            
            if st.button("Evaluate My Progress", key="btn_eval_chat"):
                with st.spinner("Analyzing chat history..."):
                    eval_result = st.session_state.unified_agent.evaluate_chat(student_id=student_id)
                
                if "error" in eval_result:
                    st.error(f"Evaluation failed: {eval_result['error']}")
                else:
                    # Score
                    score = eval_result.get("overall_score", 0)
                    if score >= 80:
                        st.success(f"Overall Score: {score}/100")
                    elif score >= 50:
                        st.warning(f"Overall Score: {score}/100")
                    else:
                        st.error(f"Overall Score: {score}/100")
                    
                    st.write(f"**Feedback:** {eval_result.get('detailed_feedback', '')}")
                    
                    # Errors
                    errors = eval_result.get("all_errors", [])
                    if errors:
                        st.write("### Identified Errors")
                        for i, err in enumerate(errors):
                            with st.expander(f"Error {i+1}: {err.get('error_description', 'Unknown error')}"):
                                st.write(f"**Student Answer:** {err.get('student_answer', 'N/A')}")
                                st.write(f"**Correction:** {err.get('correction', 'N/A')}")
                                st.write(f"**Rule:** {err.get('rule_explanation', 'N/A')}")
                    else:
                        st.info("No major errors detected in recent history!")
                        
                    # Improvement Plan
                    st.write("### Improvement Plan")
                    st.info(eval_result.get("improvement_plan", "Keep practicing!"))
                    
                    # Follow-up
                    q_list = eval_result.get("follow_up_questions", [])
                    if q_list:
                        st.write("**Suggested Follow-up Questions:**")
                        for q in q_list:
                            st.markdown(f"- {q}")

        # --- SUB-TAB 2: CONTENT GENERATION ---
        with tab_uni_2:
            st.subheader("Generate Syllabus-Aligned Content")
            st.caption("Content is automatically aligned to your current week's topics.")

            c1, c2 = st.columns(2)
            with c1:
                # Locked to current week
                st.text_input("Target Week", value=f"Week {curr_week}", disabled=True)
                target_week = curr_week
            with c2:
                content_type = st.selectbox("Content Type", ["multiple_choice", "fill_in_the_blank", "open_question"])
                
            if st.button("Generate Content", key="btn_gen_content"):
                with st.spinner(f"Generating {content_type} for Week {target_week}..."):
                    
                    params = {
                        "week": target_week,
                        "type": content_type,
                        "difficulty": student_info.get("current_level", 1)
                    }
                    
                    gen_result = st.session_state.unified_agent.generate_content(
                        student_id=student_id,
                        request_params=params
                    )
                
                if "error" in gen_result:
                    st.error(f"Generation failed: {gen_result['error']}")
                else:
                    st.markdown("---")
                    st.subheader(f"Week {target_week} Exercise")
                    st.write(f"**Topic:** {gen_result.get('topic', 'General')}")
                    st.write(f"**Question:** {gen_result.get('question', '')}")
                    
                    if "options" in gen_result and gen_result["options"]:
                        st.write("**Options:**")
                        for opt in gen_result["options"]:
                             st.markdown(f"- {opt}")
                    
                    with st.expander("Show Answer"):
                        st.success(f"Correct Answer: {gen_result.get('correct_answer', 'N/A')}")
                        st.info(f"Explanation: {gen_result.get('explanation', 'N/A')}")

    # TAB 4: EXERCISES
    with tab4:
        st.header("Practice Exercises")
        
        # Get Current Week Info
        curr_week_num = 1
        curr_week_topics = []
        if st.session_state.curriculum:
            curr_week_num = st.session_state.curriculum.get("next_week", 1)
            if "topics_by_week" in st.session_state.curriculum:
                for w in st.session_state.curriculum["topics_by_week"]:
                    if w["week"] == curr_week_num:
                        curr_week_topics = w["topics"]
                        break
        
        st.info(f"📅 **Current Week {curr_week_num}**: {', '.join(curr_week_topics)}")
        
        # Initialize quiz session state if not exists
        if "quiz_session" not in st.session_state:
            st.session_state.quiz_session = None

        # --- SESSION NOT STARTED ---
        if st.session_state.quiz_session is None:
            col1, col2 = st.columns(2)
            with col1:
                mode = st.radio("Mode", ["Practice", "Weekly Exam (Level Up)"], horizontal=True)
            with col2:
                if mode == "Practice":
                    exercise_type = st.selectbox("Exercise Type", ["vocabulary", "grammar", "dialogue"])
                else:
                    st.warning("Pass this exam (80%+) to unlock the next week!")
                    exercise_type = "grammar" # Exam default
            
            if st.button("Start Session (10 Questions)", key="start_session"):
                with st.spinner("Generating 10 questions... This may take a moment."):
                    try:
                        import asyncio
                        
                        topic_prompt = f"{student_info.get('target_language')} {exercise_type}"
                        if curr_week_topics:
                            topic_prompt += f" related to topics: {', '.join(curr_week_topics)}"
                        
                        if mode == "Weekly Exam (Level Up)":
                            topic_prompt += ". Create challenging comprehensive test questions."
                        
                        # Request 10 exercises
                        result_data = asyncio.run(
                            st.session_state.tutor.tools.generate_exercise(
                                topic=topic_prompt,
                                exercise_type=exercise_type,
                                level=student_info.get('current_level', 3),
                                count=10
                            )
                        )
                        
                        exercises_list = []
                        if "exercises" in result_data and isinstance(result_data["exercises"], list):
                            exercises_list = result_data["exercises"]
                        elif isinstance(result_data, list):
                            exercises_list = result_data
                        elif isinstance(result_data, dict) and "error" not in result_data:
                            # Fallback if only 1 returned
                            exercises_list = [result_data]
                        
                        if not exercises_list:
                            st.error("Failed to generate exercises. Please try again.")
                        else:
                            # Initialize Session
                            st.session_state.quiz_session = {
                                "active": True,
                                "questions": exercises_list,
                                "total": len(exercises_list),
                                "current_index": 0,
                                "score": 0,
                                "mode": mode,
                                "exercise_type": exercise_type,
                                "results": [], # To store correct/incorrect for each
                                "completed": False
                            }
                            st.rerun()

                    except Exception as e:
                        st.error(f"Error generating exercises: {e}")

        # --- SESSION ACTIVE ---
        elif st.session_state.quiz_session and not st.session_state.quiz_session["completed"]:
            qs = st.session_state.quiz_session
            idx = qs["current_index"]
            total = qs["total"]
            current_q = qs["questions"][idx]
            
            # Header Status
            c1, c2, c3 = st.columns([1, 2, 1])
            with c1:
                st.metric("Question", f"{idx + 1} / {total}")
            with c3:
                st.metric("Score", f"{qs['score']} / {idx}") # Score so far
            
            # Progress bar
            st.progress((idx) / total)
            
            st.markdown(f"### Question {idx + 1}")
            
            # Display the core content (sentence/text) if available
            if current_q.get('content'):
                st.info(current_q['content'], icon="📖")
            
            st.write(f"**Task:** {current_q.get('task', 'N/A')}")
            st.write(f"**Instructions:** {current_q.get('instructions', 'N/A')}")
            
            # Input Area
            user_answer = None
            answer_submitted = False
            
            # We use a form or just keys to handle state
            # Using a key based on index ensures fresh widget for each question
            input_key = f"q_input_{idx}"
            check_key = f"check_btn_{idx}"
            next_key = f"next_btn_{idx}"
            
            # Determine input type
            if 'options' in current_q and current_q['options']:
                user_answer = st.radio(
                    "Choose Option:",
                    options=current_q['options'],
                    key=input_key
                )
                answer_type = "choice"
            else:
                user_answer = st.text_area(
                    "Your Answer:",
                    height=100,
                    key=input_key
                )
                answer_type = "text"
            
            # State for "Show Result" for THIS question
            if f"q_result_{idx}" not in st.session_state:
                st.session_state[f"q_result_{idx}"] = None
            
            current_result = st.session_state[f"q_result_{idx}"]
            
            if current_result is None:
                if st.button("Check Answer", key=check_key):
                    correct_val = current_q.get('correct_answer', '')
                    is_correct = False
                    
                    if answer_type == "choice":
                        # Handle cases like "B) My name is..." vs "B" or "My name is..."
                        # We try to match:
                        # 1. Exact match
                        # 2. Content match (if correct answer is the text part)
                        # 3. Letter match (if correct answer is 'B')
                        
                        u_ans = user_answer.strip()
                        c_ans = correct_val.strip()
                        
                        # Extract letter if present (e.g., "B) ...")
                        u_letter = u_ans.split(')')[0].strip() if ')' in u_ans else u_ans
                        
                        is_correct = (u_ans == c_ans) or (u_letter == c_ans) or (u_ans in c_ans)
                    else:
                        is_correct = (user_answer.lower().strip() == correct_val.lower().strip())
                    
                    # Update Score
                    if is_correct:
                        qs["score"] += 1
                        st.session_state[f"q_result_{idx}"] = "correct"
                    else:
                        st.session_state[f"q_result_{idx}"] = "incorrect"
                    
                    # Log result
                    qs["results"].append({
                        "question": idx + 1,
                        "correct": is_correct,
                        "user_answer": user_answer,
                        "correct_answer": correct_val
                    })
                    
                    # Save to DB (optional: save per question or at end)
                    # Saving per question is safer for data loss
                    db.db.exercise_results.insert_one({
                        "student_id": student_id,
                        "exercise_id": current_q.get('exercise_id', 'unknown'),
                        "exercise_type": qs["exercise_type"],
                        "correct": is_correct,
                        "mode": qs["mode"],
                        "session_index": idx + 1,
                        "created_at": datetime.datetime.utcnow()
                    })

                    st.rerun()
            else:
                # Show Result Feedback
                correct_val = current_q.get('correct_answer', '')
                explanation = current_q.get('explanation', '')
                
                if current_result == "correct":
                    st.success("✅ Correct!")
                else:
                    st.error("❌ Incorrect")
                    st.info(f"Correct Answer: {correct_val}")
                
                if explanation:
                    st.markdown(f"**Explanation:** {explanation}")
                
                # Next Button
                if st.button("Next Question" if idx < total - 1 else "Finish Session", key=next_key):
                    qs["current_index"] += 1
                    if qs["current_index"] >= total:
                        qs["completed"] = True
                    st.rerun()
        
        # --- SESSION COMPLETED ---
        elif st.session_state.quiz_session and st.session_state.quiz_session["completed"]:
            qs = st.session_state.quiz_session
            score = qs["score"]
            total = qs["total"]
            percent = (score / total) * 100
            passed = percent >= 80
            
            st.markdown(f"## Session Complete! 🏁")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Final Score", f"{score} / {total}")
            with col2:
                st.metric("Percentage", f"{percent:.1f}%")
            with col3:
                st.metric("Result", "PASSED" if passed else "FAILED")
            
            st.divider()
            
            if passed:
                st.balloons()
                st.success("Congratulations! You achieved the target score.")
                
                if qs["mode"] == "Weekly Exam (Level Up)":
                    # Check if we haven't already rewarded this session to prevent double updates on refresh
                    if "rewarded" not in qs:
                       qs["rewarded"] = True 
                       
                       current_lang = student_info.get("target_language", "English")
                       
                       # Ensure we update only the curriculum for this language
                       db.db.curriculums.update_one(
                           {
                               "student_id": student_id,
                               "language": current_lang
                           },
                           {"$inc": {"completed_weeks": 1}}
                       )
                       st.toast("Level Up! Next week unlocked.")
                       st.session_state.curriculum = None # Force refresh
                       st.success(f"🎉 You have officially passed Week {curr_week_num}! Proceeding to Week {curr_week_num + 1}...")
            else:
                st.error("You did not reach the 80% passing mark. Try again!")
                st.write("Review your mistakes and start a new session.")
            
            if st.button("Return to Menu", key="end_session_btn"):
                # Clear session keys
                keys_to_clear = [k for k in st.session_state.keys() if k.startswith("q_input_") or k.startswith("q_result_") or k.startswith("check_btn_")]
                for k in keys_to_clear:
                    del st.session_state[k]
                
                st.session_state.quiz_session = None
                st.rerun()

else:
    st.info("Please enter your name and create your profile to start learning.")
