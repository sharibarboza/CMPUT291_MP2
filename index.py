import os

os.system('db_load -f tweets.txt -T -t hash tw.idx')
os.system('db_dump -p tw.idx')

os.system('db_load -f terms.txt -T -t btree te.idx')
os.system('db_dump -p te.idx')

os.system('db_load -f dates.txt -T -t btree da.idx')
os.system('db_dump -p da.idx')

