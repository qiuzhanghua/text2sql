### Text To SQL Sample

### 0. 前置条件

- Ollama 已经安装好并正常运行
- PostgreSQL is read for user=app, password=app and database=app
- run sample_pg.sql to create a table

### 1. 下载所需的 Ollama 模型

```bash
ollama pull glm4
# memory about 5.5G
# or
ollama pull qwen2.5-coder:14b
# memory about 9G
# or
ollama pull llama3.3
# llama3.3 need (GPU) memory > 42G
```

### 2. Clone 该项目到本地后运行一次

```bash
uv sync
```

### 3. 运行

#### 3.1 Linux/Darwin

````bash
# 替换为你下载的model
TEXT_TO_SQL_MODEL=llama3.3 uv run app.py
# or
uv run app.py


#### 3.2 Windows PowerShell

```powershell
$env:TEXT_TO_SQL_MODEL=qwen2.5-coder:14b; uv run app.py; $env:TEXT_TO_SQL_MODEL=$null
````

#### 3.3 Windows Command Prompt(命令提示符)

```bat
uv run app.py
```

### 参考资料

- [https://ollama.com/](https://ollama.com/)
