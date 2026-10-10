import csv

postal_patterns = {}

with open('PostCodes.csv', newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        iso = row['ISO'].strip()
        regex = row['Regex'].strip()
        if regex:  
            postal_patterns[iso] = r'^' + regex + r'$'