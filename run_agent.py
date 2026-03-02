from agents.planner_agent import PlannerAgent
from agents.critic_agent import CriticAgent
from memory.learning_memory import LearningMemory
from memory.working_memory import WorkingMemory
from core.react_loop import ReActLoop
from tools.web_search_tool import WebSearchTool
from tools.python_tool import PythonTool

planner = PlannerAgent()
critic = CriticAgent()

working_memory = WorkingMemory()
learning_memory = LearningMemory()

tools = [WebSearchTool(), PythonTool()]

agent = ReActLoop(
    tools,
    working_memory,
    learning_memory
)

while True:

    query = input("\nAsk: ")

    # ✅ learned memory lookup
    learned = learning_memory.retrieve(query)
    if learned:
        print("\n(learned answer)\n", learned)
        continue

    # ✅ planning
    plan = planner.plan(query)
    print("\nPLAN:\n", plan)

    # ✅ execution
    answer = agent.run(query)

    # ✅ critic verification
    if critic.verify(query, answer):
        learning_memory.store(query, answer)
        agent.metrics.mark_success()
        print("\nFINAL ANSWER:\n", answer)
    else:
        agent.metrics.mark_hallucination()
        print("\n❌ Critic rejected answer.")

    # ✅ metrics logging
    agent.metrics.save(query)
    print(agent.metrics.summary())
    agent.metrics.reset()