import uuid
import json
from typing import Literal, List, Dict, Any, Optional
from pydantic import BaseModel

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.prebuilt import ToolNode

# =============================================================================
# 1. Простые хранилища памяти (вместо отдельных модулей)
# =============================================================================

class SimpleBlackboard:
    """Shared memory — «чёрная доска» для всех агентов"""
    def __init__(self):
        self.data: Dict[str, Dict] = {}

    def read(self, student_id: str, key: str = None):
        student_data = self.data.get(student_id, {})
        return student_data if key is None else student_data.get(key)

    def write(self, student_id: str, key: str, value: Any):
        if student_id not in self.data:
            self.data[student_id] = {}
        self.data[student_id][key] = value

    def update(self, student_id: str, updates: Dict):
        if student_id not in self.data:
            self.data[student_id] = {}
        self.data[student_id].update(updates)


class SimpleStudentProfile:
    """Долгосрочная память студента (SQLite + JSON)"""
    def __init__(self, db_path: str = "students.db"):
        import sqlite3
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                student_id TEXT PRIMARY KEY,
                data TEXT
            )
        """)
        self.conn.commit()

    def get(self, student_id: str) -> Dict:
        cur = self.conn.cursor()
        cur.execute("SELECT data FROM profiles WHERE student_id = ?", (student_id,))
        row = cur.fetchone()
        return json.loads(row[0]) if row else {}

    def save(self, student_id: str, data: Dict):
        self.conn.execute("""
            INSERT INTO profiles (student_id, data) 
            VALUES (?, ?)
            ON CONFLICT(student_id) DO UPDATE SET data = excluded.data
        """, (student_id, json.dumps(data)))
        self.conn.commit()


# =============================================================================
# 2. Pydantic-схемы
# =============================================================================

class LessonPlan(BaseModel):
    lesson_number: int
    topic: str
    objectives: List[str]
    duration_minutes: int = 45

class Curriculum(BaseModel):
    total_weeks: int = 12
    topics_per_week: List[str]


# =============================================================================
# 3. Инструменты Curriculum Planner'а
# =============================================================================

blackboard = SimpleBlackboard()
profile_db = SimpleStudentProfile()

@tool
def create_initial_curriculum(
    target_language: str,
    current_level: str,
    goals: str,
    weeks: int = 12
) -> str:
    """Создаёт общий учебный план при первом контакте"""
    curriculum = Curriculum(total_weeks=weeks, topics_per_week=[
        "Знакомство и базовые фразы",
        "Настоящее время", "Семья и описание",
        "Прошедшее время", "Еда и ресторан", "Путешествия", "Работа",
        "Будущее время", "Условное наклонение", "Субхунтив", "Культура", "Итоговый проект"
    ])
    
    profile_db.save(student_id, {
        "target_language": target_language,
        "cefr_level": current_level,
        "goals": goals,
        "curriculum": curriculum.dict()
    })
    
    blackboard.write(student_id, "current_lesson", 1)
    return f"Создан учебный план на {weeks} недель по {target_language} (уровень {current_level})"


@tool
def create_lesson_plan(topic: str, level: str) -> str:
    """Создаёт план текущего урока и кладёт его на blackboard"""
    current = blackboard.read(student_id, "current_lesson") or 1
    plan = LessonPlan(
        lesson_number=current,
        topic=topic,
        objectives=[
            f"Освоить тему «{topic}»",
            "Практика в диалогах",
            "Упражнения на закрепление",
            "Короткий тест"
        ]
    )
    blackboard.write(student_id, "current_lesson_plan", plan.dict())
    blackboard.write(student_id, "current_topic", topic)
    return f"Урок {current}: {topic} — план готов и опубликован на доске!"


@tool
def finish_lesson_and_plan_next(score: int, weak_topics: Optional[List[str]] = None):
    """Вызывается после урока — переходит к следующему"""
    current = blackboard.read(student_id, "current_lesson") or 1
    blackboard.write(student_id, "current_lesson", current + 1)
    blackboard.write(student_id, "last_score", score)
    
    profile = profile_db.get(student_id)
    history = profile.get("lesson_history", [])
    history.append({"lesson": current, "score": score, "weak_topics": weak_topics or []})
    profile["lesson_history"] = history[-20:]  # храним последние 20
    profile_db.save(student_id, profile)
    
    return f"Урок {current} завершён! Оценка: {score}/100. Готовимся к уроку {current + 1}"


tools = [create_initial_curriculum, create_lesson_plan, finish_lesson_and_plan_next]
tool_node = ToolNode(tools)

# =============================================================================
# 4. Сам Curriculum Planner
# =============================================================================

class AgentState(BaseModel):
    messages: List[Any]
    student_id: str

# Глобальный student_id — меняется при каждом новом студенте
student_id = str(uuid.uuid4())

# Выбирай любую модель:
llm = ChatOllama(model="llama3.2:3b", temperature=0.7)
# llm = ChatOllama(model="gemma2:9b")
# llm = ChatOllama(model="phi3:14b")

model_with_tools = llm.bind_tools(tools)

def planner_node(state: AgentState):
    profile = profile_db.get(state.student_id)
    lesson_no = blackboard.read(state.student_id, "current_lesson") or 1
    
    system = f"""Ты — Curriculum Planner в персонализированном репетиторе по иностранным языкам.
Студент ID: {state.student_id}
Язык: {profile.get('target_language', 'не указан')}
Уровень: {profile.get('cefr_level', 'A1')}
Текущий урок: {lesson_no}

Твои задачи:
- При первом контакте — спроси язык, уровень, цели и вызови create_initial_curriculum.
- На каждом занятии — создай план урока через create_lesson_plan.
- После завершения урока (когда скажут) — вызови finish_lesson_and_plan_next.
- Всегда используй инструменты, когда нужно что-то зафиксировать.

Отвечай на русском или на целевом языке — как удобнее студенту.
"""

    messages = [SystemMessage(content=system)] + state.messages
    response = model_with_tools.invoke(messages)
    return {"messages": [response]}

def should_continue(state: AgentState) -> Literal["tools", "__end__"]:
    last_msg = state.messages[-1]
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        return "tools"
    return "__end__"

# =============================================================================
# 5. Сборка графа
# =============================================================================

workflow = StateGraph(AgentState)

workflow.add_node("planner", planner_node)
workflow.add_node("tools", tool_node)

workflow.add_edge(START, "planner")
workflow.add_conditional_edges("planner", should_continue)
workflow.add_edge("tools", "planner")

memory = SqliteSaver.from_conn_string("curriculum_checkpoints.db")
app = workflow.compile(checkpointer=memory)

# =============================================================================
# 6. Запуск чата (просто запусти файл)
# =============================================================================

if __name__ == "__main__":
    print("Curriculum Planner запущен!")
    print("Напиши «новый студент» — чтобы начать с чистого листа")
    print("Напиши «выход» для завершения\n")

    config = {"configurable": {"thread_id": "curriculum_thread", "student_id": student_id}}

    while True:
        user_input = input("\nТы: ").strip()
        if user_input.lower() in ["выход", "exit", "quit"]:
            break
        if user_input.lower() == "новый студент":
            student_id = str(uuid.uuid4())
            config["configurable"]["student_id"] = student_id
            blackboard.data.pop(student_id, None)
            print("Новый студент создан! ID:", student_id)
            continue

        # Обновляем текущий student_id в конфиге
        config["configurable"]["student_id"] = student_id

        for chunk in app.stream(
            {"messages": [HumanMessage(content=user_input)], "student_id": student_id},
            config,
            stream_mode="values"
        ):
            msg = chunk["messages"][-1]
            if isinstance(msg, AIMessage) and msg.content:
                print(f"Planner: {msg.content}")
            elif isinstance(msg, ToolMessage):
                print(f"Инструмент: {msg.content}")
