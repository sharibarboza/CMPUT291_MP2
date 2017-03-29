# CMPUT 291 Mini Project 2

### How to test your own data files:
Create data files in XML format
See example record file: example.txt

#### Phase 1: Preparing Data Files
Reads tweets records from the data file and outputs dates.txt, terms.txt, and tweets.txt
```
python3 phase1.py example.txt
```

#### Phase 2: Building Indexes
Loads data from text files as key/value pairs in a Berkeley database
```
python3 phase2.py
```

#### Phase 3: Data Retrieval
Query the database, retrieve and output the results
```
python3 main.py
```

##### Example queries:
* name:den% location:canada
* text:iphone date<2012/06/30
* canada
* location:new%
* text:yeg location:edmonton name:michael
* location:vancouver rain

