import json

log_path = r"C:\Users\singh\.gemini\antigravity-ide\brain\86267715-41fa-4794-8758-ad9769900ade\.system_generated\logs\transcript.jsonl"
with open(log_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

for line in reversed(lines):
    data = json.loads(line)
    if data.get('type') == 'USER_INPUT' and 'LMSIS 2.0' in data.get('content', ''):
        with open('full_build_plan.txt', 'w', encoding='utf-8') as out:
            out.write(data['content'])
        print("Successfully extracted full build plan.")
        break
