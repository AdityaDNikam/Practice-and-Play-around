import json
import os
import time
from dotenv import load_dotenv
from openai import OpenAI, RateLimitError
from tools import AVAILABLE_TOOLS, execute_tool

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI Client
# Supports standard OpenAI API or Gemini's OpenAI-compatible endpoint
openai_api_key = os.getenv("OPENAI_API_KEY")
gemini_api_key = os.getenv("GEMINI_API_KEY")

if gemini_api_key:
    # Use Gemini's OpenAI-compatible endpoint with GEMINI_API_KEY
    client = OpenAI(
        api_key=gemini_api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )
    model_env = os.getenv("MODEL_NAME", "models/gemini-3.5-flash-lite")
    DEFAULT_MODEL = model_env if model_env.startswith("models/") else f"models/{model_env}"
elif openai_api_key:
    client = OpenAI(api_key=openai_api_key)
    DEFAULT_MODEL = os.getenv("MODEL_NAME", "gpt-4o-mini")
else:
    raise ValueError("Neither OPENAI_API_KEY nor GEMINI_API_KEY found in environment variables.")

# Chain of Thought (CoT) System Prompt
SYSTEM_PROMPT = """You are an intelligent, analytical AI assistant.

When answering any user request or processing tool data, you MUST follow a strict Chain-of-Thought (CoT) reasoning structure:

1. THOUGHT PROCESS:
   - Identify the user's primary question or request.
   - Determine whether external information or tool usage is required.
   - If tool data is retrieved, break down and evaluate the retrieved metrics step-by-step.
   - Formulate logical conclusions based on factual evidence.

2. FINAL RESPONSE:
   - Provide a clear, accurate response formatted in 2-3 key bullet points.
   - Do not output unnecessary filler text; keep the final answer direct and informative.
"""

def create_completion_with_retry(client, **kwargs):
    """
    Calls chat.completions.create with automatic retry logic for 429 / RateLimit errors.
    """
    max_retries = 5
    base_delay = 5.0
    for attempt in range(1, max_retries + 1):
        try:
            return client.chat.completions.create(**kwargs)
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or isinstance(e, RateLimitError):
                # Try to extract retry delay from error message (e.g. 'retry in 32.9s')
                import re
                match = re.search(r"retry in (\d+(\.\d+)?)s", error_str, re.IGNORECASE)
                if match:
                    wait_time = float(match.group(1)) + 1.0
                else:
                    wait_time = base_delay * (2 ** (attempt - 1))
                
                print(f"\n[Rate Limit / 429 Detected] Quota limit reached. Retrying in {wait_time:.1f} seconds (Attempt {attempt}/{max_retries})...")
                time.sleep(wait_time)
            else:
                raise e
    raise RuntimeError("Exceeded maximum retries due to persistent Rate Limit / 429 errors.")

def Apicall(prompt: str):
    """
    Executes an LLM request using OpenAI SDK with Chain of Thought prompting and multi-step tool integration.
    """
    try:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]

        print(f"\n--- Question: '{prompt}' ---")

        # Initial call to LLM with tool definitions
        response = create_completion_with_retry(
            client,
            model=DEFAULT_MODEL,
            messages=messages,
            tools=AVAILABLE_TOOLS
        )

        response_message = response.choices[0].message
        max_iterations = 10
        iteration_count = 0

        # Loop as long as the model outputs tool calls
        while response_message.tool_calls and iteration_count < max_iterations:
            iteration_count += 1
            # Append assistant's message containing tool calls to context
            messages.append(response_message)

            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)

                print(f"[Tool Call Detected] Executing '{function_name}' with args: {function_args}")
                tool_output = execute_tool(function_name, function_args)
                print(f"[Tool Result Received] {tool_output}")

                # Send tool execution result back to the model context
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_output)
                })

            # Query model again with updated context and tools available
            response = create_completion_with_retry(
                client,
                model=DEFAULT_MODEL,
                messages=messages,
                tools=AVAILABLE_TOOLS
            )
            response_message = response.choices[0].message

        final_content = response_message.content

        print("\n--- Model Response (Chain-of-Thought & Solution) ---")
        print(final_content)

    except Exception as e:
        print(f"API Error: {e}")

if __name__ == "__main__":
    while True:
        User_Prompt = input("Where to start Today?\n =>")
        Apicall(User_Prompt)
