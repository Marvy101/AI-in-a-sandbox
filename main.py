import requests
from openai import OpenAI
import json
from love import OPENAIKEY, RapidAPI_1COMPKEY

client = OpenAI(api_key=OPENAIKEY)

def run_code(code):
    print("Executing Code...")
    #code = f""" {code} """
    payload = {
        "language": "python",
        "stdin": "",
        "files": [
            {
                "name": "index.py",
                "content": code
            }
        ]
    }

    url = "https://onecompiler-apis.p.rapidapi.com/api/v1/run"

    headers = {
        "content-type": "application/json",
        "X-RapidAPI-Key": RapidAPI_1COMPKEY,
        "X-RapidAPI-Host": "onecompiler-apis.p.rapidapi.com"
    }

    response = requests.post(url, json=payload, headers=headers)

    # Check if the response is successful
    if response.status_code == 200:
        print("Answer from code tool: "+str(response.json()))
        return response.json()
    else:
        return f"Error: {response.status_code}"

def run_conversation():
    # Step 1: send the conversation and available functions to the model
    messages = [
        {"role": "system", "content": "you are  an AI that answers various questions. For calculation requests, you will write and execute the code to ensure reliability using the run code tool. You must write print in the code that is sent to the run_code tool to see results "},
        {"role": "user", "content": "generate a very hard question and answer it youeself also tell me the question and how it was solved in the final putput"}
    ]
    tools = [
        {
            "type": "function",
            "function": {
                "name": "run_code",
                "description": "Run Python code using a specified API. ",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "The Python code to be executed",
                        }
                    },
                    "required": ["code"],
                },
            },
        }
    ]
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=messages,
        tools=tools,
        tool_choice="auto",  # auto is default, but we'll be explicit
    )
    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls
    # Step 2: check if the model wanted to call a function
    if tool_calls:
        # Step 3: call the function
        # Note: the JSON response may not always be valid; be sure to handle errors
        available_functions = {
            "run_code": run_code,
        }  # only one function in this example, but you can have multiple
        messages.append(response_message)  # extend conversation with assistant's reply
        # Step 4: send the info for each function call and function response to the model
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            print("What AI is sending to tool "+str(function_args.get("code")))
            function_response = function_to_call(
                code=function_args.get("code"),
            )
            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": str(function_response),
                }
            )  # extend conversation with function response
        second_response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=messages,
        )  # get a new response from the model where it can see the function response
        return second_response.choices[0].message

print(run_conversation())