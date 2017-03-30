from bsddb3 import db

from phase1 import get_text

class Node:

    def __init__(self, data=None, next_node=None):
        self.data = data
        self.next_node = next_node

    def get_data(self):
        return self.data

    def get_next(self):
        return self.next_node

    def set_next(self, node):
        self.next_node = node

    def set_data(self, data):
        self.data = data


class LinkedList:

    def __init__(self, head=None):
        self.head = head

    def insert(self, data):
        code = data['code']
        current = self.head
        previous = None

        while current != None:
            cur_data = current.get_data()
            other_code = cur_data['code']

            if code <= other_code:
                break
            else: 
                previous = current
                current = current.get_next() 
         
        new_node = Node(data, current)
        if previous is None:
            self.head = new_node            
        else:
            previous.set_next(new_node)

    def get_head(self):
        return self.head 


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

        :param dates_db: dates database with date as key
	      :param terms_db: terms database with prefix/term as key
        :param query: query string from user input
        """
        self.dates_db = dates_db
        self.terms_db = terms_db 
        self.t_prefixes = ['text:', 'name:', 'location:']
        self.d_prefixes = [':', '<', '>']

        self.terms = query.split()
        self.linked_list = LinkedList()
        self.results = None 
        self.sort_terms()

    #---------------------------------------------------------------------------

    def get_results(self):
        current = self.linked_list.get_head()

        while current != None:
            data = current.get_data()
            query = data['term']
            prefix = data['prefix']

            if prefix is None or 'date' not in prefix:
                records = self.get_terms(query, prefix)
            else:
                records = self.get_dates(query, prefix[-1])

            if len(records) == 0:
                self.results = set()
                break
            elif self.results is None:
                self.results = records
            elif len(self.results) == 0:
                break 
            else:
                self.results = self.results.intersection(records)

            current = current.get_next()

        return sorted(self.results) 

    #---------------------------------------------------------------------------

    def sort_terms(self):
        for term in self.terms:
            prefix = None
            mid = None

            if len(term) > 0 and term[-1] == '%':
                partial = True
            else:
                partial = False

            if ':' in term:
                mid = ':'
            elif '>' in term:
                mid = '>'
            elif '<' in term:
                mid = '<'
            
            if mid:
                prefix, term = term.split(mid)
            code = self.classify_term(term, prefix, mid, partial)

            if prefix:
                prefix += mid
            data = {'code': code, 'prefix': prefix, 'term': term}
            self.linked_list.insert(data)

    #---------------------------------------------------------------------------

    def classify_term(self, term, prefix, mid, partial):
        if prefix == 'date':
            if mid == ':':
                return 4
            else:
                return 9
        elif partial:
            if prefix == 'name':
                return 6
            elif prefix == 'location':
                return 7
            elif prefix == 'text':
                return 8
            else:
                return 10
        else:
            if prefix == 'name':
                return 1
            elif prefix == 'location':
                return 2
            elif prefix == 'text':
                return 3
            else:
                return 5 
        
    #---------------------------------------------------------------------------

    def get_terms(self, term, prefix):
        """Match tweet records to term queries with the prefix location:, name:,
        or text: or to all of them if term query has no prefix
        """
        if len(term) > 0 and term[-1] == '%':
            partial = True
            term = term[:-1]
        else:
            partial = False 
            
        if prefix is None:
            # If term query has no term prefix
            return self.match_general(term, partial)
        else:
            # If term query has a prefix
            query = (prefix[0] + '-' + term)
            return self.match_query(self.terms_db, query, partial)

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
        """Match keywords with an exact match or terms with a colon in the prefix
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

    def get_dates(self, date, mid):
        """Matches tweet records to date query. Date query can be an exact or
        range query
        """
        if mid == ':': 
            return self.match_query(self.dates_db, date)
        else:
            return self.match_range(date, mid)

    #---------------------------------------------------------------------------

    def match_range(self, date, mid):
        """Match range date queries"""
        curs1 = self.dates_db.cursor()
        matches = set()

        date = date.encode('utf-8')
        curs1.set_range(date)
        if mid == '<':
            iter = curs1.first()
        else: 
            iter = curs1.next_nodup()

        while iter: 
            if mid == '<' and iter[0] >= date:
                break 
            matches.add(iter[1])
            iter = curs1.next()

        curs1.close()
        return matches 

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
    again = 'y'
    affirmatives = ['y', 'yes', '1'] 
    while again in affirmatives: 
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

        again = input("Do you want to make another query? y/n: ").lower()

    database1.close()
    database2.close()
    database3.close()

if __name__ == "__main__":
    main()
