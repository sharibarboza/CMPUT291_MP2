import os

os.system('db_load -f tweets.txt -T -t hash tweets.db')
os.system('db_dump -p tweets.db')

os.system('db_load -f terms.txt -T -t btree terms.db')
os.system('db_dump -p terms.db')

os.system('db_load -f dates.txt -T -t btree dates.db')
os.system('db_dump -p dates.db')


