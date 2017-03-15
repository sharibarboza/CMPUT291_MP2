import re
import html
import xml.etree.ElementTree as ET

tree = ET.parse('data.txt')
root = tree.getroot()


def strip_text(string, tag):
    opening = "<%s>" % (tag)
    closing = "</%s" % (tag)
    string = string.decode('ascii')
    string = string.replace(opening, '').replace(closing, '')
    return string

def convert_quote(string):
    return string.replace('"', " &quot ")	

def filter_len(term):
    return len(term) > 2

def filter_html(term):
    return False if '&#' in term else True

def filter_string(string):
    string = convert_quote(string)
    tokens = ' '.join(re.split(';', string))
    string = tokens.replace(',', '')
    tokens = string.split()
    tokens = list(filter(filter_html, tokens))
    return ' '.join(tokens)

def filter_tokens(string):
    tokens = re.split('[\W_]', string)
    tokens = list(filter(filter_len, tokens))
    return [token.lower() for token in tokens]

def get_terms(string, tag):
    raw_txt = strip_text(ET.tostring(string), tag)
    filtered_txt = filter_string(raw_txt)
    return filter_tokens(filtered_txt)


#------------------------------MAIN---------------------------------

def main():
    outfile1 = 'terms.txt'
    outfile2 = 'dates.txt'
    outfile3 = 'tweets.txt'

    f1 = open(outfile1, 'w')
    f2 = open(outfile2, 'w')
    f3 = open(outfile3, 'w')

    t_str = "t-%s:%s\n"
    n_str = "n-%s:%s\n"
    l_str = "l-%s:%s\n"

    for status in root.iter('status'):
        id_num = status.findtext('id')       
        user = status.find('user')
        text = status.find('text')

    # -------------------------TASK 1-------------------------------
        # Get text terms
        t_terms = get_terms(text, 'text')
        for term in t_terms:
            f1.write(t_str % (term, id_num))

        # Get name terms
        name = user[0]
        n_terms = get_terms(name, 'name')      
        for term in n_terms:
            f1.write(n_str % (term, id_num))

        # Get location terms
        loc = user[1]
        l_terms = get_terms(loc, 'location')
        for term in l_terms:
            f1.write(l_str % (term, id_num))
	    	
    # -------------------------TASK 2-------------------------------
        date_str = "%s:%s\n"
        date = status.findtext('created_at')
        f2.write(date_str % (date, id_num))

    # -------------------------TASK 3-------------------------------
        stat_str = "%s:%s\n"
        record = ET.tostring(status)
        record = record.decode('ascii').rstrip('\n')
        f3.write(stat_str % (id_num, record))

    f1.close()
    f2.close()
    f3.close()


if __name__ == "__main__":
	main()