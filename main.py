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

def run_conversation(user_question):


    try:
        messages = [
            {"role": "system", "content":"""
            When answering computational questions, write the code using the 'run code' tool. Ensure that the code includes print statements to display the results. Do not use the sympy library; instead, utilize other mathematics libraries available in Python.

                Example: 
                Question: Calculate the factorial of 50.
                Response: 
                import math
                result = math.factorial(50)
                print(result)
            """},
            {"role": "user", "content": str(user_question)}
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
            model="gpt-4-1106-preview",
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )

        if not response.choices:
            print("No choices in response")
            return None

        response_message = response.choices[0].message
        #print("1") # Debugging
        print(response_message)

        #print("2") # Debugging
        if not hasattr(response_message, 'tool_calls'):
            print("No tool_calls in response message")
            return response.choices[0].message.content

        #print("3") # Debugging
        tool_calls = response_message.tool_calls
        function_responses = []
        all_the_codes = []
        if tool_calls:
            available_functions = {
                "run_code": run_code,
            }
            #messages.append(response_message)
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
                print("What AI is sending to tool: \n" + str(function_args.get("code"))) # Debugging
                all_the_codes.append(function_args.get("code"))

                function_response = function_to_call(
                    code=function_args.get("code")
                )
                function_responses.append(function_response)

                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": str(function_response),
                    }
                )
                print("Code tool function response: \n", str(function_response)) # Debugging

            second_response = client.chat.completions.create(
                model="gpt-3.5-turbo-1106",
                messages=[
                        {"role": "system", "content": """
                                You are Galileo, an AI to help students solve their questions both technical and non-technical. Your goal is to help students get correct answers and explain to them step by step so they can learn it.
                                To solve some calculations, you wrote some code earlier and ran it in a code sandbox. I will show you the code written and the answer from the sandbox just so you know what's happening - if the sandbox returns an error, don't tell the user 
                                about it. Just try solving it yourself by thinking step by step. 
                                """},
                        {"role": "user", "content": f""" Here's the question the user asked: {str(user_question)}
                                                         Here's the code you wrote earlier: {str(all_the_codes)}
                                                         Here's the answer from the code sandbox after running the code: {str(function_responses)}
                                                         
                                                         Remember, your goal is to explain to the user how you got the answer the way the normal arithmetic way. Don't tell them to write code. If there's an error with the sandbox simply solve the user's question step by step.
                                """}
                        ],
            )

            if not second_response.choices:
                print("No choices in second response")
                return None

            return second_response.choices[0].message.content
        else:
            print("No tool calls to process")
            return response.choices[0].message.content
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

#print(run_code("import math\nresult = math.factorial(50)\nprint(result)"))
question = input("What is your math's question: ")
print(run_conversation(question ))
