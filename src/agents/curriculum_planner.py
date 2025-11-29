# agents/curriculum_planner.py
from typing import Literal, Annotated, List, Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import tools_agent
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
import uuid

from memory.blackboard import Blackboard
from memory.student_profile import StudentProfileDB
from tools.planner_tools import (
    create_initial_curriculum,
    create_lesson_plan,
    update_curriculum_after_lesson,
    write_to_blackboard,
    read_from_blackboard
)
from schemas.models import (
    StudentInfo,
    Curriculum,
    LessonPlan,
    AgentState
)

class CurriculumPlanner:
    def __init__(self, model, student_id: str = None):
        self.model = model
        self.student_id = student_id or str(uuid.uuid4())
        self.profile_db = StudentProfileDB()
        self.blackboard = Blackboard()
        
        # Привязываем инструменты
        self.tools = [
            create_initial_curriculum,
            create_lesson_plan,
            update_curriculum_after_lesson,
            write_to_blackboard,
            read_from_blackboard
        ]
        self.model_with_tools = model.bind_tools(self.tools)

        # Создаём граф
        self.graph = self._create_graph()

    def _planner_node(self, state: AgentState) -> Dict[str, Any]:
        """Основная логика Curriculum Planner"""
        
        # Загружаем профиль студента (долгосрочная память)
        profile = self.profile_db.get_profile(self.student_id)
        current_lesson = self.blackboard.get(self.student_id, {}).get("current_lesson", 1)
        
        system_prompt = f"""Ты — Curriculum Planner в системе персонализированного репетитора по иностранным языкам.
        
        Студент: {profile.get('name', 'Неизвестно')}
        Целевой язык: {profile.get('target_language', 'Неизвестно')}
        Текущий уровень: {profile.get('cefr_level', 'A1')}
        Цели: {profile.get('goals', 'Не указано')}
        Уже пройдено уроков: {current_lesson - 1}
        
        Твои задачи:
        1. Если это первый контакт — провести интервью и создать общий учебный план (curriculum).
        2. Для каждого занятия — создать детальный план урока (lesson plan).
        3. После урока — обновить общий план на основе результатов от Assessor.
        4. Всегда записывать текущий план урока в Blackboard (shared memory).
        
        Используй инструменты строго по назначению. Делегируй выполнение урока — Tutor'у.
        """

        messages = [SystemMessage(content=system_prompt)]
        
        # Добавляем историю (короткосрочная память)
        messages.extend(state["messages"])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
            ("human", "{input}"),
        ])
        
        chain = prompt | self.model_with_tools
        
        response = chain.invoke({
            "input": state["messages"][-1].content if state["messages"] else "Привет! Начнём обучение?",
            "messages": state["messages"][:-1] if len(state["messages"]) > 1 else []
        }, config=RunnableConfig(configurable={"student_id": self.student_id}))
        
        return {"messages": [response]}

    def _should_continue(self, state: AgentState) -> Literal["tools", "end"]:
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return "end"

    def _create_graph(self):
        workflow = StateGraph(AgentState)

        workflow.add_node("planner", self._planner_node)
        workflow.add_node("tools", tools_agent.create_tool_calling_executor(self.model, self.tools))

        workflow.add_edge(START, "planner")
        workflow.add_conditional_edges(
            "planner",
            self._should_continue,
            {
                "tools": "tools",
                "end": END
            }
        )
        workflow.add_edge("tools", "planner")

        # Подключаем чекпоинтер для сохранения состояния между уроками
        memory = SqliteSaver.from_conn_string("checkpoints.db")
        return workflow.compile(checkpointer=memory, interrupt_before=["tools"])
