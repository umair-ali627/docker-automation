import json
import uuid

def replace_ids_with_new_uuids(input_file, output_file):
    # Read the JSON data from file
    with open(input_file, 'r') as file:
        data = json.load(file)
    
    # Replace each "id" field with a new UUID
    for item in data:
        # Generate a new UUID and convert to string
        new_uuid = str(uuid.uuid4())
        # Replace the existing ID
        item["id"] = new_uuid
    
    # Write the updated JSON to the output file
    with open(output_file, 'w') as file:
        json.dump(data, file, indent=2)
    
    print(f"Updated IDs with new UUIDs and saved to {output_file}")

# Example usage
input_file = "voices.json"  # Change this to your input file name
output_file = "voices.json"  # Change this to your desired output file name

replace_ids_with_new_uuids(input_file, output_file)