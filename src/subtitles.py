import copy
import src.helpers as h
from itertools import groupby
from operator import itemgetter


def order_sub(subsection):
    subtuple = []
    for g in subsection:
        subtuple.append((g['page'], g))
    sorted_tuple = sorted(subtuple, key=itemgetter(0))
    pages = groupby(sorted_tuple, key=itemgetter(0))
    pages = [{'page':k, 'groups':[x[1] for x in v]} for k, v in pages]
    final_list = []
    for p in pages:
        first_column = [x for x in p['groups'] if x['bbox'][0] < 40]
        second_column = [x for x in p['groups'] if x['bbox'][0] >= 40]
        first_column = sorted(first_column, key=lambda g: g['bbox'][1])
        second_column = sorted(second_column, key=lambda g: g['bbox'][1])
        new_page = [x for x in first_column] + [y for y in second_column]
        final_list += new_page
    return final_list


def extract_section_subtitles(group_list):
    subs_list = []
    for i, group in enumerate(group_list):
        if len(group['lines']) == 1:
            subs_list.append(group)

        elif 2 <= len(group['lines']) <= 3 and h.check_bold(group):
            subs_list.append(group)
    return subs_list


def clean_section_subs(list_groups):
    final_list = copy.deepcopy(list_groups)
    count = 0
    # print(font_dict)
    for group in list_groups:
        count += 1
        multi_lined = False
        if len(group['lines']) == 1:
            text = group['lines'][0]['text']
        else:
            multi_lined = True
            text = ""
            for line in group['lines']:
                text = h.add_string(text, line['text'])
        
        if (len(text) > 50 and not multi_lined)or\
           len(text) < 4 or\
           text.count(".") > 2 or\
           text.count('(') > 0 or \
           h.test_long_subs(text) or\
           text.count("=") > 0 or \
           h.contains_word(text, "hopg") or\
           text.replace(' ', "").lower() == "absorbance" or\
           text.replace(' ', "").lower() == "langmuir" or \
           not h.string_has_characters(text) or\
           not h.is_title(text):
            # print(final_list[count - 1])
            del final_list[count - 1]
            count -= 1
    return final_list


def extract_subtitles(doc_list):
    """
    Function extract_subtitles function takes a list containing the text and extracts
    subtitles based on certain requirements:
    - If the text group is one line
    - If the text group is bold
    - If  the text is placed between paragraphs and space

    :param doc_list: list containing all of the groups of text previously grouped
    :type (list(list(str))) - (pages(text-group(text)))
    :return subs_list: list containing subtitles
    :rtype list(str)  - (subtitles extracted(text))
    """
    subs_list = []
    page_count = 0
    for page in doc_list:
        for group in page:
            for line in group:
                line['page'] = page_count
            if len(group) == 1:
                subs_list.append(group[0])

            elif len(group) == 2 and h.check_bold(group[0]) and page_count > 0:
                subs_list.append([group[0], group[1]])
        page_count += 1
    return subs_list


def clean_subs(semi_list):
    """
    Function clean_subs cleans the subtitles list to eliminate any non-subtitle elements such as
    figures and other single lines. It rules out certain sentences by comparing
    type of font to a previous subtitle and only keeping those with the same fonts.

    :param semi_list: list containing the subtitles extracted from previous function
    :type (list(str)) - (subtitles extracted(text))
    :return new_string_list: list containing the cleaned subtitles
    :rtype list(str) - (clean subtitles(text))
    """

    sections_list = ['abstract', 'introduction', 'results', 'references', 'conclusion', 'acknowledgements',
                     'experimental', 'methodology']
    final_list = copy.deepcopy(semi_list)
    new_string_list = []
    count = 0
    font_dict = {}
    for element in semi_list:
        if isinstance(element, dict):
            if h.contains(element['text'], sections_list) and len(element['text']) < 26:
                # print(element['text'])
                if h.get_font_type(element) not in font_dict.keys():
                    font_dict[h.get_font_type(element)] = [h.get_font_size(element)]
                else:
                    if h.get_font_size(element) not in font_dict[h.get_font_type(element)]:
                        font_dict[h.get_font_type(element)].append(h.get_font_size(element))
    # print(font_dict)
    for element in semi_list:
        count += 1
        if isinstance(element, dict):
            if len(element['text']) > 50 or len(element['text']) < 4 or element['text'].count(".") > 1 or element['text'].count('(') > 0 or\
                    (element['text'][-1] == "." and h.test_fonts(element, font_dict)) or h.test_long_subs(element['text']) or element['text'].count("=") > 0 or\
                    h.contains_word(element['text'], "hopg") or h.test_fonts(element, font_dict)or\
                    element['text'].replace(' ', "").lower() == "absorbance" or element['text'].replace(' ', "").lower() == "langmuir" or\
                    not h.string_has_characters(element['text']):
                #print(final_list[count - 1])
                del final_list[count - 1]
                count -= 1
        else:
            # print(element)
            # del final_list[count - 1]
            # count -= 1
            if h.test_fonts(element[0], font_dict):
                # print("HERE")
                del final_list[count - 1]
                count -= 1
    for element in final_list:
        # print(element)
        if isinstance(element, dict):
            new_string_list.append(element['text'])
        else:
            new_string_list.append(h.add_string(element[0]['text'], element[1]['text']))
    return new_string_list


def re_get_subtitles(dynamic_list, final_subs):
    """
    Function re_get_subtitles takes in the list containing the groups of text and
    the final subtitles extracted. It goes through and checks the subtitles

    :param dynamic_list: list containing all of the text groups
    :type (list(list(str))) - (pages(text-group(text)))
    :param final_subs: containing the extracted subtitles
    :type (list(str))
    :return new_sub: list containing final subtitles
    :rtype list(str) - subtitles
    """
    new_sub = []
    for page in dynamic_list:
        for group in page:
            text = ""
            for line in group['lines']:
                text = h.add_string(text, line['text'])
            if h.check_subs(group, final_subs):
                new_sub.append(text)
    return final_clean_subtitles(new_sub)


def final_clean_subtitles(sub_list):
    new_sub_list = h.delete_repeats(sub_list)
    for i in range(len(new_sub_list)):
        new_sub_list[i] = new_sub_list[i].strip(" ")
    return new_sub_list
