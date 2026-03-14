# 🧠 ReAct Agent: Self-Learning Multi-Agent Reasoning Framework

<p align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![AI](https://img.shields.io/badge/AI-Multi--Agent-orange)
![Architecture](https://img.shields.io/badge/Architecture-ReAct-green)
![LLM](https://img.shields.io/badge/LLM-Gemini%20%7C%20Groq-purple)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

</p>

---

# 🚀 Overview

**ReAct Agent** is an advanced **autonomous multi-agent reasoning framework** that combines:

- 🧠 Planning
- ⚡ Reasoning
- 🔧 Tool Usage
- 🔍 Critique
- 🪞 Reflection
- 📊 Evaluation

The system is inspired by the **ReAct (Reason + Act)** paradigm used in modern AI agents.

Instead of a single LLM answering a query, the system uses **multiple specialized agents** that collaborate to solve complex tasks.

---

# ✨ Key Features

### 🧭 Planner Agent
Breaks complex problems into structured reasoning steps.

### ⚡ ReAct Agent
Executes reasoning and interacts with tools.

### 🔍 Critic Agent
Checks correctness and detects hallucinations.

### 🪞 Reflection Agent
Analyzes previous reasoning and improves future responses.

### 🧠 Memory System
Stores knowledge and reasoning trajectories.

### 📊 Evaluation Metrics
Measures system performance automatically.

---

# 🏗 System Architecture

```
User Query
     │
     ▼
Planner Agent
(Task Decomposition)
     │
     ▼
ReAct Reasoning Loop
     │
 ┌───┴───────────┐
 ▼               ▼
Tools         Memory
(Web/Python)  (Context)
     │
     ▼
Critic Agent
(Fact Verification)
     │
     ▼
Reflection Agent
(Self Improvement)
     │
     ▼
Evaluation Metrics
```

---

# 📂 Project Structure

```
ReAct_Agent
│
├── agents
│   ├── planner_agent.py
│   ├── react_agent.py
│   ├── critic_agent.py
│   └── reflection_agent.py
│
├── tools
│   ├── web_search_tool.py
│   └── python_tool.py
│
├── memory
│   ├── working_memory.py
│   └── learning_memory.py
│
├── core
│   └── react_loop.py
│
├── config
│   └── settings.py
│
├── evaluation
│   └── run_metrics.json
│
├── metrics.py
├── evaluator.py
├── tool_selector.py
├── report.py
└── run_agent.py
```

---

# ⚙️ Installation

Clone the repository

```bash
git clone https://github.com/darshannikrad/ReAct_Agent.git
cd ReAct_Agent
```

Install dependencies

```bash
pip install -r requirements.txt
```

---

# ▶️ Running the Agent

Start the system:

```bash
python run_agent.py
```

Example query:

```
Ask: What is the capital of Japan?
```

Agent reasoning:

```
Thought: The question asks for a capital city.
Action: search
Observation: Tokyo is the capital of Japan.

Final Answer: Tokyo
```

---

# 🧪 Example ReAct Reasoning

```
Question: What is sqrt(144)?

Thought: This requires mathematical calculation
Action: python_tool
Input: sqrt(144)

Observation: 12

Final Answer: 12
```

---

# 📊 Evaluation Metrics

The framework automatically tracks system performance.

Example output:

```
===== AGENT REPORT =====

Success Rate:        92.3%
Hallucination Rate:  4.5%
Avg Reasoning Steps: 3.6
Avg Tool Calls:      1.7
Avg Token Usage:     1150
```

Metrics stored in:

```
evaluation/run_metrics.json
```

---

# 🧠 Memory System

Two levels of memory are used:

| Memory Type | Purpose |
|-------------|--------|
| Working Memory | Temporary reasoning context |
| Learning Memory | Stores solved tasks for future reuse |

This allows the system to **improve over time**.

---

# 🔧 Tools

The agent can interact with external tools such as:

- 🌐 Web Search
- 🧮 Python Execution
- 📚 Knowledge Retrieval
- 🔌 Custom APIs

Tools are selected dynamically using the **Tool Selector Module**.

---

# 📈 Future Improvements

Planned upgrades:

- Vector database memory
- Multi-tool orchestration
- Autonomous planning loops
- Reinforcement learning
- Multi-agent collaboration
- GUI dashboard for metrics

---

# 🤝 Contributing

Contributions are welcome!

Steps:

```
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Submit a Pull Request
```

---

# 📜 License

MIT License

---

# ⭐ Support

If you find this project useful:

⭐ Star the repository  
🍴 Fork the project  
🚀 Share it with others

---

# 🔬 Research Inspiration

This project is inspired by:

- ReAct: Synergizing Reasoning and Acting in Language Models
- Autonomous AI Agents
- Multi-Agent Systems
- Self-Reflective AI

---

# 👨‍💻 Author

**Darshan Nikrad**

AI / Autonomous Systems

GitHub  
https://github.com/darshannikrad

---

# 🧩 Topics

```
ai-agents
react-agents
multi-agent-system
llm-framework
autonomous-agents
reasoning-ai
self-learning-ai
```
