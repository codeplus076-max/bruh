import sys
import json
import os

# Use relative path resolution so this works on any machine
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

from app.api.predict import client, tools, predictor

messages = [
    {"role": "system", "content": "You are a highly empathetic and professional rural health triage assistant."},
    {"role": "user", "content": "headache"},
    {"role": "assistant", "content": "How old are you? male/female? etc"},
    {"role": "user", "content": "25,male,2 days,2"}
]

print('Sending to OpenRouter/OpenAI...')
try:
    response = client.chat.completions.create(
        model="openai/gpt-3.5-turbo",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )
    msg = response.choices[0].message
    print(f'Response received. Tool calls: {msg.tool_calls}')

    if msg.tool_calls:
        tc = msg.tool_calls[0]
        args = json.loads(tc.function.arguments)
        print(f'Function args: {args}')
        print('Calling predictor...')

        disease = predictor.predict(
            age=args.get('age', 30),
            gender=args.get('gender', 1),
            severity=args.get('severity', 1),
            duration=args.get('duration_days', 1.0)
        )
        print(f'Predictor result: {disease}')
    else:
        print(f'No tool call made. AI response: {msg.content}')

except Exception as e:
    import traceback
    traceback.print_exc()
