from bsddb3 import db

from phase1 import get_text

#------------------------------------------------------------------------

class Node:

    def __init__(self, data=None, next_node=None):
        """Node object for linked list
        :param data: dictionary containing term query data 
        :param next_node: what current node is pointing to
        """
        self.data = data
        self.next_node = next_node

    def get_data(self):
        """Get the node dictionary"""
        return self.data

    def get_next(self):
        """Get the next node"""
        return self.next_node

    def set_next(self, node):
        """Set the next node"""
        self.next_node = node

#------------------------------------------------------------------------

class LinkedList:

    def __init__(self, head=None):
        """Singly linked list consisting of nodes
        Each node contains a one-word query term
        """
        self.head = head

    def get_head(self):
        """Returns the start of the linked list"""
        return self.head

    def insert(self, data):
        """Inserts a new node into the linked list based on data values

        Each data dictionary contains a code that corresponds to a 
        query term. Ensures that nodes are stored in ascending order of
        code values.
        :param data: dictionary with query term code
        """
        code1 = data['code']
        prefix1 = data['prefix']
        term1 = data['term']
        term1 = term1[:-1] if is_partial(term1) else term1
        current = self.head
        previous = None
        new_node = Node(data, current)

        # Search for a position to insert
        while current != None:
            cur_data = current.get_data()
            code2 = cur_data['code']
            prefix2 = cur_data['prefix']
            term2 = cur_data['term']
            term2 = term2[:-1] if is_partial(term2) else term2
 
            # Check if term to be inserted is longer
            both = both_terms(prefix1, prefix2)
            if both and code1 < code2 and (len(term1) - len(term2) > 0):
                break 
           
            # Term not inserted here, so get next node 
            previous = current
            current = current.get_next() 
        
        # Insert node before current node
        new_node = Node(data, current) 
        if previous is None:
            self.head = new_node            
        else:
            previous.set_next(new_node)

#---------------------------------------------------------------------------

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
        :param terms_db: terms database with term as key
        :param query: query string from user input
        """
        self.dates_db = dates_db
        self.terms_db = terms_db 
        self.t_prefixes = ['text:', 'name:', 'location:']
        self.d_prefixes = ['date:', 'date<', 'date>']

        self.results = None
        self.terms = query.split()
        self.linked_list = LinkedList()
        self.sort_terms()

    #---------------------------------------------------------------------------

    def get_results(self):
        """Get the results of the query. After the order of the terms are sorted
        into a linked list, get the results of each term and intersect them with
        the current result matches.
        """
        current = self.linked_list.get_head()
        while current != None:
            data = current.get_data()
            query = data['term']
            prefix = data['prefix']

            # Get the results from database based on query term
            if prefix is None or 'date' not in prefix:
                records = self.get_terms(query, prefix)
            else:
                records = self.get_dates(query, prefix[-1])

            # If records returns nothing, then we're done
            if len(records) == 0:
                self.results = set()
                break
            elif self.results is None:
                self.results = records
            else:
                self.results = self.results.intersection(records)

            # Immediately exit if intersecting produces nothing
            if self.results and len(self.results) == 0:
                break 
            current = current.get_next()
        return sorted(self.results) if self.results else []

    #---------------------------------------------------------------------------

    def sort_terms(self):
        """Sort individual query terms. Terms with prefixes/exact queries are
        considered first because they are more likely to return smaller result
        sets than partial/range queries.

        Term order is maintained by storing each term in a linked list.
        """
        for term in self.terms:
            prefix = None
            partial = is_partial(term)
            mid = self.find_separator(term)
            word = term

            # If term has a prefix
            if mid:
                prefix, word = term.split(mid)

            # Get relative position of term for linked list
            code = self.classify_term(word, prefix, mid, partial)

            if prefix:
                if not self.valid_prefixes(prefix + mid): 
                    prefix = None
                    word = term
                else:
                    prefix += mid

            # Data to be stored in node
            data = {'code': code, 'prefix': prefix, 'term': word}
            self.linked_list.insert(data)

    #---------------------------------------------------------------------------

    def find_separator(self, term):
        """Find whether a term has a prefix or not and whether the prefix and
        term is separated by ':', '<', or '>'.
        """
        separator = None
        if ':' in term:
            separator = ':'
        elif '>' in term:
            separator = '>'
        elif '<' in term:
            separator = '<'
        return separator
 
    #---------------------------------------------------------------------------

    def valid_prefixes(self, prefix):
        """Returns True if the prefix is a valid prefix"""
        if prefix in self.t_prefixes or prefix in self.d_prefixes:
            return True
        else:
            return False

    #---------------------------------------------------------------------------

    def classify_term(self, term, prefix, mid, partial):
        """Determine the code value for a term. The lower the return value, the
        earlier the term query should be processed.

        :param term: single keyword
        :param prefix: either name, location, text, or date
        :param mid: either None, :, <, or >
        :param partial: True if mid is < or >
        """
        code = 10
        if prefix == 'date':
            code = 8 if mid == ':' else 9
        elif prefix == 'name':
            code = 5 if partial else 1
        elif prefix == 'location':
            code = 6 if partial else 2
        elif prefix == 'text':
            code = 7 if partial else 3 
        return code 
        
    #---------------------------------------------------------------------------

    def get_terms(self, term, prefix):
        """Match tweet records to term queries with the prefix location:, name:,
        or text: or to all of them if term query has no prefix
        """
        if is_partial(term): 
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
            query = prefixes[i] + term
            results = self.match_query(self.terms_db, query, partial)
            matches.update(results)
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

        # Get starting index
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
        """Match range date queries to find records either below/above the date

        :param date: date query
        :param mid: either < or >
        """
        curs1 = self.dates_db.cursor()
        matches = set()
        date = date.encode('utf-8')
        start = curs1.set_range(date)

        # Determine which index to start iterating at
        if mid == '<':
            iter = curs1.first()
        else: 
            iter = curs1.next_nodup()

        # Iterate until the query date or the end of database
        while start and iter:
            if mid == '<' and iter[0] >= date:
                break 
            matches.add(iter[1])
            iter = curs1.next()
        curs1.close()
        return matches 


#---------------------------------------------------------------------------


def is_partial(term):
    """Return True if term is querying a partial match"""
    if len(term) > 0:
        return term[-1] in ['%', 37]
    else:
        return False


def both_terms(prefix1, prefix2):
    """Return True if both prefixes are not date prefixes"""
    both = True
    if prefix1 and 'date' in prefix1:
        both = False
    if prefix2 and 'date' in prefix2:
        both = False
    return both 


def display_record(tw_db, tw_id):
    """Display tweet record information to the console"""
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
