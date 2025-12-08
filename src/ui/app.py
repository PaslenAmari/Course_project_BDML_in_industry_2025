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

if "tutor" not in st.session_state:
    try:
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
            
            with st.expander("View Full Curriculum", expanded=True):
                # Fallback: if 'topics_by_week' is missing (due to stale agent), fetch from DB
                display_topics = plan_result.get("topics_by_week")
                if not display_topics:
                    full_curr = db.get_curriculum(student_id)
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
        
        col1, col2 = st.columns(2)
        with col1:
             mode = st.radio("Mode", ["Practice", "Weekly Exam (Level Up)"], horizontal=True)
             
        with col2:
             if mode == "Practice":
                exercise_type = st.selectbox("Exercise Type", ["vocabulary", "grammar", "dialogue"])
             else:
                st.warning("Pass this exam to unlock the next week!")
                exercise_type = "grammar" # Exam default
        
        if st.button("Generate New Exercise", key="gen_exercise"):
            st.session_state.current_exercise = None
        
        if "current_exercise" not in st.session_state:
            st.session_state.current_exercise = None
        
        if st.button("Generate", key="do_gen") or st.session_state.current_exercise is None:
            with st.spinner("Generating exercise..."):
                try:
                    import asyncio
                    
                    topic_prompt = f"{student_info.get('target_language')} {exercise_type}"
                    if curr_week_topics:
                        topic_prompt += f" related to topics: {', '.join(curr_week_topics)}"
                    
                    if mode == "Weekly Exam (Level Up)":
                        topic_prompt += ". Create a challenging comprehensive test question."
                    
                    exercise = asyncio.run(
                        st.session_state.tutor.tools.generate_exercise(
                            topic=topic_prompt,
                            exercise_type=exercise_type,
                            level=student_info.get('current_level', 3)
                        )
                    )
                    
                    # Tag exercise with mode
                    exercise["mode"] = mode
                    
                    st.session_state.current_exercise = exercise
                    st.session_state.exercise_answered = False
                    
                except Exception as e:
                    st.error(f"Error generating exercise: {e}")
        
        if st.session_state.current_exercise:
            ex = st.session_state.current_exercise
            ex_mode = ex.get("mode", "Practice")
            
            if "error" in ex:
                st.error(f"Exercise generation error: {ex['error']}")
            else:
                if ex_mode == "Weekly Exam (Level Up)":
                     st.write(f"### **WEEK {curr_week_num} EXAM** 🎓")
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
                        
                        # Save result
                        db.db.exercise_results.insert_one({
                            "student_id": student_id,
                            "exercise_id": ex.get('exercise_id', 'unknown'),
                            "exercise_type": exercise_type,
                            "correct": True,
                            "mode": ex_mode,
                            "student_answer": answer,
                            "created_at": datetime.datetime.utcnow()
                        })
                        
                        # LEVEL UP LOGIC
                        if ex_mode == "Weekly Exam (Level Up)":
                            st.toast("Level Up! Updating curriculum...")
                            db.db.curriculums.update_one(
                                {"student_id": student_id},
                                {"$inc": {"completed_weeks": 1}}
                            )
                            # Force refresh of curriculum in session
                            st.session_state.curriculum = None
                            st.balloons()
                            st.success(f"🎉 You have passed Week {curr_week_num}! proceeding to Week {curr_week_num + 1}...")
                            st.rerun()

                        st.session_state.exercise_answered = True
                    else:
                        st.error("Incorrect!")
                        st.info(f"**Correct answer:** {correct}")
                        
                        db.db.exercise_results.insert_one({
                            "student_id": student_id,
                            "exercise_id": ex.get('exercise_id', 'unknown'),
                            "exercise_type": exercise_type,
                            "correct": False,
                            "mode": ex_mode,
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
