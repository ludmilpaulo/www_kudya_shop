import json


def remove_authtoken_entries(input_file, output_file):
    with open(input_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    # Filter out entries where model is 'authtoken.token'
    filtered_data = [entry for entry in data if entry["model"] != "authtoken.token"]

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(filtered_data, file, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    input_file = "local.json"  # Path to your input JSON fixture file
    output_file = "filtered_local.json"  # Path to the output JSON file

    remove_authtoken_entries(input_file, output_file)
    print(f"Filtered fixture saved to {output_file}")
