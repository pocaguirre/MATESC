import src.helpers as h
import copy
from collections import OrderedDict


def sub_section_extraction(section, sub_titles):
    """
    The Format of the new sections will be the following:
    section = {
                'free': [group()],
                'subsections': [
                    (group(), [group()]),
                    (group(), [group()])
                ]
              }

    :param section:
    :type section: list
    :param sub_titles:
    :type sub_titles: list
    :return:
    """
    final = {'free': [], 'subsections': []}
    first_subsection = True
    sub_section_group = []
    sub_section_title = None

    for group in section:
        if group in sub_titles:
            if first_subsection:
                final['free'] = sub_section_group
                first_subsection = False
            else:
                final['subsections'].append((sub_section_title, sub_section_group))
            sub_section_group = []
            sub_section_title = group
        else:
            sub_section_group.append(group)
    if len(sub_titles) == 0:
        final['free'] = sub_section_group
    else:
        final['subsections'].append((sub_section_title, sub_section_group))
    '''
    if len(final['free']) > 1:
        # print("FREE:")
        for group in final['free']:
            for line in group['lines']:
                print("\t\t", line['text'])
    for ss in final['subsections']:
        for line in ss[0]['lines']:
            print('\t', line['text'])
        for group in ss[1]:
            for line in group['lines']:
                print('\t\t', line['text'])
    '''
    return final


def section_extraction(sorted_list, final_subs):
    """
    Given a document and a list of section titles that are sorted correctly
    extract the sections of a document:
    - Find title and authors
    - If title is found on second page, find title and authors on second page
    - Get Abstract and location of abstract
    - If there is less than 3 sections, get section with body, else just get section without body
    - If no sections found, get all the text in one section called body

    :param sorted_list: document to be processed
    :type sorted_list: list(list(dict))
    :param final_subs: list of section titles
    :type final_subs: list(str)
    :return: Final dictionary of sections
    :rtype: dict
    """
    sections = {}
    #print_all(sorted)

    # Find title and authors
    title, authors = get_title_and_authors(sorted_list)
    sections['title'] = title
    sections['authors'] = authors

    # Find title and authors on second page
    if h.find_title_on_second_page(sorted_list, title):
        del sorted_list[0]
        title, authors = get_title_and_authors(sorted_list)
        sections['title'] = title
        sections['authors'] = authors
    for element in final_subs:
        #print(element)
        #print(authors)
        group_text = ""
        for line in authors['lines']:
            group_text = h.add_string(group_text, line['text'])
        if element.replace(" ", "") == group_text.replace(" ", ""):
            #print("HERE")
            final_subs.remove(element)
    dict_count = 0
    #print(final_subs)
    if final_subs:
        # print(dict_count)

        # Get Abstract
        temp, location = get_abstract(sorted_list, final_subs)
        if temp:
            index = 100
            for sub in range(len(final_subs)):
                if final_subs[sub].strip(" ").lower() == 'abstract':
                    index = sub
            if not index == 100:
                del final_subs[index]
        if dict_count < len(final_subs):
            if h.find_intro_in_subs(final_subs):
                if not h.contains_word(final_subs[dict_count], "introduction"):
                    dict_count += 1

        # If less than 3 sections get sections with body
        if len(final_subs) < 4 and not h.find_intro_in_subs(final_subs):
            # print("HERE")
            if location == (0, 0):
                contents = get_sections_with_body(sorted_list, temp, final_subs, dict_count, location, authors)
            else:
                contents = get_sections_with_body(sorted_list, temp, final_subs, dict_count, location)
            sections['contents'] = contents
            try:
                if len(sections['contents']['body']) < 500:
                    del sections['contents']['body']
            except KeyError:
                pass

        # Else find sections without body
        else:
            sections["contents"] = get_sections(sorted_list, temp, final_subs, dict_count)
    else:
        temp, location = get_abstract(sorted_list)
        # print(temp['abstract'])
        body = ""
        body_group = []
        abstract = False
        for i in range(len(sorted_list)):
            for j in range(len(sorted_list[i])):
                if (i, j) == location:
                    abstract = True
                elif abstract:
                    for line in sorted_list[i][j]['lines']:
                        body = h.add_string(body, line['text'])
                    body_group.append(sorted_list[i][j])
        temp['body'] = body_group
        sections['contents'] = temp
    # TODO: Keyword section handling with new output
    try:
        # print("HERE")
        # print(sections['contents']['keywords'])
        sections['contents']['keywords'] = sections['contents']['keywords'][:70]
    except KeyError:
        # print("ERROR")
        pass
    return sections


def get_sections_with_body(sorted_list, temp, final_subs, dict_count, location, authors=None):
    """
    Get Sections with body because there are not many section subtitles so a body
    section might be needed. Given the abstract location loop through the document
    until a section title is found and add to the temp dictionary

    :param sorted_list: document to be processed
    :type sorted_list: list(list(dict))
    :param temp: dictionary that holds the title and previous features
    :type temp: dict
    :param final_subs: list of section titles
    :type final_subs: list(str)
    :param dict_count: counter of the list of section titles
    :type dict_count: int
    :param location: abstract location: page, group
    :type location: list(int)
    :param authors: string representing authors or title depending on what is last
    :type authors: dict
    :return: dictionary of final sections
    :rtype: dict
    """
    # print("HERE")
    page_number = location[0]
    group_number = location[1]
    abstract_location = False
    second_loop = False
    temp_text = ""
    temp_group = []
    for page in range(len(sorted_list)):
        for group in range(len(sorted_list[page])):
            if abstract_location:
                # print(final_subs[dict_count])
                # print(sorted_list[page][group]["text"])
                # print(group["text"] + "\n\n\n\n")
                if sorted_list[page][group]["lines"][0]['text'].find(final_subs[dict_count]) > -1:
                    # print()
                    if not second_loop:
                        # print("HERE")
                        # temp2[final_subs[dict_count]] += group["text"]
                        # print(group["text"])
                        # temp_text += group["text"]
                        # print('\n\n'+str(temp_text))
                        temp['body'] = temp_group
                        # print(temp_text)
                        temp_text = ""
                        temp_group = []
                        second_loop = True
                        if dict_count < (len(final_subs) - 1):
                            dict_count += 1
                            # print(final_subs[dict_count])
                            # print(dict_count)
                    else:
                        # print("HERE")
                        # print(final_subs[dict_count-1].lower())
                        # print(temp_text)
                        temp[final_subs[dict_count - 1].lower().strip(" ")] = temp_group
                        temp_text = ""
                        temp_group = []
                        # print(dict_count)
                        # print("saving" + final_subs[dict_count-1])
                        if dict_count < (len(final_subs) - 1):
                            dict_count += 1
                            # print(final_subs[dict_count])
                            # print(dict_count)
                elif second_loop:
                    for i in range(len(sorted_list[page][group]['lines'])):
                        temp_text = h.add_string(temp_text, sorted_list[page][group]['lines'][i]['text'])
                    temp_group.append(sorted_list[page][group])
                else:
                    # print("HERE")
                    for i in range(len(sorted_list[page][group]['lines'])):
                        temp_text = h.add_string(temp_text, sorted_list[page][group]['lines'][i]['text'])
                    temp_group.append(sorted_list[page][group])
            elif page_number == 0 and group_number == 0:
                authors_text = ""
                for line in range(len(sorted_list[page][group]['lines'])):
                    authors_text = h.add_string(authors_text, sorted_list[page][group]['lines'][line]['text'])
                a_t = ""
                for line in authors['lines']:
                    a_t = h.add_string(a_t, line['text'])
                if authors_text == a_t:
                    abstract_location = True
            elif page == page_number and group_number == group:
                abstract_location = True
    temp[final_subs[dict_count].lower().strip(" ")] = temp_group
    return temp


def get_sections(sorted_list, temp, final_subs, dict_count):
    """
        Get Sections without body because there are enough section subtitles. Loop through the document
        until a section title is found and add to the temp dictionary

        :param sorted_list: document to be processed
        :type sorted_list: list(list(dict))
        :param temp: dictionary that holds the title and previous features
        :type temp: dict
        :param final_subs: list of section titles
        :type final_subs: list(str)
        :param dict_count: counter of the list of section titles
        :type dict_count: int
        :return: dictionary of final sections
        :rtype: dict
    """
    second_loop = False
    temp_text = ""
    temp_group = []
    for page in sorted_list:
        for i, group in enumerate(page):
            # print(final_subs[dict_count-1])
            # print(group["text"] + "\n\n\n\n")
            text = ""
            for i in range(min(len(group['lines']), 3)):
                text = h.add_string(text, group['lines'][i]['text'])
            if group['lines'][0]["text"].find(final_subs[dict_count]) > -1 or \
                    text.find(final_subs[dict_count]) > -1:
                if not second_loop:
                    # temp2[final_subs[dict_count]] += group["text"]
                    # print(group["text"])
                    # temp_text += group["text"]
                    # print('\n\n'+str(temp_text))
                    second_loop = True
                    if dict_count < (len(final_subs) - 1):
                        dict_count += 1
                        # print(final_subs[dict_count])
                        # print(dict_count)
                else:
                    # print("HERE")
                    # print(final_subs[dict_count-1].lower())
                    # print(temp_text)
                    temp[final_subs[dict_count - 1].lower().strip(" ")] = temp_group
                    temp_text = ""
                    temp_group = []
                    # print(dict_count)
                    # print("saving" + final_subs[dict_count-1])
                    if dict_count < (len(final_subs) - 1):
                        dict_count += 1
                        # print(final_subs[dict_count])
                        # print(dict_count)
            elif second_loop:
                for line in group['lines']:
                    temp_text = h.add_string(temp_text, line['text'])
                temp_group.append(group)
    temp[final_subs[dict_count].lower().strip(" ")] = temp_group
    return temp


def get_abstract(sorted_list, final_subs=None):
    """
    Given document and a list of section titles, extract the abstract

    :param sorted_list: document to be processed
    :type sorted_list: list(list(dict))
    :param final_subs: list of section titles
    :type final_subs: list(str)
    :return: dictionary that contains the abstract
    :rtype: dict
    """
    # print(dict_count)
    temp = OrderedDict()
    loop = False
    dict_count = 0
    if final_subs:
        if final_subs[0].lower().find("abstract") > -1:
            dict_count = 1
            abstract_in_subs = True
        else:
            dict_count = 0
            abstract_in_subs = False
    else:
        abstract_in_subs = False
    page_counter = 0
    for page in sorted_list:
        abstract_text = ""
        abstract_font = (0, "type")
        abstract_group = []
        group_counter = 0
        for group in page:
            if group["lines"][0]['text'].lower().find('abstract') > -1:
                loop = True
                if not abstract_in_subs and len(group['lines']) > 1:
                    for line in group['lines']:
                        words = line['text'].strip(" ").split(" ")
                        if words[0].replace(" ", "").replace(":", "").replace(".", "").replace(",", "").lower() =='abstract':
                            del words[0]
                        for word in words:
                            abstract_text = h.add_string(abstract_text, word)
                        # abstract_text += group["text"]
                        # print(group)
                        abstract_font = (h.get_font_size(line), h.get_font_type(line))
                    line_text = ''
                    words = group['lines'][0]['text'].strip(" ").split(" ")
                    if words[0].replace(" ", "").replace(":", "").replace(".", "").replace(",","").lower() == 'abstract':
                        del words[0]
                    for word in words:
                        line_text = h.add_string(line_text, word)
                    group['lines'][0]['text'] = line_text
                    abstract_group.append(group)
            elif loop:
                if abstract_in_subs:
                    for line in group['lines']:
                        abstract_text = h.add_string(abstract_text, line['text'])
                        # print(group)
                        abstract_font = (h.get_font_size(group), h.get_font_type(group))
                        abstract_in_subs = False
                    abstract_group.append(group)
                # print(dict_count)
                elif final_subs:
                    if (not (group['lines'][0]["text"].find(final_subs[dict_count]) > -1)) and\
                            abstract_font == (h.get_font_size(group), h.get_font_type(group)):
                        for line in group['lines']:
                            abstract_text = h.add_string(abstract_text, line['text'])
                        abstract_group.append(group)
                    else:
                        temp["abstract"] = abstract_group
                        # sections["contents"].update(temp)
                        return temp, (page_counter, group_counter)
            group_counter += 1
        page_counter += 1
    group_counter = 0
    if len(sorted_list) > 0:
        for group in sorted_list[0]:
            if group['column'] == 1:
                if len(group['lines']) > 3:
                    abstract_text = ""
                    for line in group['lines']:
                        abstract_text = h.add_string(abstract_text, line['text'])
                    temp['abstract'] = [group]
                    return temp, (0, group_counter)
            group_counter += 1
        group_counter = 0
        for group in sorted_list[0]:
            if group['column'] == 2:
                # print(group['font'])
                if len(group['lines']) > 3 and (h.check_bold(group) or h.check_italic(group)):
                    print("HERE")
                    abstract_text = ""
                    for line in group['lines']:
                        abstract_text = h.add_string(abstract_text, line['text'])
                    temp['abstract'] = [group]
                    return temp, (0, group_counter)
            group_counter += 1
    return temp, (0, 0)


def get_title_and_authors(sorted_list):
    """
    Given a document list, find the title and authors. We are using a list of words
    to ignore

    :param sorted_list: document to be processed
    :type sorted_list: list(list(dict))
    :return: title, authors, location
    :rtype: str, str
    """
    ignore_list = ["author", "copyright", "journal", "published", "downloaded", "article", "licensed", "download",
                   "available", "doi", "ip", "please", "institute", "university", "laboratory", "department", "letters",
                   "rsc", "research", "iop", "school", "american", "keyword", "abstract", 'introduction', 'appl',
                   "angewandte", 'nih', 'adv', 'crystengcomm', 'title']
    ignore_authors = ["communication", "vol.", "no.", "cite", "published", "licensed", "article", "factor",
                      "citation", "institute", "paper", "mechanistic", "molecule", "issn", 'introduction', 'material',
                      'experimental', 'nano', 'vol', 'wiley-vch', 'e-mail', 'supplementary', 'www', 'com', 'angewandte',
                      'abstract', 'information', 'keyword', 'manuscript', 'review', '(dsscs)', 'content', 'please',
                      'epitaxy', 'title', 'table', 'fortran', 'zuschriften', 'nanoparticle', 'december',
                      'germany']

    copy_list = copy.deepcopy(sorted_list)
    new_list = []
    for page in copy_list:
        new_page = sorted(page, key=lambda g: g['bbox'][1])
        new_page = sorted(new_page, key=lambda g: int(g['size']), reverse=True)
        new_list.append(new_page)

    # for page in new_list:
    #     for group in page:
    #         print(group)

    title = ""
    title_found = False
    page_counter = 0
    for page in new_list:
        group_counter = 0
        for group in page:
            #print(group)
            group_text = ""
            for line in group['lines']:
                group_text = h.add_string(group_text, line['text'])
            if not h.contains(group_text, ignore_list) and group["bbox"][0] < 50 and (not title_found) and\
                    len(group_text) > 9 and not group_text.lower().replace(" ", "") == "shortcommunication" and\
                    len(group_text) < 200 and group['bbox'][3] > 5 and group['bbox'][1] > 2 and\
                    not group_text.lower() == ' nanoscale' and\
                    not group_text.lower() == ' comptes rendus chimie' and\
                    not group_text == ' Materials Chemistry' and group['bbox'][3] < 90:
                if len(group_text) < 25:
                    if not h.contains_word(group_text, 'information'):
                        title = group
                        title_found = True
                else:
                    title = group
                    #print(title)
                    title_found = True
            elif h.prove_author(group_text, ignore_authors) and title_found and 7 < len(group_text) < 500 and\
                            group['bbox'][0] < 75:
                if group_text.lower().strip(" ") == 'a b s t r a c t':
                    return title, {'lines': [{'text': 'no authors'}]}
                return title, group
            elif title_found and page_counter > 0 and h.contains_word(group_text, 'introduction'):
                return title, {'lines': [{'text': 'no authors'}]}
            group_counter += 1
        page_counter += 1
    if title:
        return title, {'lines': [{'text': 'no authors'}]}
    else:
        try:
            return sorted_list[0][0]['text'], {'lines': [{'text': 'no authors'}]}
        except IndexError:
            return {'lines': [{'text': 'no title'}]}, {'lines': [{'text': 'no authors'}]}
