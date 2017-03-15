import re
import xml.etree.ElementTree as ET

tree = ET.parse('data.txt')
root = tree.getroot()


def strip_text(string, tag):
    """Removes tags from string

    :param string: tag + text string
    :param tag: tag label
    """
    string = string.decode('ascii')
    opening = "<%s>" % (tag)
    closing = "</%s>" % (tag)

    if opening in string and closing in string:
        string = string.replace(opening, '').replace(closing, '')
    else:
        string = ""
    return string

def convert_quote(string):
    """Escape html for double quotation marks

    :param string: text inside tag
    """
    return string.replace('"', " &quot ")	

def filter_len(term):
    """Ignore terms of length 2 or less

    :param term: string token
    """
    return len(term) > 2

def filter_html(term):
    """Ignore all special characters coded as &#number

    :param term: string token
    """
    return False if '&#' in term else True

def filter_string(string):
    """Remove unwanted characters from string text

    :param string: tag + text
    """
    string = convert_quote(string)
    tokens = ' '.join(re.split(';', string))
    string = tokens.replace(',', '')
    tokens = string.split()
    tokens = list(filter(filter_html, tokens))
    return ' '.join(tokens)

def filter_tokens(string):
    """Remove unwanted terms from tokens and convert to lowercase

    :param string: filtered string
    """
    tokens = re.split('[\W]', string)
    tokens = list(filter(filter_len, tokens))
    return [token.lower() for token in tokens]

def get_terms(string, tag):
    """Tokenize the string and return the tokens in a list

    :param string: tag + text
    :param tag: tag label
    """
    tokens = []
    raw_txt = strip_text(ET.tostring(string), tag)
    filtered_txt = filter_string(raw_txt)
    tokens = filter_tokens(filtered_txt)
    return tokens


#--------------------------------MAIN-----------------------------------

def main():
    # Phase 1: Preparing data files
    outfile1 = 'terms.txt'
    f1 = open(outfile1, 'w')
    t_str = "t-%s:%s\n"
    n_str = "n-%s:%s\n"
    l_str = "l-%s:%s\n"

    outfile2 = 'dates.txt'
    f2 = open(outfile2, 'w')
    d_str = "%s:%s\n"

    outfile3 = 'tweets.txt'
    f3 = open(outfile3, 'w')
    s_str = "%s:%s\n"

    # Scan through each tweet record stored in 'status' tags in xml format
    
    for status in root.iter('status'):
        id_num = status.findtext('id')       
        user = status.find('user')
        text = status.find('text')

        # -------------------------TASK-1-------------------------------
        # Get text terms
        t_terms = get_terms(text, 'text')
        for term in t_terms:
            f1.write(t_str % (term, id_num))

        # Get name terms
        name = user.find('name')
        n_terms = get_terms(name, 'name')      
        for term in n_terms:
            f1.write(n_str % (term, id_num))

        # Get location terms
        loc = user.find('location')
        l_terms = get_terms(loc, 'location')
        for term in l_terms:
            f1.write(l_str % (term, id_num))
	    	
        # -------------------------TASK-2-------------------------------
        date = status.findtext('created_at')
        f2.write(d_str % (date, id_num))

        # -------------------------TASK-3-------------------------------
        record = ET.tostring(status)
        record = record.decode('ascii').rstrip('\n')
        f3.write(s_str % (id_num, record))

    f1.close()
    f2.close()
    f3.close()


if __name__ == "__main__":
	main()