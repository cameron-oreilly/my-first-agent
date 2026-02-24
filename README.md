# my-first-agent

A minimal conversational AI agent powered by the OpenAI Responses API. The agent runs in a terminal loop, accepts natural language input, and can invoke local tools on your machine when needed.

## Requirements

- Python 3.10+
- An OpenAI API key

## Setup

1. Install dependencies:

   ```bash
   pip install openai python-dotenv
   ```

2. Create a `.env` file in the project root:

   ```
   OPENAI_API_KEY=your-key-here
   ```

3. Run the agent:

   ```bash
   python agent.py
   ```

## How It Works

The agent maintains a conversation context and sends it to the OpenAI Responses API on each turn. When the model decides a tool is needed, the agent executes the tool locally, feeds the result back to the model, and lets the model produce a final response.

```
User input  -->  Model  -->  Tool call?  --yes-->  Execute locally  -->  Model summarizes
                                \--no-->  Direct text response
```

## Functions

| Function | Description |
|---|---|
| `call()` | Sends the current conversation context and tool definitions to the OpenAI Responses API and returns the raw response. |
| `process(line)` | Handles a single user turn: appends the message to context, calls the model, runs any requested tools in a loop, and returns the final text response. |
| `ping(host)` | Executes the system `ping` command against a given hostname or IP address and returns the raw output. Works on both Windows and Unix. |
| `main()` | Runs the interactive input loop, reading user input and printing model responses. |

## Tools

The model can request the following tools during a conversation:

| Tool | Parameters | Description |
|---|---|---|
| `ping` | `host` (string) — hostname or IP address | Pings a host on the internet (4 packets, 15 s timeout) and returns the output. The ping runs locally on your machine via `subprocess`. |

## Project Structure

```
my-first-agent/
├── .env           # API key (git-ignored)
├── .gitignore
├── agent.py       # Agent source code
└── README.md      # This file
```
