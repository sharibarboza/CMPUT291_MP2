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
        filtered_terms = []
        for term in terms:
            if all(prefix not in term for prefix in self.d_prefixes):
                filtered_terms.append(term)
 
        for term in filtered_terms:
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

    def add_results(self, tweets, results):
        if tweets is None:
            return results
        else:
            return tweets.intersection(results)

    def get_results(self):
        tweets = None
        
        # Match records to date query
        if len(self.date) > 0:
            tweets = self.get_dates()

        # Match records to term query
        if len(self.term) > 0:
            results = self.get_terms()
            tweets = self.add_results(tweets, results)

        return sorted(tweets)

    def get_terms(self):
        tweets = None
        t_db = self.dbs['terms']

        i = 0
        for i in range(len(self.term)):
            term = self.term[i]
            prefix = self.termPrefix[i]
            
            if prefix is None:
                results = self.match_general(t_db, term)
            else:
                query = (prefix[0] + '-' + term)
                results = self.match_query(t_db, query)

            tweets = self.add_results(tweets, results)

        return tweets

    def match_general(self, q_db, term):
        matches = set()
        prefixes = ['l-', 'n-', 't-']

        for i in range(3):
            curs = q_db.cursor()
            query_str = prefixes[i] + term
            query = query_str.encode('utf-8')
            iter = curs.set(query)

            while iter:
                result = curs.get(db.DB_CURRENT)
                matches.add(result[1])
                iter = curs.next_dup()

            curs.close()
     
        return matches
        
    def match_query(self, q_db, query):
        matches = set()
        curs = q_db.cursor()
        query = query.encode('utf-8')
        iter = curs.set(query)
        
        while iter:
            result = curs.get(db.DB_CURRENT)
            matches.add(result[1])
            iter = curs.next_dup()

        curs.close()
        return matches

    def get_dates(self):
        tweets = set()
        d_db = self.dbs['dates']

        if len(self.date) > 1 and any('date:' in date for date in self.dateQuery):
            return tweets

        prefix = self.datePrefix[0][-1]
        exact = prefix ==':'

        if exact:
            tweets = self.match_query(d_db, self.date[0])
        else:
            tweets = self.match_range(d_db)

        return tweets

    def match_range(self, d_db):
        curs1 = d_db.cursor()
        curs2 = d_db.cursor()

        min_date, max_date = self.find_range()
        matches = set()
        start = curs1.set_range(min_date)[0]
     
        if min_date is not None:
            iter = curs1.next_nodup()
        else:
            iter = curs1.first()

        if max_date is None:
            max_date = curs2.last()

        while iter and iter[0] != max_date:
            result = curs1.get(db.DB_CURRENT)
            matches.add(result[1])
            iter = curs1.next()

        curs1.close()
        curs2.close()    
 
        return matches 

    def find_range(self):
        min_date = None
        max_date = None

        for i in range(len(self.date)):
            date = self.date[i].encode('utf-8')
            prefix = self.datePrefix[i][-1]

            if prefix == '<':
                if max_date is None or date > max_date:
                    max_date = date
            else:
                if min_date is None or date < min_date:
                    min_date = date

        return min_date, max_date


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
