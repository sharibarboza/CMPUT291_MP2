from bsddb3 import db

from phase1 import get_text

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
    
    def __init__(self, dates_db, terms_db, query):
        """
        Class for parsing queries and returning matches from the Berkeley
        database.

        :param db_dict: contains the dates, terms, and tweets databases
        :param query: query string from user input
        """
        self.dates_db = dates_db
        self.terms_db = terms_db 
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

        # Break down/parse query
        self.set_dateGrammar()
        for term in self.t_prefixes:
            self.set_termGrammar(term)
        self.set_generalTerms() 

    #---------------------------------------------------------------------------

    def set_generalTerms(self):
        """Look for keyword terms with no prefix"""
        terms = self.query.split(' ')
        filtered_terms = []

        for term in terms:
            if all(prefix not in term for prefix in self.d_prefixes):
                filtered_terms.append(term)
 
        for term in filtered_terms:
            self.termPrefix.append(None)
            self.termQuery.append(term)
            self.set_pattern(term)
            
    #---------------------------------------------------------------------------

    def set_dateGrammar(self):
        """Parse the query to set the date, date prefix, and date query"""
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

    #---------------------------------------------------------------------------

    def set_termGrammar(self, prefix):
        """Parse the query and set the term, term prefix, and term query

        :param prefix: either location:, name: or text: 
        """
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

            self.set_pattern(term)
            self.termPrefix.append(prefix)
            self.termQuery.append(prefix + term)

    #---------------------------------------------------------------------------

    def set_pattern(self, term):
        """Set the term and term pattern

        :param term: term from query
        """
        if len(term) > 0 and term[-1] == '%':
            self.termPattern.append(True)
            self.term.append(term[:-1])
        else:
            self.termPattern.append(False)
            self.term.append(term)

    #---------------------------------------------------------------------------

    def add_results(self, tweets, results):
        """Gets the new results and compares them with the previous results

        Takes the intersection of two resulting matches
        :param tweets: results found already
        :param results: new incoming results to be added or intersected
        """
        if tweets is None:
            return results
        else:
            return tweets.intersection(results)

    #---------------------------------------------------------------------------

    def get_results(self):
        """Gets the final results based on the use query"""
        tweets = None
        
        # Match records to date query
        if len(self.date) > 0:
            tweets = self.get_dates()

        # Match records to term query
        if len(self.term) > 0:
            results = self.get_terms()
            tweets = self.add_results(tweets, results)

        return sorted(tweets)

    #---------------------------------------------------------------------------

    def get_terms(self):
        """Match tweet records to term queries with the prefix location:, name:,
        or text: or to all of them if term query has no prefix
        """
        tweets = None

        i = 0
        for i in range(len(self.term)):
            term = self.term[i]
            prefix = self.termPrefix[i]
            partial = self.termPattern[i]
            
            if prefix is None:
                # If term query has no term prefix
                results = self.match_general(term, partial)
            else:
                # If term query has a prefix
                query = (prefix[0] + '-' + term)
                results = self.match_query(self.terms_db, query, partial)

            tweets = self.add_results(tweets, results)

        return tweets

    #---------------------------------------------------------------------------

    def match_general(self, term, partial=False):
        """Check if term matches any records with the prefix location:, name:,
        and text:

        :param term: keyword with no prefix
        :param partial: True if partial, False if exact
        """ 
        matches = set()
        prefixes = ['l-', 'n-', 't-']

        for i in range(3):
            curs = self.terms_db.cursor()
            query_str = prefixes[i] + term
            key = query_str.encode('utf-8')

            if partial:
                iter = curs.set_range(key)
            else:
                iter = curs.set(key)

            while iter and term in iter[0].decode('utf-8'):
                result = curs.get(db.DB_CURRENT)
                matches.add(result[1])
  
                if partial:
                    iter = curs.next()
                else:
                    iter = curs.next_dup()
            curs.close()

        return matches

    #---------------------------------------------------------------------------
        
    def match_query(self, q_db, query, partial=False):
        """Match keywords with an exact match or terms with prefixes with a ':'
        Used for both term and date queries

        :param q_db: dates or term database
        :param query: potential key found in database
        :param partial: True if partial, False if exact
        """ 
        matches = set()
        curs = q_db.cursor()
        key = query.encode('utf-8')

        if partial:
            iter = curs.set_range(key)
        else:
            iter = curs.set(key)

        while iter and query in iter[0].decode('utf-8'):
            result = curs.get(db.DB_CURRENT)
            matches.add(result[1])
 
            if partial:
                iter = curs.next()
            else:
                iter = curs.next_dup()

        curs.close()
        return matches

    #---------------------------------------------------------------------------

    def get_dates(self):
        """Matches tweet records to date query. Date query can be an exact or
        range query
        """
        tweets = set()

        # Multiple exact date matches always return no results
        if len(self.date) > 1 and any('date:' in date for date in self.dateQuery):
            return tweets

        # ':', '<' or '>'
        prefix = self.datePrefix[0][-1]
        exact = prefix ==':'

        if exact:
            tweets = self.match_query(self.dates_db, self.date[0])
        else:
            tweets = self.match_range()

        return tweets

    #---------------------------------------------------------------------------

    def match_range(self):
        """Match range date queries"""
        curs1 = self.dates_db.cursor()
        curs2 = self.dates_db.cursor()

        # Get start and end of date range
        min_date, max_date = self.find_range()
        matches = set()

        # Set cursor 1 to start at minimum date
        start = curs1.set_range(min_date)
     
        if min_date is not None:
            iter = curs1.next_nodup() 
        else:
            iter = curs1.first()      

        if max_date is None:
            max_date = curs2.last()   

        # If start is None, no more dates exist in database
        while start and iter and iter[0] != max_date:
            result = curs1.get(db.DB_CURRENT)
            matches.add(result[1])
            iter = curs1.next()

        curs1.close()
        curs2.close()    
        return matches 

    #---------------------------------------------------------------------------

    def find_range(self):
        """Get the minimum and maximum date to find date range"""
        min_date = None
        max_date = None

        for i in range(len(self.date)):
            date = self.date[i].encode('utf-8')
            
            # '<' or '>'
            prefix = self.datePrefix[i][-1]

            if prefix == '<':
                if max_date is None or date > max_date:
                    max_date = date
            else:
                if min_date is None or date < min_date:
                    min_date = date

        return min_date, max_date

    #---------------------------------------------------------------------------


def display_record(tw_db, tw_id):
    curs = tw_db.cursor()
    record = curs.set(tw_id)[1].decode('utf-8')
    curs.close()

    date = get_text(record, 'created_at')
    text = get_text(record, 'text')
    rt_count = get_text(record, 'retweet_count')
    name = get_text(record, 'name')
    location = get_text(record, 'location')
    description = get_text(record, 'description')
    url = get_text(record, 'url')

    print("Record ID: " + tw_id.decode('utf-8'))    
    print("Created at: %s\nText: %s\nRetweet count: %s" % (date, text, rt_count))
    print("Name: %s\nLocation: %s" % (name, location))
    print("Description: %s\nUrl: %s" % (description, url)) 


#-------------------------------------------------------------------------------


def main():
    # Dates database with date as key, tweet record as value
    database1 = db.DB()
    database1.open('da.idx')

    # Terms database with term query as key, tweet record as value
    database2 = db.DB()
    database2.open('te.idx')

    # Tweets database with tweet record as key, tweet info as value
    database3 = db.DB()
    database3.open('tw.idx')

    # Get user query input
    query = input("Enter query: ").lower()

    # Parse the query and return tweet records that match query
    q = Query(database1, database2, query)
    results = q.get_results()
    
    # Output the results
    border = '-' * 100 
    for result in results:
        print(border)
        display_record(database3, result)
    if len(results) > 0:
        print(border)
    if len(results) == 1:
        print("1 record found.")
    else:
        print("%d records found." % (len(results))) 

    database1.close()
    database2.close()
    database3.close()

if __name__ == "__main__":
    main()
