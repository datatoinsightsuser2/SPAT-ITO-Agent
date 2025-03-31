
# Smart Pet Travel Agent

## What's inside?

Here's how I broke down the project:

### 📁 `agent/`
This folder holds all the logic for the assistant and the LangGraph setup.

- `agent.py`: core logic (state + assistant + graph)
- `utils.py`: helper stuff like error handling and pretty printing
- `system_prompt.py`: just a function to load the prompt
- `system_prompt_content.txt`: where the actual prompt lives (easy to edit)

### 📁 `tools/`
Each tool is in its own file. They handle things like:
- fetching user info
- calculating flight quotes
- looking up banned breeds
- getting ground transfer driver options
- answering FAQ stuff from a file

### 📁 `quote/`
This has all the airline rate logic, crate sizing, distance calculation — the works. Everything used to calculate quotes.

### 📁 `data/` & `docs/`
All the JSON files and the FAQ markdown live here. I left them at the root so paths are simple (like `"data/airlines.json"`).

---

## 🛠️ How to run it

Make sure you have:
- Python 3.9+ installed
- `.env` file with your Anthropic / OpenAI keys if you’re using those

Then just run:

```bash
cd ai_agent
python main.py
```