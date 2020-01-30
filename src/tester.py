def detect_unrendered(line_list):
    """
    Function detect_unrendered goes through the lines of text, and depending on
    the number of unrendered lines (> 20%) The algorithm will not attempt to
    render the file.

    param: line_list: list containing the file's lines of text
    type: list(list(dict)) - pages(lines(dictionaries))
    return: the pergentage of undrendered lines
    rtype: integer  

    """
    wrong_counter = 0
    counter = 0
    for page in line_list:
        for line in page:
            for c in line['text']:
                if not c == " ":
                    if "\uFFFD" == c:
                        wrong_counter += 1
                    counter += 1
    if counter > 0:
        return wrong_counter/counter > .2
    return False
