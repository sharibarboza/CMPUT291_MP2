import os

# Sort files and get unique rows from command line
os.system("sort terms.txt -u -o terms.txt")
os.system("sort dates.txt -u -o dates.txt")
os.system("sort tweets.txt -u -o tweets.txt")