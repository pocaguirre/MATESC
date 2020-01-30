import nltk


def is_title(string):
    tokens = nltk.word_tokenize(string)
    tagged = nltk.pos_tag(tokens)
    filtered = []
    if tagged[0][1] == 'CD':
        return True
    for t in tagged:
        if not(t[1] == 'IN' or t[1] == 'CC' or t[1] == 'DT' or t[1] == 'PDT'):
            filtered.append(t[0])
    for f in filtered:
        if (not f[0].isupper()) and f[0].isalpha():
            return False
    return True


def check_bold(span):
    """
    Check if the font type of the span is bold, if it has bold then return true

    :param span: span to test
    :type span: dict
    :return: True if bold, else False
    :rtype: bool
    """
    return span['font'][-1] == 'B' or span['font'][-4:] == "Bold" or span['font'] == 'AdvOTce3d9a73' or\
           span['font'] == 'AdvOTce3d9a73+fb'


def check_italic(span):
    """
    Check if the font type of the span is italic, if it is then return true

    :param span: span to test
    :type span: dict
    :return: True if italic, else False
    :rtype: bool
    """
    return span['font'][-1] == 'I' or span['font'][-6:] == "Italic"


def contains(long_str, word_list):
    """
    Check if a list of words is on a string

    :param long_str: string to be checked
    :type long_str: str
    :param word_list: list of strings to be checked
    :type word_list: list(str)
    :return: True if long_str contains any of the words, else false
    """
    for word in word_list:
        if contains_word(long_str, word):
            return True
    return False


def contains_word(long_str, word):
    """
    Check if a long string contains exactly the word

    :param long_str: string to be checked
    :type long_str: str
    :param word: word to be searched for
    :type word: str
    :return: True if the long string contains the word, else False
    :rtype: bool
    """
    str_list = long_str.replace(":", " ").replace(".", " ").replace("/", " ").split(" ")
    for w in str_list:
        if w.lower() == word or w.lower() == word + "s":
            return True
    return False


def test_long_subs(string):
    """
    Meant to be used to test if section title contain more than 3 digits.

    :param string: title section to test (could be any string)
    :type string: str
    :return: True if it contains more than 3 digits, else False
    :rtype: bool
    """
    return sum(x.isdigit() for x in string) > 3


def get_font_type(span):
    """
    Extract font type from given span

    :param span: span to be processed
    :type span: dict
    :return: font type of the span
    :rtype: str
    """
    return span['font']


def get_font_size(span):
    """
    Extract font size from given span. Font size is rounded nearest digit.

    :param span: span to be processed
    :type span: dict
    :return: font size
    :rtype: float
    """
    return round(float(span['size']))


def test_fonts(element, font_dict):
    """
    Check whether element's font size and type is in the dictionary of font types and sizes.
    If the font size or type are not given then return False

    :param element: element to be checked
    :type element: dict
    :param font_dict: dictionary of font sizes and types
    :type font_dict: dict
    :return: True if element's font is in both lists, else False
    :rtype: bool
    """
    if font_dict:
        if get_font_type(element) in font_dict.keys():
            if get_font_size(element) in font_dict[get_font_type(element)]:
                return False
        return True
    else:
        return False


def test_figures(text):
    """
    Check whether the text given contains any of the list_words constants

    :param text: text to be tested
    :type text: str
    :return: True if text contains any of the words, else False
    :rtype: bool
    """
    list_words = ["figure", 'fig', 'scheme']
    return contains(text, list_words)


def check_same_line(span1, span2):
    """
    Check whether spans given belong to the same line. They pass the test if:
    - they are subscripts and the space between where span1 ends and span2 begins
    is less than 10
    - OR if the top y-coordinate is the same
    - OR if the bottom y-coordinate is the same

    :param span1: first span
    :type span1: dict
    :param span2: second span
    :type span2: dict
    :return: True if it passes the test, else False
    :rtype: bool
    """
    is_line, t = check_subscripts(span1, span2)
    return (is_line or (abs(span1["bbox"][2] - span2["bbox"][0]) < 10 and
                         round(float(span1['size'])) == round(float(span2['size'])))), t


def check_subscripts(line1, line2):
    """
    Check whether line1 and line2 have a subscript or superscript relationship between
    each other. (order doesn't matter)

    + means superscript
    - means subscript

    1 first span
    2 second span

    :param line1: first line
    :type line1: dict
    :param line2: second line
    :type line2: dict
    :return: True if vertically a line begins or ends in between the other line, else False
    :rtype: bool
    """
    if line1['bbox'][3] - line2['bbox'][1] < 0.15:
        return False, None
    #if round(float(line1['size'])) == round(float(line2['size'])):
        #return False, None
    if line1["bbox"][1] <= line2["bbox"][1] <= line1["bbox"][3] and line1['size'] - line2['size'] > 1:
        return True, "2-"
    elif line1["bbox"][1] <= line2["bbox"][3] <= line1["bbox"][3] and line1['size'] - line2['size'] > 1:
        return True, "2+"
    elif line2["bbox"][1] <= line1["bbox"][1] <= line2["bbox"][3] and line2['size'] - line1['size'] > 1:
        return True, "1-"
    elif line2["bbox"][1] <= line1["bbox"][3] <= line2["bbox"][3] and line2['size'] - line1['size'] > 1:
        return True, "1+"
    else:
        return False, None


def fix_spaces(span):
    """
    Fix spaces in the text of a span. Sometimes some spans have extra spaces

    :param span: span to be fixed
    :type span: dict
    :return: new span with fixed text
    :rtype: dict
    """
    original_text = span['text']
    new_text = original_text.replace("    ", " ").replace("   ", ' ').replace("  ", " ").strip(" ")
    span['text'] = new_text
    return span


def compare_font(line1, line2):
    """
    Check whether line1 has exactly the same font type and size of
    line2.

    :param line1: first line
    :type line1: dict
    :param line2: second line
    :type line2: dict
    :return: True if the font size and type are the same, else False
    :rtype: bool
    """
    font1 = get_font_size(line1)
    font2 = get_font_size(line2)
    font_type1 = get_font_type(line1)
    font_type2 = get_font_type(line2)
    if len(font_type1) - len(font_type2) == 3:
        font_type1 = font_type1[:-3]
    elif len(font_type2) - len(font_type1) == 3:
        font_type2 = font_type2[:-3]
    return font1 == font2 and font_type1 == font_type2


def calculate_spacing(line1, line2):
    """
    Calculates the spacing between the lines by taking the top y coordinate of
    line2 and the bottom from line1

    :param line1: line that is in the top
    :type line1: dict
    :param line2: line that is on the bottom
    :type line2: dict
    :return: spacing between the lines
    :rtype: float
    """
    return round(line2["bbox"][1] - line1["bbox"][3])


def get_biggest_y(group):
    """
    Given a group, find the lowest group in position (biggest y coordinate) by looping through the group

    :param group: group to be processed
    :type group: list(dict)
    :return: biggest y coordinate in the group
    :rtype: float
    """
    biggest = 0
    for line in group:
        if line["bbox"][3] > biggest:
            biggest = line["bbox"][3]
    return biggest


def find_font_in_group(group):
    """
    Given a group of lines, find the font type that the group should have if the lines
    were to be merged. We do this by making a dictionary of the font and appearances.

    {"font_type1": 3, "font_type2: 1, "font_type3": 5}

    :param group: group to be processed
    :type group: list(dict)
    :return: font type that happens the most in the group
    :rtype: str
    """
    font_type_dict = {}
    for line in group:
        if get_font_type(line) in font_type_dict.keys():
            font_type_dict[get_font_type(line)] += 1
        else:
            font_type_dict[get_font_type(line)] = 1
    font_type_number = ["", 0]
    for key in font_type_dict:
        if font_type_dict["{}".format(key)] > font_type_number[1]:
            font_type_number[0] = key
            font_type_number[1] = font_type_dict["{}".format(key)]
    return font_type_number[0]


def find_font_size_in_group(group):
    """
    Given a group of lines, find the font size that the group should have if the lines
    were to be merged. We do this by making a dictionary of the font and appearances.

    {"font_size1": 3, "font_size2: 1, "font_size3": 5}

    :param group: group to be processed
    :type group: list(dict)
    :return: font size that happens the most in the group
    :rtype: str
    """
    font_type_dict = {}
    for line in group:
        if str(get_font_size(line)) in font_type_dict.keys():
            font_type_dict[str(get_font_size(line))] += 1
        else:
            font_type_dict[str(get_font_size(line))] = 1
    font_type_number = ["", 0]
    for key in font_type_dict:
        if font_type_dict["{}".format(key)] > font_type_number[1]:
            font_type_number[0] = key
            font_type_number[1] = font_type_dict["{}".format(key)]
    return font_type_number[0]


def find_title_on_second_page(sorted_list, title):
    """
    Given a document and the presumed title, try to find the title in second page
    if found then true, else False. ( this is done because of cover pages )

    :param sorted_list: document to be processed
    :type sorted_list: list(list(dict))
    :param title: Title found in first page
    :type title: dict
    :return: True if title found in second page, else False
    :rtype: bool
    """
    if len(sorted_list) > 0:
        second_page = sorted_list[1]
        title_text = ""
        for line in title['lines']:
            title_text = add_string(title_text, line['text'])
        for group in second_page:
            text = ""
            for line in group['lines']:
                text = add_string(text, line['text'])
            if text.replace(' ', '') == title_text.replace(' ', ''):
                return True
    return False


def find_intro_in_subs(final_subs):
    """
    Check if we have found introduction in the title sections

    :param final_subs: list of title sections
    :type final_subs: list(str)
    :return: True if 'introduction' is found in the title sections, else False
    """
    for sub in final_subs:
        if contains_word(sub, 'introduction'):
            return True
    return False


def prove_author(text, ignore):
    """
    Given a text and a list of words to ignore check that the text is fit
    to be a list of authors. It is fit if: it doesn't contain any of the
    ignore words, if the text is not a digit, if length of the text is
    greater than 1, if its not all numbers, if its not just spaces, or
    if its not all numbers.

    :param text: text tested for authors
    :type text: str
    :param ignore: list of words to ignore
    :type ignore: list(str)
    :return: True if it passes the test, else False
    """
    return (not contains(text, ignore)) and (not text.isdigit()) and len(text) > 1 and (not all_numbers(text)) and\
           (not just_spaces(text)) and not all_numbers(text)


def just_spaces(str):
    """
    Given a string check if the string only contains spaces

    :param str: string to test
    :type str: str
    :return: True if it only contains spaces, False if it contains any other character
    :rtype: bool
    """
    if len(str) == 1:
        return False
    for char in str:
        if char != " ":
            return False
    return True


def all_numbers(text):
    """
    Check if a string is a series number given by "####-####"

    :param text: text to be checked
    :type text: str
    :return: True if its a series of number, else False
    :rtype: bool
    """
    text = text.replace(" ", "")
    parts = text.split("-")
    if len(parts) == 1:
        parts = parts[0].split("-")
    all_number = False
    counter = 0
    for i in range(len(parts)):
        if parts[i].isdigit():
            counter += 1
    if counter == len(parts):
        all_number=True
    if len(parts) > 1 and all_number:
        return True
    return False


def get_bbox_length(bbox):
    """
    Given a bounding box in the form of [x1, y1, x2, y2] find the horizontal
    length of the bounding box

    :param bbox: bounding box in specified form
    :type bbox: list(float)
    :return: horizontal length of bounding box
    :rtype: float
    """
    return bbox[2] - bbox[0]


def check_subs(group, sub_list):
    """
    Check if a group is a section title.

    :param group: group to be checked
    :type group: dict
    :param sub_list: list of section titles
    :type sub_list: list(str)
    :return: True if group is a section title, else False
    :rtype: bool
    """
    text = ""
    for i in range(min([2, len(group['lines'])])):
        text += group['lines'][i]['text'].strip("") + " "
    words = text.strip(" ").split()
    ft = ""
    for w in words:
        if w != "":
            ft += w

    for sub in sub_list:
        s = sub.strip(' ').split()
        fs = ""
        for w in s:
            if w != "":
                fs += w
        if ft == fs:
            return True
    return False


def string_has_characters(s):
    """
    Check if a string has 5 or more characters other than spaces

    :param s: string to test
    :type s: str
    :return: True if string has more than 5 characters, else False
    :rtype: bool
    """
    return len(s.replace(" ", "")) > 5


def check_inline_subs(span1, span2):
    """
    Checking for in line section titles. The way we do this is by checking if there
    is a change in span font type from any to bold and that both spans lengths are greater
    than 2.

    :param span1: first span
    :type span1: dict
    :param span2: second span
    :type span2: dict
    :return: True if its inline subtitle, else False
    """
    return ((check_bold(span1) and not check_bold(span2)) or (check_bold(span2) and not check_bold(span1))) and\
           (len(span1['text']) > 2 and len(span2['text']) > 2)


def delete_repeats(sub_list):
    new_subs = []
    for i in range(len(sub_list)):
        repeated = False
        for j in range(len(sub_list)):
            if not i == j:
                if sub_list[i] == sub_list[j]:
                    repeated = True
        if not repeated:
            new_subs.append(sub_list[i])
    return new_subs


def add_string(string1, string2):
    if string2 == "" or string2 is None:
        return string1
    elif string1 == "" or string1 is None:
        return string2
    try:
        if string1[-1] == " " or string2[0] == " ":
            string1 += string2
        else:
            string1 += " " + string2
    except KeyError:
        print(string1)
    return string1


def get_text_from_group(group):
    text = ''
    for line in group['lines']:
        text += add_string(text, line['text'])
    return text
