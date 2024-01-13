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
        #print("Answer from code tool: "+str(response.json())) #debugging
        return response.json()
    else:
        return f"Error: {response.status_code}"

def run_conversation(prompt):
    try:
        messages = [
            {"role": "system", "content":
            f"""
            You are an AI that answers various questions correctly. For calculation requests, you MUST write and execute the code to ensure reliability using the run code tool then after writing the code, always print(result) so that the user can see the end result. Use popular maths libraries except sympy.
            For example: 
            Question from user: What is the factorial of 50.
             -> write the code and add print at the end: import math \n result = math.factorial(50) \n print(result)
            """},
            {"role": "user", "content": str(prompt)}
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
            tool_choice="auto",
        )

        if not response.choices:
            print("No choices in response")
            return None

        response_message = response.choices[0].message
        #print("1") # Debugging
        #print(response_message)

        #print("2") # Debugging
        if not hasattr(response_message, 'tool_calls'):
            print("No tool_calls in response message")
            
            return None

        #print("3") # Debugging
        tool_calls = response_message.tool_calls
        if tool_calls:
            available_functions = {
                "run_code": run_code,
            }
            messages.append(response_message)
            for tool_call in tool_calls:
                #print("4") # Debugging
                #print(str(tool_call)) # Debugging
                function_name = tool_call.function.name
                #print("5") # Debugging
                function_to_call = available_functions.get(function_name)
                if not function_to_call:
                    print(f"No available function called {function_name}")
                    continue
                #print("6") # Debugging
                #print(str(tool_call)) # Debugging
                function_args = json.loads(tool_call.function.arguments)
                #print("What AI is sending to tool: \n" + str(function_args.get("code"))) # Debugging
                function_response = function_to_call(
                    code=function_args.get("code")+"\nprint(result)", #adding print results because GPT3 just does not want to print the results lol. You don't need this if GPT4 writes the code however
                )

                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": str(function_response),
                    }
                )
                #print("Code tool function response: \n", str(function_response)) # Debugging

            second_response = client.chat.completions.create(
                model="gpt-3.5-turbo-1106",
                messages=messages,
            )

            if not second_response.choices:
                print("No choices in second response")
                return None

            return second_response.choices[0].message.content
        else:
            print("No tool calls to process")
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

#print(run_code("import math\nresult = math.factorial(50)\nprint(result)"))
print(run_conversation('write a very hard maths problem and solve it to tell me the answer that requires external libraries'))