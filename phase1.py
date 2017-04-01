import sys
import re

"""
CMPUT291 Mini Project Phase 1: Preparing Data Files
"""

def get_text(string, tag):
    start = "<%s>" % tag
    end = "</%s>" % tag
    result = re.search('%s(.*)%s' % (start, end), string)
    if result:
        return result.group(1)
    else:
        return ""

def filter_len(term):
    """Ignore terms of length 2 or less

    :param term: string token
    """
    return len(term) > 2

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
    filtered_txt = re.sub(r'&#\d*;', '', string)
    tokens = filter_tokens(filtered_txt)
    return tokens

def write_out(filename, str_list):
    """Write data produced to the output file

    :param filename: name of the file to write to
    :param str_list: all data strings to be appended to file
    """
    for string in str_list:
        filename.write(string)
        

def main():
    
    # Get data file from command line arguments
    try:
        file_name = sys.argv[1]
    except IndexError:
        print("Error: No file added")
        sys.exit()
    except FileNotFoundError:
        print("Error: %s not found" % (file_name))
        sys.exit()

    # Get string records
    f = open(file_name, 'r')
    lines = f.read()
    records = lines.split('<status>')
    records[-1] = records[-1].replace('\n</statuses>', '')

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

    for status in records[1:]:
        id_num = get_text(status, "id")
        text = get_text(status, "text")
        # Scan through each tweet record stored in 'status' tags in xml format

        # Produce data for terms.txt
        # -------------------------------------------------------------

        # Get text terms
        t_terms = get_terms(text, 'text')
        for term in t_terms:
            file1_lines.append(t_str % (term, id_num))

        # Get name terms
        name = get_text(status, "name")
        n_terms = get_terms(name, 'name')      
        for term in n_terms:
            file1_lines.append(n_str % (term, id_num))

        # Get location terms
        loc = get_text(status, "location")
        l_terms = get_terms(loc, 'location')
        for term in l_terms:
            file1_lines.append(l_str % (term, id_num))

        # Produce data for dates.txt            
        # -------------------------------------------------------------
        date = get_text(status, "created_at")
        
        # Produce data for dates.txt	    	
        # -------------------------------------------------------------
        file2_lines.append(d_str % (date, id_num))

        # Produce data for tweets.txt
        # -------------------------------------------------------------

        record = ("<status>" + status).rstrip('\n')
        file3_lines.append(s_str % (id_num, record))

    # Remove newline from last element
    file1_lines[-1] = file1_lines[-1].rstrip('\n')
    file2_lines[-1] = file2_lines[-1].rstrip('\n')
    file3_lines[-1] = file3_lines[-1].rstrip('\n')

    # Write to output files
    write_out(f1, file1_lines)
    print(outfile1 + " created.")
    write_out(f2, file2_lines)
    print(outfile2 + " created.")
    write_out(f3, file3_lines)
    print(outfile3 + " created.")

    f1.close()
    f2.close()
    f3.close()


if __name__ == "__main__":
    main()
