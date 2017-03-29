"""
Part of Phase 2
- Prepare data files for loading
- Place keys on first line and values on second line
- Remove any backslashes
- Write changed data back to file
"""

infiles = ['tweets.txt', 'dates.txt', 'terms.txt']

for file in infiles:
    # Open .txt data file
    f1 = open(file, 'r')
    records = f1.read().split('\n')
    f1.close()
    new_records = [] 

    # Change output of record
    for record in records:
        if len(record) > 0:
            # Get keys and values split by first colon
            data = record.split(':', 1)
            key, value = data[0], data[1]

            # Remove backslashes
            if '\\' in value:
            	value = value.replace('\\', '\\\\')
            lines = "%s\n%s\n" % (key, value)
            new_records.append(lines)

    # Write back to .txt file
    f2 = open(file, 'w')
    for record in new_records:
        f2.write(record)
    f2.close()
