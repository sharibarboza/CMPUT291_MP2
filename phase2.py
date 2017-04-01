import os

# Sort files and get unique rows from command line
os.system("sort terms.txt -u -o terms.txt")
os.system("sort dates.txt -u -o dates.txt")
os.system("sort tweets.txt -u -o tweets.txt")

# Break files
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

# Create indexes in Berekley DB
os.system('db_load -f tweets.txt -T -t hash tw.idx')
print("Loaded database into tw.idx.")
#os.system('db_dump -p tw.idx')

os.system('db_load -f terms.txt -c duplicates=1 -T -t btree te.idx')
print("Loaded database into te.idx.")
#os.system('db_dump -p te.idx')
  
os.system('db_load -f dates.txt -c duplicates=1 -T -t btree da.idx')
print("Loaded database into da.idx.")
#os.system('db_dump -p da.idx')
