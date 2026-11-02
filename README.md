# 🚀 RepoPilot — AI Codebase Explainer

**Understand any GitHub repository using AI.**

RepoPilot is an AI-powered codebase exploration tool that helps developers understand unfamiliar codebases faster. It indexes source code, retrieves relevant code snippets, and generates contextual explanations with source references.

Instead of manually navigating hundreds of files, developers can ask questions in natural language and get AI-generated answers grounded in the repository's code.

## ✨ Features

- 🔍 **Repository Indexing** — Index GitHub repositories for code exploration.
- 🤖 **AI-Powered Q&A** — Ask questions about source code in natural language.
- 🧠 **Semantic Search** — Retrieve relevant code using embeddings.
- 📂 **Code Explanations** — Understand functions, classes, modules, and architecture.
- 📌 **Source References** — View relevant file paths and line ranges to verify answers.
- 🖥️ **Local LLM Support** — Generate answers using Ollama.
- ⚡ **CLI Interface** — Index repositories and ask questions from your terminal.
- 🌐 **Web Server** — Launch the application for browser-based access.

## 🛠️ Tech Stack

- **Language:** Python
- **Backend:** FastAPI, Uvicorn
- **LLM Runtime:** Ollama
- **Embeddings:** Sentence Transformers
- **Retrieval:** Semantic search
- **Testing:** Pytest

## 🏗️ How It Works

```text
GitHub Repository
        |
        v
 Repository Indexing
        |
        v
 Source Code Processing
        |
        v
 Chunking and Embeddings
        |
        v
 Searchable Code Index
        |
        v
 Natural Language Question
        |
        v
 Relevant Code Retrieval
        |
        v
 Local LLM (Ollama)
        |
        v
 AI Answer with Source References
```

## 📋 Prerequisites

Install the following before getting started:

- Python 3.10+
- Git
- Ollama
- A compatible local language model

Download Ollama: https://ollama.com/download

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Vinay171105/RepoPilot.git
cd RepoPilot
```

### 2. Create a virtual environment

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows**

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -e ".[embed]"
```

### 4. Download the language model

```bash
ollama pull llama3.1:8b
```

Ensure Ollama is running before using RepoPilot.

### 5. Configure the model

For macOS / Linux, run:

```bash
export REPOPILOT_LLM_BASE_URL=http://localhost:11434/v1
export REPOPILOT_LLM_MODEL=llama3.1:8b
export REPOPILOT_LLM_API_KEY=none
```

These settings configure RepoPilot to use Ollama's local API.

## 💻 Usage

### Index a GitHub repository

```bash
repopilot index pallets/flask
```

Replace `pallets/flask` with the owner and repository name you want to explore.

### Ask questions about the codebase

```bash
repopilot ask pallets-flask "Explain the project architecture"
```

More examples:

```bash
repopilot ask pallets-flask "How does routing work?"
repopilot ask pallets-flask "Explain the main modules"
repopilot ask pallets-flask "Suggest unit tests for the routing module"
```

### List indexed repositories

```bash
repopilot list
```

### Start the web server

```bash
repopilot serve
```

If the server starts on port 8000, open:

http://127.0.0.1:8000

## 📁 Project Structure

```text
RepoPilot/
├── .github/          # GitHub configuration
├── eval/             # Evaluation resources
├── src/              # Application source code
├── tests/            # Automated tests
├── .env.example      # Example environment configuration
├── .gitignore        # Git exclusions
├── LICENSE           # License information
├── pyproject.toml    # Dependencies and project configuration
└── README.md         # Project documentation
```

## 🧪 Testing

Run the automated tests:

```bash
pytest
```

For detailed output:

```bash
pytest -v
```

## 🔒 Security

- Never commit API keys, passwords, or `.env` files.
- Keep `.venv/` and generated indexes out of version control.
- Review files before pushing to GitHub.
- Use trusted repositories when indexing third-party code.

## 🛣️ Future Improvements

- Interactive codebase visualization
- Dependency graph exploration
- Automated bug detection
- AI-generated unit tests
- Multi-repository comparison
- Improved retrieval accuracy
- Support for additional LLMs

## 🤝 Contributing

Contributions and suggestions are welcome.

1. Fork this repository.
2. Create a feature branch.
3. Implement your changes and add tests.
4. Submit a pull request.

## 📄 License

See the [LICENSE](LICENSE) file for license terms.

## 👨‍💻 Author

**Vinay Kokanti**

- GitHub: [@Vinay171105](https://github.com/Vinay171105)

---

⭐ If you find RepoPilot useful, consider starring the repository.

**RepoPilot — Explore codebases faster. Understand code smarter.**
