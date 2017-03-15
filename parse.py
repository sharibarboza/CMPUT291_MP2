import sys
import re
import xml.etree.ElementTree as ET

"""
CMPUT291 Mini Project Phase 1: Preparing Data Files
"""

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
    return string.replace('"', "&quot;")	

def filter_len(term):
    """Ignore terms of length 2 or less

    :param term: string token
    """
    return len(term) > 2

def filter_string(string):
    """Remove unwanted characters from string text

    :param string: tag + text
    """
    string = convert_quote(string)
    return re.sub(r'&#\d*;', '', string)

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
    raw_txt = strip_text(ET.tostring(string, method='html'), tag)
    filtered_txt = filter_string(raw_txt)
    tokens = filter_tokens(filtered_txt)
    return tokens

def write_out(filename, str_list):
    """Write data produced to the output file

    :param filename: name of the file to write to
    :param str_list: all data strings to be appended to file
    """
    for string in str_list:
        filename.write(string)

#--------------------------------MAIN-----------------------------------

def main():
    
    # Get data file from command line arguments
    try:
        file_name = sys.argv[1]
        tree = ET.parse(file_name)
    except xml.etree.ElementTree.ParseError:
        print("Error: Failed to parse file.")
        sys.exit()
    except IndexError:
        print("Error: No file added")
        sys.exit()
    except FileNotFoundError:
        print("Error: %s not found" % (file_name))
        sys.exit()

    root = tree.getroot()

    # Prepare output files and strings
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

    file1_lines = []
    file2_lines = []
    file3_lines = []

    # Scan through each tweet record stored in 'status' tags in xml format

    for status in root.iter('status'):
        id_num = status.findtext('id')       
        user = status.find('user')
        text = status.find('text')

        # Produce data for terms.txt
        # -------------------------------------------------------------

        # Get text terms
        t_terms = get_terms(text, 'text')
        for term in t_terms:
            file1_lines.append(t_str % (term, id_num))

        # Get name terms
        name = user.find('name')
        n_terms = get_terms(name, 'name')      
        for term in n_terms:
            file1_lines.append(n_str % (term, id_num))

        # Get location terms
        loc = user.find('location')
        l_terms = get_terms(loc, 'location')
        for term in l_terms:
            file1_lines.append(l_str % (term, id_num))

        # Produce data for dates.txt	    	
        # -------------------------------------------------------------

        date = status.findtext('created_at')
        file2_lines.append(d_str % (date, id_num))

        # Produce data for tweets.txt
        # -------------------------------------------------------------

        record = ET.tostring(status, method='html')
        record = record.decode('ascii').rstrip('\n')
        record = convert_quote(record)
        file3_lines.append(s_str % (id_num, record))


    # Remove newline from last element
    file1_lines[-1] = file1_lines[-1].rstrip('\n')
    file2_lines[-1] = file2_lines[-1].rstrip('\n')
    file3_lines[-1] = file3_lines[-1].rstrip('\n')

    # Write to output files
    write_out(f1, file1_lines)
    write_out(f2, file2_lines)
    write_out(f3, file3_lines)

    f1.close()
    f2.close()
    f3.close()


if __name__ == "__main__":
    main()