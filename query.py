from bsddb3 import db


class Query:
    """
	alphanumeric    ::= [0-9a-zA-Z_]
    date            ::= year '/' month '/' day
    datePrefix      ::= 'date' (':' | '>' | '<')
    dateQuery       ::= dataPrefix date
    termPrefix      ::= ('text' | 'name' | 'location') ':'
    term            ::= alphanumeric
    termPattern     ::= alphanumeric '%'
    termQuery       ::= termPrefix? (term | termPattern)
    expression      ::= termQuery | dateQuery
    query           ::= expression | (expression whitespace)+
    """
    
    def __init__(self, db_dict, query):
        self.dbs = db_dict
        self.t_prefixes = ['text:', 'name:', 'location:']
        self.d_prefixes = [':', '<', '>']

        self.date = []
        self.datePrefix = []
        self.dateQuery = []
        self.term = []
        self.termPrefix = []
        self.termPattern = []
        self.termQuery = []
        self.expression = []
        self.query = query

        self.set_dateGrammar()

        for term in self.t_prefixes:
            self.set_termGrammar(term)

        print(self.dateQuery)
        print(self.termQuery)

    def set_dateGrammar(self):
        q = self.query
        index = 0
        while index < len(q):
            # Get the date prefix
            index = q.find('date', index)
            if index < 0:
                break
            
            index += 4
            while q[index] not in self.d_prefixes and index < len(q):
	            index += 1
            prefix = 'date' + q[index]
            self.datePrefix.append(prefix)

	        # Get the date string
            index += 1
            while q[index] == ' ':
	            index += 1      	
            q = q[index:]
            index = q.find(' ')

            date = ""
            if index >= 0:
                date = q[:index]
            else:
                date = q

            # Get the date query altogether       
            self.dateQuery.append(prefix + date)

    def set_termGrammar(self, prefix):
        q = self.query
        index = 0
        while index < len(q):
            # Get the term prefix
            index = q.find(prefix)
            if index < 0:
            	break
            self.termPrefix.append(prefix)
            q = q[index:]

            # Get the term string
            index = q.index(':') + 1
            while q[index] == ' ':
        	    index += 1
            q = q[index:]

            index = q.find(' ')
            term = ""
            if index >= 0:
                term = q[:index]
            else:
            	term = q

            # Check if exact or partial match
            if term[-1] == '%':
            	self.termPattern.append(term)
            else:
            	self.term.append(term)

            # Get the term query altogether
            self.termQuery.append(prefix + term)

        
def main():
    # Get an instance of BerkeleyDB
    db_dict = {}

    database1 = db.DB()
    database1.open('da.idx')
    db_dict['dates'] = database1

    database2 = db.DB()
    database2.open('te.idx')
    db_dict['terms'] = database2

    database3 = db.DB()
    database3.open('tw.idx')
    db_dict['tweets'] = database3

    query = input("Enter query: ").lower()
    q = Query(db_dict, query)

    database1.close()
    database2.close()
    database3.close()

if __name__ == "__main__":
    main()