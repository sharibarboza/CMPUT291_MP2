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

    # -------------------------TASK 1-------------------------------
    f1 = open(outfile1, 'w')
    for status in root.iter('status'):
        id_num = status.findtext('id')

        # Get text terms
        t_str = "t-%s:%s\n"
        text = status.find('text')
        t_terms = get_terms(text, 'text')

        for term in t_terms:
        	f1.write(t_str % (term, id_num))

        user = status.find('user')

        # Get name terms
        n_str = "n-%s:%s\n"
        name = user[0]
        n_terms = get_terms(name, 'name')
        
        for term in n_terms:
        	f1.write(n_str % (term, id_num))

        # Get location terms
        l_str = "l-%s:%s\n"
        loc = user[1]
        l_terms = get_terms(loc, 'location')

        for term in l_terms:
        	f1.write(l_str % (term, id_num))

    f1.close()
	    	
	    	
	    









    # -------------------------TASK 2-------------------------------












    # -------------------------TASK 3-------------------------------


if __name__ == "__main__":
	main()