import fitz
import os
import json


def file_list(root, recursive=True, file_types=['.pdf']):
    """
    Given a path to a directory, return a list of absolute paths to all
    of the files found within.

    :param root: An absolute or relative path to a directory
    :type root: str
    :param recursive: Whether to search the given directory recursively
    :type recursive: bool
    :return: A list of absolute paths to all files contained within
        the given directory and all of its subdirectories
    :rtype: list(str)
    """
    if os.path.isfile(root):
        return [os.path.abspath(root)]

    fpaths = []

    for abs_path, dirs, fnames in os.walk(root):
        abs_path = os.path.abspath(abs_path)
        fpaths.extend(map(lambda x: os.path.join(abs_path, x),
                          filter(lambda name: os.path.splitext(name)[1] in file_types, fnames)))

        if not recursive:
            break

    return fpaths


def select_title(ordered_list, gazetteer_list, ignore_list, index=0, title_continued=False):
    """
    Given an index and a list of blocks, it loops through lines and spans of the specified block to
    find the first line of the title according to specifications: The first line should be more than
    25 characters long, or it should contain a word from the gazetteer list and the X coordinate
    of its bounding box should be less than 300.

    :param ordered_list: List of ordered blocks (ordered by font size)
    :type ordered_list: json file
    :param gazetteer_list: list of words that are relevant
    :type gazetteer_list: list(str)
    :param ignore_list: list of words that shouldn't be on the title
    :type ignore_list: list(str
    :param index: the index number of the block to be looped through
    :type index: int
    :param title_continued: True if there is a title line already and the function was recursively called
    :type title_continued: bool
    :return: A string that contains the title of the document
    :rtype: str
    """
    title = ""
    span_text = ""
    bbox = []
    previous_length = 0
    count_repeated_title = 0
    for line in ordered_list[index]["lines"]:
        for span in line["spans"]:
            if span_text != span["text"]:
                span_text = ""
                #print(span["text"])
                #print(get_font_brom_bbox(span["bbox"]))
                #if bbox:
                    #print(get_font_brom_bbox(bbox))
                if (not title) and (group_spans(line["spans"], title_continued) or
                        contains(span["text"], gazetteer_list)) and span["bbox"][0] < 300:
                    span_text += span["text"]
                    bbox = span["bbox"]
                elif title and (get_font_brom_bbox(span["bbox"]) == get_font_brom_bbox(bbox) or
                                    contains(span["text"], gazetteer_list)) or\
                        contains_word(span["text"], "and") or contains_word(span["text"], "via") or\
                        contains_word(span["text"], "conductive"):
                    span_text += span["text"]
                    bbox = span["bbox"]
                if just_spaces(span["text"]) and title:
                    return title
                if (contains(span_text, ignore_list) or
                        contain_period(span_text)):
                    if title:
                        return title
                    span_text = ""
                    break
                title += span_text

            else:
                if span["bbox"] != bbox:
                    span_text = ""
                break

        #print(title)
        if previous_length == len(title) and not just_spaces(title):
            count_repeated_title += 1
        else:
            previous_length = len(title)
        if count_repeated_title > 6:
            break
        # end of for loop spans
    #print(title)
    # end of for loop lines
    if len(title) < 25 and not title_continued and not contains(title, gazetteer_list):
        if index < len(ordered_list) -1:
            return select_title(ordered_list, gazetteer_list, ignore_list, index+1)
    else:
        current_font = int(ordered_list[index]["bbox"][3] - ordered_list[index]["bbox"][1])
        try:
            next_font = int(ordered_list[index+1]["bbox"][3] - ordered_list[index+1]["bbox"][1])
        except:
            next_font = 0
        if current_font == next_font:
            if index < len(ordered_list) - 1:
                return title + ' ' + select_title(ordered_list, gazetteer_list, ignore_list, index + 1, True)
        return title


def get_font_brom_bbox(bbox):
    """
    Given a bounding box subtract their Y values to get the font size

    :param bbox: Bounding box given by [bottom left X value, bottom left Y value, top right X value
                    top right Y value]
    :type bbox: list(int)
    :return: font size given by bbox
    :rtype: int
    """
    return int(bbox[3] - bbox[1])


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


def group_spans(spans, flag):
    """
    Check if the title is distributed through many spans. If so get the text
    from all the spans and check if the length is greater than 25 characters
    else still check if the line is 25 characters unless the flag is True

    :param spans: list of spans that contain possible title
    :type spans: list of dictionaries containing the bbox and the text
    :param flag: False if you want to check for length in title
    :type flag: bool
    :return: False if the title is less than 25 characters, or True if the title is greater than 25
    """
    span = spans[0]
    text1 = span["text"]
    font_span = get_font_brom_bbox(span["bbox"])
    for span in spans[1:]:
        if not font_span == get_font_brom_bbox(span["bbox"]) and (flag or len(text1) < 25):
            if check_subscripts(spans):
                text1 += span["text"]
            else:
                return False
        else:
            text1 += span["text"]
    return len(text1) > 25 or flag


def check_subscripts(spans):
    """
    Check if there are subscripts in the group of spans

    :param spans: list of spans
    :type spans: list of dictionaries containing the bbox and the text
    :return: False if the text doesn't contain a subscript, True if it does
    :rtype: bool
    """
    for i in range(len(spans)):
        try:
            second = spans[i + 1]
            third = spans[i + 2]
            if get_font_brom_bbox(spans[i]["bbox"]) == get_font_brom_bbox(third["bbox"]):
                i += 3
                if len(second["text"]) < 7 and len(second["text"]):
                    return True
        except:
            return False
    return False


def contain_period(str):
    """
    Check if the string contains a period

    :param str: string to be checked
    :type str: str
    :return: True if there is a period else false
    :rtype: bool
    """
    if len(str) > 2:
        for i in range(1, len(str) - 1):
            if str[i] == "." and not (str[i-1].isdigit() or str[i+1].isdigit()):
                return True
            i += 1
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
    str_list = long_str.replace(":", " ").split(" ")
    for w in str_list:
        if w.lower() == word or w.lower() == word + "s":
            return True
    return False


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


def get_font(ordered_list, index):
    """
    Get the font of the first span of the first line of the block specified given a list of blocks
    and the index of the block desired

    :param ordered_list: list of blocks
    :type ordered_list: list of dictionaries containing lines and spans that contain bbox and text
    :param index: index of the block desired in the list
    :type index: int
    :return: size of the font of that block
    :rtype: int
    """
    font = int(ordered_list[index]["lines"][0]["spans"][0]["bbox"][3] -
               ordered_list[index]["lines"][0]["spans"][0]["bbox"][1])
    return font


def order_list(normal_list):
    """
    Order a list by font size

    :param normal_list: list of blocks
    :type normal_list: list of dictionaries containing lines and spans that contain bbox and text
    :return: ordered list of blocks by font size
    :rtype: list of dictionaries containing lines and spans that contain bbox and text
    """
    new_list = sorted(normal_list, key=lambda block: block["lines"][0]["spans"][0]["bbox"][3] -
                                                     block["lines"][0]["spans"][0]["bbox"][1], reverse=True)
    for i in range(len(new_list) - 1):
        this_term = new_list[i]["lines"][0]["spans"][0]["bbox"][1]
        next_term = new_list[i+1]["lines"][0]["spans"][0]["bbox"][1]
        if get_font(new_list, i) == get_font(new_list, i+1):
            if this_term > next_term:
                temp = new_list[i]
                new_list[i] = new_list[i+1]
                new_list[i+1] = temp
    return new_list


def order_by_location(normal_list):
    """
    Order a list of blocks by y-coordinates and then by x_coordinates

    :param normal_list: list of blocks
    :type normal_list: list of dictionaries containing lines and spans that contain bbox and text
    :return: ordered list of blocks by location
    :rtype: list of dictionaries containing lines and spans that contain bbox and text
    """
    new_list = sorted(normal_list, key=lambda block: (block["lines"][0]["spans"][0]["bbox"][1],
                                                      block["lines"][0]["spans"][0]["bbox"][0]))
    return new_list


def authors_location(list_blocks, title, ignore):
    """
    given a list of blocks, the title of the document and a list of words to ignore,
    loop through the lines and spans of the list of blocks until the title is found.
    Then return the coordinates of the next available span that doesn't contain the
    words in the ignore list.

    :param list_blocks: list of blocks to look for author
    :type list_blocks: list of dictionaries containing lines and spans that contain bbox and text
    :param title: the title extracted from the list of blocks
    :type title: str
    :param ignore: list of words to ignore
    :type ignore: list(str)
    :return: coordinates of the next available span if it doesn't contain the words in ignore list
    :rtype: list(block index, line index, span index)
    """
    keep_looking = False
    for block in range(len(list_blocks)):
        for line in range(len(list_blocks[block]["lines"])):
            for span in range(len(list_blocks[block]["lines"][line]["spans"])):
                contains_title = list_blocks[block]["lines"][line]["spans"][span]["text"].find(title[-7:])
                #print(title[-7:])
                if contains_title > -1 or keep_looking:
                    #print(list_blocks[block]["lines"][line]["spans"][span]["text"])
                    keep_looking = True
                    if span == len(list_blocks[block]["lines"][line]["spans"]) -1:
                        if line == len(list_blocks[block]["lines"]) - 1:
                            if prove_first_line(list_blocks[block+1]["lines"][0]["spans"][0]["text"], ignore):
                                return [block+1, 0, 0]
                        elif prove_first_line(list_blocks[block]["lines"][line + 1]["spans"][0]["text"], ignore):
                            return [block, line + 1, 0]
                    elif prove_first_line(list_blocks[block]["lines"][line]["spans"][span + 1]["text"], ignore):
                        return [block, line, span + 1]
    return "Can't find authors"


def find_next(list_blocks, bbox, ignore):
    """
    given a list of blocks, the bounding box of the title of the document and a list
    of words to ignore, loop through the lines and spans of the list of blocks until
    the matching bbox of the title is found. Then return the coordinates of the next
    available span that doesn't contain the words in the ignore list.

    :param list_blocks: list of blocks to look for author
    :type list_blocks: list of dictionaries containing lines and spans that contain bbox and text
    :param bbox: bounding box of the title
    :type bbox: list(bottom left X, bottom left Y, top right X, top right Y)
    :param ignore: list of words to ignore
    :type ignore: list(str)
    :return: coordinates of the next available span if it doesn't contain the words in ignore list
    :rtype: list(block index, line index, span index)
    """
    #print("here next")
    keep_looking = False
    for block in range(len(list_blocks)):
        for line in range(len(list_blocks[block]["lines"])):
            for span in range(len(list_blocks[block]["lines"][line]["spans"])):
                equal_bbox = list_blocks[block]["lines"][line]["spans"][span]["bbox"]
                #print(list_blocks[block]["lines"][line]["spans"][span]["bbox"])
                if bbox == equal_bbox or keep_looking:
                    # print(list_blocks[block]["lines"][line]["spans"][span]["text"])
                    keep_looking = True
                    if span == len(list_blocks[block]["lines"][line]["spans"]) - 1:
                        if line == len(list_blocks[block]["lines"]) - 1:
                            if prove_first_line(list_blocks[block + 1]["lines"][0]["spans"][0]["text"], ignore):
                                return [block + 1, 0, 0]
                        elif prove_first_line(list_blocks[block]["lines"][line + 1]["spans"][0]["text"], ignore):
                            return [block, line + 1, 0]
                    elif prove_first_line(list_blocks[block]["lines"][line]["spans"][span + 1]["text"], ignore):
                        return [block, line, span + 1]
    return "Can't find authors"


def prove_first_line(text, ignore_list):
    """
    given string check if the string does not contain any words from the ignore list,
    if the string is not only digits, if the string is not null, if the string is
    just spaces, or if the string is a series number

    :param text: text to be checked
    :type text: str
    :param ignore_list: list of words to be ignored
    :type ignore_list: list(str)
    :return: True if: text does not contain any of the ignore list, text is not a digit,
                        text is not null, text is not a series number, text is not spaces,
                        else False
    :rtype: bool
    """
    if not contains(text, ignore_list) and not text.isdigit() and len(text) > 1 and not all_numbers(text) and\
            not just_spaces(text):
        #print(text)
        return True
    return False


def all_numbers(text):
    """
    Check if a string is a series number given by "####-####"

    :param text: text to be checked
    :type text: str
    :return: True if its a series of number, else False
    """
    parts = text.split("-")
    if len(parts) == 1:
        parts = parts[0].split("–")
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


def get_first_author_span(list_blocks, location):
    """
    Given a list of blocks and the coordinates of a span, get the text and the
    font of given span.

    :param list_blocks: list of blocks
    :type list_blocks: list of dictionaries containing lines and spans that contain bbox and text
    :param location: coordinates of the span to be extracted
    :type location: list(index of block, index of list, index of span)
    :return: list containing the text and the font of given span
    :rtype: list(str, int)
    """
    return [list_blocks[location[0]]["lines"][location[1]]["spans"][location[2]]["text"],
            get_font_brom_bbox(list_blocks[location[0]]["lines"][location[1]]["spans"][location[2]]["bbox"])]


def compare_without_spaces(text1, text2):
    """
    Given two strings, delete the spaces and compare them

    :param text1: string1
    :type text1: str
    :param text2: string2
    :type text2: str
    :return: True if they are equal, else False
    :rtype: bool
    """
    text1_spaceless = ""
    text2_spaceless = ""
    for char in text1:
        if char and char != " ":
            text1_spaceless += char
    for char in text2:
        if char and char != " ":
            text2_spaceless += char
    return text1_spaceless == text2_spaceless


def select_authors(list_blocks, title, ignore, coordinates=None):
    """
    Given a list of blocks, the title, a list of words to ignore, if coordinates were not given
    search for the title in the list of blocks and get the coordinates of the span where authors
    begin. Then extract the text and font of span given the coordinates. Then starting at the
    position at the next available span, loop through the rest of the line and get the text
    until the font changes, then go to the next line and get the text until font changes, then
    if the authors is still less than 10 characters, then go to the next block and loop through
    its lines and spans until the font changes.

    :param list_blocks: list of blocks
    :type list_blocks: list of dictionaries containing lines and spans that contain bbox and text
    :param title: title of the document extracted from the list
    :type title: str
    :param ignore: list of words to ignore before the authors
    :type ignore: list(str)
    :param coordinates: list of ints representing the coordinate of the title
    :type coordinates: list(block index, line index, span index)
    :return: string containing a list of authors
    :rtype: str
    """
    bbox = coordinates
    if bbox:
        location = find_next(list_blocks, bbox, ignore)
    else:
        location = authors_location(list_blocks, title, ignore)
    #print(location)
    if isinstance(location, str):
        return location
    first_span = get_first_author_span(list_blocks, location)
    authors = first_span[0]
    #print(authors)
    authors_font = first_span[1]
    try:
        for s in range(location[2] + 1, len(list_blocks[location[0]]["lines"][location[1]]["spans"])):
            if get_font_brom_bbox(list_blocks[location[0]]["lines"][location[1]]["spans"][s]["bbox"]) == authors_font or\
                    check_subscripts(list_blocks[location[0]]["lines"][location[1]]["spans"]):
                #print("adding ____" + list_blocks[location[0]]["lines"][location[1]]["spans"][s]["text"])
                authors += list_blocks[location[0]]["lines"][location[1]]["spans"][s]["text"]
                bbox = list_blocks[location[0]]["lines"][location[1]]["spans"][s]["bbox"]
            else:
                if compare_without_spaces(title, authors):
                    return select_authors(list_blocks, title, ignore, bbox)
                return authors
        #print("first time ______ " + authors)
        for line in range(location[1]+1, len(list_blocks[location[0]]["lines"])):
            for span in range(len(list_blocks[location[0]]["lines"][line]["spans"])):
                #print(authors)
                #print(authors_font)
                #print(get_font_brom_bbox(list_blocks[location[0]]["lines"][line]["spans"][span]["bbox"]))
                if get_font_brom_bbox(
                        list_blocks[location[0]]["lines"][line]["spans"][span]["bbox"]) == authors_font or \
                        check_subscripts(list_blocks[location[0]]["lines"][line]["spans"]) or\
                        contains_word(list_blocks[location[0]]["lines"][line]["spans"][span]["text"], "and"):
                    #print("adding here ______" + list_blocks[location[0]]["lines"][line]["spans"][span]["text"])
                    authors += list_blocks[location[0]]["lines"][line]["spans"][span]["text"]
                    bbox = list_blocks[location[0]]["lines"][line]["spans"][span]["bbox"]
                else:
                    if compare_without_spaces(title, authors):
                        return select_authors(list_blocks, title, ignore, bbox)
                    #print(authors)
                    return authors
        #print("second time _____ " + authors)
        if len(authors) < 10:
            for block in range(location[0]+1, len(list_blocks)):
                for line in range(len(list_blocks[block]["lines"])):
                    for span in range(len(list_blocks[block]["lines"][line]["spans"])):
                        #print(list_blocks[block]["lines"][line]["spans"][span])
                        if get_font_brom_bbox(
                                list_blocks[block]["lines"][line]["spans"][span]["bbox"]) == authors_font or \
                                check_subscripts(list_blocks[block]["lines"][line]["spans"]):
                            # print("adding here ______" + list_blocks[block]["lines"][line]["spans"][span]["text"])
                            authors += list_blocks[block]["lines"][line]["spans"][span]["text"]
                            bbox = list_blocks[block]["lines"][line]["spans"][span]["bbox"]
                        else:
                            # print(authors)
                            if compare_without_spaces(title, authors):
                                return select_authors(list_blocks, title, ignore, bbox)
                            return authors
        if compare_without_spaces(title, authors):
            return select_authors(list_blocks, title, ignore, bbox)
        return authors
    except:
        return "no authors found"


def make_gazetteer_list():
    """
    Create a list of strings that contains the words of the text file "gazetteer.txt"

    :return: the list of words inside gazetteer.txt
    :rtype: list(str)
    """
    document = open("gazetteer.txt", "r")
    words = document.readlines()
    for i in range(len(words)):
        words[i] = words[i][:-1]
    return words


def clean_title(title):
    """
    delete any spaces at the end of string

    :param title: string to be modified
    :type title: str
    :return: clean title or same if title was already cleaned
    :rtype: str
    """
    if title[-1] == " ":
        title = title[:-1]
        return clean_title(title)
    else:
        return title

def main(debug):
    document_list = file_list("input")
    gazetteer = make_gazetteer_list()
    ignore_list = ["author", "copyright", "journal", "published", "downloaded", "article", "licensed", "download",
                   "available", "doi", "ip", "please", "institute", "university", "laboratory", "department", "letters"]
    ignore_authors = ["communication", "vol.", "no.", "cite", "published", "licensed", "article", "factor",
                      "citation", "institute", "paper", "mechanistic"]
    counter = 0
    for file in document_list:
        # if counter > 5:
        #     break
        doc = fitz.Document(file)
        page = doc.loadPage(0)
        page_json = json.loads(page.getText(output="json"))
        ordered_by_font = order_list(page_json["blocks"]) # sorted(page_json["blocks"], key=lambda block: block["lines"][0]["spans"][0]["bbox"][3] - block["lines"][0]["spans"][0]["bbox"][1], reverse=True)
        new_order = order_by_location(page_json["blocks"])
        if debug:
            """
            for thing in page_json["blocks"]:
                print("block:")
                for line in thing["lines"]:
                    print("\tline:")
                    for span in line["spans"]:
                        print("\t\t"+str(span))
            """
            print("----------------------------------------------------------------------------")
            for block in new_order:
                print("block:")
                for line in block["lines"]:
                    print("\tline:")
                    for span in line["spans"]:
                        print("\t\t" + str(span))
        """
        title = ""
        for line in ordered_by_font[0]["lines"]:
            for span in line["spans"]:
                title += span["text"] + "\n"
        counter +=1
        """
        counter += 1
        title = select_title(ordered_by_font, gazetteer, ignore_list)
        title = clean_title(title)
        print(str(counter) + ".\n" + "TITLE:\n\t" + title)
        authors = select_authors(new_order, title, ignore_authors)
        print("AUTHORS:\n\t" + authors + "\t\t\t\t\n\n")


main(True)
