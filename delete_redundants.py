
file_match_lines = []
full_lines = []
with open('zest_data.csv', 'r') as zdata:
    for line in zdata:
        file_match_lines.append(line[:100])
        full_lines.append(line)

list_match_lines = []
filtered_lines = []
for i in range(len(full_lines)):
    if file_match_lines[i] not in list_match_lines:
        list_match_lines.append(file_match_lines[i])
        filtered_lines.append(full_lines[i])

with open('zest_data_filtered.csv', 'w') as zdata_new:
    for line in filtered_lines:
        zdata_new.write(line)
            
