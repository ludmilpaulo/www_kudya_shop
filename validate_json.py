import json

def validate_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            print("JSON is valid")
            return data
    except json.JSONDecodeError as e:
        print(f"JSON decode error at line {e.lineno} column {e.colno}: {e.msg}")
        # Print the surrounding lines for context
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            start = max(0, e.lineno - 3)
            end = min(len(lines), e.lineno + 2)
            for i in range(start, end):
                print(f"{i + 1}: {lines[i].strip()}")
        return None

file_path = 'all_data.json'
validate_json(file_path)
