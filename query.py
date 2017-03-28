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
        self.set_generalTerms()

        self.results = self.get_results()
        print(self.results) 

    def set_generalTerms(self):
        terms = self.query.split(' ')
        terms = list(filter(lambda x: ':' not in x, terms)) 
        
        for term in terms:
            self.term.append(term)
            self.termPrefix.append(None)
            self.termPattern.append(None)
            self.termQuery.append(term)

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

	        # Get the date string
            index += 1
            q = q[index:]
            index = q.find(' ')

            date = ""
            if index >= 0:
                date = q[:index]
            else:
                date = q

            if len(date) > 0 and date.count('/') == 2:
                self.date.append(date)
                self.datePrefix.append(prefix)
                self.dateQuery.append(prefix + date)

    def set_termGrammar(self, prefix):
        q = self.query
        index = 0
        while index < len(q):
            # Get the term prefix
            index = q.find(prefix)
            if index < 0:
            	break
            q = q[index:]

            # Get the term string
            index = q.index(':') + 1
            q = q[index:]

            index = q.find(' ')
            term = q[:index] if index >= 0 else q 
            if index >= 0:
                term = q[:index]
            else:
            	term = q

            # Check if exact or partial match
            if len(term) > 0 and term[-1] == '%':
                self.termPattern.append(term)
                self.term.append(None)
            else:
                self.termPattern.append(None)
                self.term.append(term)

            self.termPrefix.append(prefix)
            self.termQuery.append(prefix + term)

    def get_results(self):
        tweets = [] 
        d_db = self.dbs['dates']
        d_curs = d_db.cursor()
        i = 0
        for i in range(len(self.date)):
            date = self.date[i].encode('utf-8')
            prefix = self.datePrefix[i][-1]
            exact = prefix ==':'
            date_results = []
            if exact:
                date_results = self.match_date(d_curs, date)
            else:
                date_results = self.match_range(d_curs, date, prefix)
            tweets.extend(date_results)

        return sorted(set(tweets)) 
        		
    def match_date(self, curs, date):
        matches = [] 
        iter = curs.set(date)

        while iter:
           result = curs.get(date, db.DB_CURRENT)
           matches.append(result[1])
           iter = curs.next_dup()

        return matches 

    def match_range(self, curs, date, prefix):
        matches = []
        start = curs.set_range(date)[0]
     
        if prefix == '>':
            iter = curs.next_nodup() 
        else:
            iter = curs.first()

        while iter and iter[0] != start:
            result = curs.get(date, db.DB_CURRENT)
            matches.append(result[1])
            iter = curs.next()
 
        return matches 
        
        
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
