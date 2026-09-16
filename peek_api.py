import json  
import pprint
with open('data/api571_mechanisms_clean.json', encoding='utf-8', errors='ignore') as f: 
    data = json.load(f) 
print('Total entries:', len(data)) 
print('Keys:', list(data[0].keys())) 
pprint.pprint(data[0]) 
