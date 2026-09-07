import json

with open('locations.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

converted = [{"name": country, "cities": cities} for country, cities in data.items()]
#filename here 
with open('locations.json', 'w', encoding='utf-8') as f:
    json.dump(converted, f, indent=2, ensure_ascii=False)

print("✅ Conversion complete! Output: locations_converted.json")
