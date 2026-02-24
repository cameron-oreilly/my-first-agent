from openai import OpenAI
import json
import os
import platform
import subprocess

client = None
context = []

tools = [
    {
        "type": "function",
        "name": "ping",
        "description": "Ping a host on the internet and return the result. Use this when the user asks to ping a host or check if a host is reachable.",
        "parameters": {
            "type": "object",
            "properties": {
                "host": {
                    "type": "string",
                    "description": "The hostname or IP address to ping, e.g. 'google.com' or '8.8.8.8'"
                }
            },
            "required": ["host"],
            "additionalProperties": False
        },
        "strict": True
    }
]


def init(api_key: str):
    global client, context
    client = OpenAI(api_key=api_key)
    context = []


def ping(host: str) -> str:
    count_flag = "-n" if platform.system().lower() == "windows" else "-c"
    try:
        result = subprocess.run(
            ["ping", count_flag, "4", host],
            capture_output=True, text=True, timeout=15
        )
        return result.stdout if result.returncode == 0 else result.stderr or result.stdout
    except subprocess.TimeoutExpired:
        return f"Ping to {host} timed out."
    except Exception as e:
        return f"Error pinging {host}: {e}"


tool_map = {
    "ping": ping
}


def call():
    return client.responses.create(model="gpt-5.2", input=context, tools=tools)


def process(line):
    context.append({"role": "user", "content": line})
    response = call()

    while response.output:
        tool_calls = [o for o in response.output if o.type == "function_call"]
        if not tool_calls:
            break

        context.extend(response.output)

        for tc in tool_calls:
            args = json.loads(tc.arguments)
            result = tool_map[tc.name](**args)
            context.append({"type": "function_call_output", "call_id": tc.call_id, "output": result})

        response = call()

    context.append({"role": "assistant", "content": response.output_text})
    return response.output_text


def main():
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not found in environment or .env file.")
        return
    init(api_key)
    while True:
        line = input("> ")
        result = process(line)
        print(f">>> {result}\n")


if __name__ == "__main__":
    main()
