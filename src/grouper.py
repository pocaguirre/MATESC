import src.helpers as h


def merging_lines(document_list):
    """
    given a document loop through the spans and merge spans to form
    corresponding lines as they would appear on the pdf.

    :param document_list: document to be looped through
    :type document_list: list(list(dict))
    :return: new document with merged lines
    :rtype: list(list(dict))
    """
    final_list = []
    first_span = True
    for i, page in enumerate(document_list):
        if i == 10:
            print("HERE")
        page_list = []
        for span in page:
            if first_span:
                page_list.append(span)
                first_span = False
            else:
                boolean, t = h.check_same_line(page_list[-1], span)
                if boolean and not h.check_inline_subs(page_list[-1], span):
                    page_list[-1] = merge(page_list[-1], span, t)
                else:
                    page_list.append(span)
        first_span = True
        final_list.append(page_list)
    for page in final_list:
        for span in range(len(page)):
            page[span] = h.fix_spaces(page[span])
    '''
    final_list = []
    first_span = True
    for i, page in enumerate(document_list):
        page_list = []
        for line in page:
            new_line = {"text": "", "bbox": line['bbox'], "dir": line['dir'], "font": "", "size": 0}
            for span in line['spans']:
                new_line = merge(new_line, span)
            page_list.append(new_line)
        final_list.append(page_list)
    for page in final_list:
        for span in range(len(page)):
            page[span] = h.fix_spaces(page[span])
    '''
    return final_list


def merge(span1, span2, t=None):
    """
    Given two spans to be merged, merge the spans into a new span. It requires
    to recalculate the bounding box as well as the font type and size and
    merge the text of the spans

    :param span1: one of the spans to merge
    :type span1: dict
    :param span2: the other span to merge
    :type span2: dict
    :param t: type whether subscript or superscript
    :return: new span
    :rtype: dict
    """
    if span1['text'] == "":
        return span2
    if span2['text'] == "":
        return span1


    # Putting the text together
    if span1['text'][-1] != " " and span2['text'][0] != " " and span2['bbox'][0] - span1['bbox'][2] > 1:
        # This means there won't be a space character in between the spans
        text = span1['text'] + " " + span2['text']
    else:
        text = span1["text"] + span2["text"]

    if 'html' in span1.keys():
        prev_html = span1['html']
    else:
        prev_html = span1['text']
    if t == "2+":
        html = prev_html + "<sup>" + span2['text'] + "</sup>"
    elif t == "2-":
        html = prev_html + "<sub>" + span2['text'] + "</sub>"
    elif t == "1+":
        html = "<sup>" + prev_html + "</sup>" + span2['text']
    elif t == "1-":
        html = "<sub>" + prev_html + "</sub>" + span2['text']

    # calculating the y coordinates of the new bbox
    if (span1["bbox"][3] - span1["bbox"][1]) > (span2["bbox"][3] - span2["bbox"][1]):
        bbox1 = span1["bbox"][1]
        bbox3 = span1["bbox"][3]
    else:
        bbox3 = span2["bbox"][3]
        bbox1 = span2["bbox"][1]

    # if span1['text'] == "":
    #     return {"bbox": span1['bbox'], "font": span2['font'], "size": span2['size'], "text": span2['text'], "html":span2['text']}
    # text = span1["text"] + span2["text"]

    # Determining the font size of new span based of length of text
    if len(span1['text']) > len(span2['text']):
        size = span1['size']
    else:
        size = span2['size']

    # Getting new font type of new span based on being italic or bold and length of text
    if not (span1['font'][-6:].lower() == 'italic' or span1['font'][-4:].lower() == 'bold' or
            span2['font'][-6:].lower() == 'italic' or span2['font'][-4:].lower() == 'bold'):
        if len(span1['text']) > len(span2['text']):
            type_font = span1['font']
        else:
            type_font = span2['font']
    else:
        # print(span2)
        # print()
        if span1['font'][-6:].lower() == 'italic' or span1['font'][-4:].lower() == 'bold':
            type_font = span1['font']
        else:
            type_font = span2['font']
    if t is None and 'html' not in span1.keys():
        merged = {"bbox": [span1['bbox'][0], bbox1, span2['bbox'][2], bbox3], "font": type_font, "size": size,
                  "text": text}
    elif t is None and 'html' in span1.keys():
        merged = {"bbox": [span1['bbox'][0], bbox1, span2['bbox'][2], bbox3], "font": type_font, "size": size,
                  "text": text, "html": span1['html']+span2['text']}
    else:
        merged = {"bbox": [span1['bbox'][0], bbox1, span2['bbox'][2], bbox3], "font": type_font, "size": size,
                  "text": text, "html": html}
    # print(merged)
    return merged


def grouping(doc_list):
    """
    Given a document, group the lines into paragraphs or sections based on metadata features such as
    font size and type and spacing based on bounding box

    :param doc_list: document to be processed
    :type list(list(dict))
    :return: new document that has grouped lines
    :rtype: list(list(list(dict)))
    """
    paper_list = []
    for page in doc_list:
        first_line = True
        page_list = []
        space = 0
        for line in page:
            """
            for each line, if its the first line of the group (first is true for default),
            add line to new group, compare next line, and add next line if passes the test,
            then save spacing, else close group and add next line to a new group. Else if
            not first line of group, then test if belongs to group, if it does append to group
            else close group and append to a new group.
            """
            if first_line:
                ''' If First line, append line as a single paragraph to page list and set spacing to -1 '''
                first_line = False
                page_list.append([line])
                space = -1
            elif h.compare_font(page_list[-1][-1], line) and\
                    not(line['bbox'][0] > 90) and\
                    (space == -1 or space == h.calculate_spacing(page_list[-1][-1], line)):
                ''' If the fonts are the same, the span is located less than 90% and the paragraph spacing is 
                    -1 meaning this is second line or the same as the expected, then append to same group '''
                if space == -1:
                    space = h.calculate_spacing(page_list[-1][-1], line)
                page_list[-1].append(line)
            else:
                ''' Else it doesn't belong to same paragraph, therefore add as new paragraph '''
                page_list.append([line])
                space = -1
        paper_list.append(page_list)

        # print("\nPAGE:")
        # for paragraph in page_list:
        #     print("\n")
        #     for line in paragraph:
        #         print("\t\t" + line['text'])
    return paper_list


def recalculate_groups(dynamic_list):
    """
    Given a document, loop through the groups and combine all lines inside the group
    into one dictionary containing all information

    :param dynamic_list: document to be processed
    :type dynamic_list: list(list(list(dict)))
    :return: new document list
    :rtype: list(list(dict))
    """
    new_final_list = []
    for page in dynamic_list:
        page_list = []
        for group in page:
            new_dict = {}
            lowest_x = 100
            highest_x = 0
            for line in group:
                # find if x is the lowest or highest
                if line['bbox'][0] < lowest_x:
                    lowest_x = line['bbox'][0]
                if line['bbox'][2] > highest_x:
                    highest_x = line['bbox'][2]
            x_one = lowest_x
            x_two = highest_x
            y_one = group[0]['bbox'][1]
            y_two = h.get_biggest_y(group)
            new_bbox = [x_one, y_one, x_two, y_two]
            new_dict['bbox'] = new_bbox
            new_dict['font'] = h.find_font_in_group(group)
            new_dict['size'] = h.find_font_size_in_group(group)
            new_dict['page'] = group[0]['page']
            new_dict['lines'] = group

            page_list.append(new_dict)

        new_final_list.append(page_list)
    return new_final_list


def group_into_columns(dynamic_list, sub_list):
    """
    Group into columns controller. Grouping into columns means to determine
    whether a groups bounding box length corresponds to being a one column
    part of the document, two columns or three. The purpose is because it's
    really hard to order a document based on how a person would read it. We
    found that people learn to divide a document based on the layout (how many
    columns there are). The algorithms input is a document and a list of the
    title sections found (this is because title sections if not treated separate
    would always be the length of a 3 column group).

    :param dynamic_list: document list to be processed
    :type dynamic_list: list(list(dict))
    :param sub_list: section titles found in the document
    :type sub_list: list(str)
    :return: ordered document
    :rtype: list(list(dict))
    """
    # Limit constants of the column length i.e. to be a one column it has to be longer than 52% of documents length
    column3 = 27
    column1 = 52

    document_list = assign_columns(dynamic_list, sub_list, column1, column3)
    new_document_list = divide_subgroups(document_list)
    sorted_subgroups = sort_subgroups(new_document_list)
    sorted_columns = sort_column_type(sorted_subgroups)
    return transform_ordering(sorted_columns)


def assign_columns(dynamic_list, sub_list, column1, column3):
    """
    Given a document, a subtitle list, and variables of column1 and column3,
    sort all groups into being part of a 1 column, 2 column or 3 column.
    If subtitle is found, then match it together with the following group
    if that group is long enough, else match it with the next one.

    :param dynamic_list: document to be processed
    :type dynamic_list: list(list(dict))
    :param sub_list: list of section titles
    :type sub_list: list(str)
    :param column1: number constant of limit of 1-2 column
    :type column1: int
    :param column3: number constant of limit of 2-3 column
    :type column3: int
    :return: new document list that its groups are sorted into columns
    :rtype: list(list(list(dict)))
    """
    document_list = []
    # print(sub_list)
    for i, page in enumerate(dynamic_list):
        group1 = []
        group2 = []
        group3 = []
        subtitle = 0
        group_counter = 0
        for group in page:
            if h.check_subs(group, sub_list):
                # print(group['text'])
                subtitle = 1
            elif subtitle and len(group['lines']) < 5 and len(group['lines'][0]['text']) < 35:
                # print("secondTime\t" + group['text'])
                subtitle += 1
            else:
                if h.get_bbox_length(group['bbox']) <= column3 and i == 0:
                    if subtitle:
                        # print(subtitle)
                        # print(group)
                        for i in range(1, subtitle+1):
                            page[group_counter-i]['column'] = 3
                            group3.append(page[group_counter-i])
                        subtitle = 0
                    # if subtitle:
                    #     print(len(group['text']))
                    #     page[group_counter-1]['column'] = 3
                    #     group3.append(page[group_counter-1])
                    #     subtitle = False
                    group['column'] = 3
                    group3.append(group)
                elif h.get_bbox_length(group['bbox']) <= column1:
                    if subtitle:
                        # print(subtitle)
                        # print(group)
                        for i in range(1, subtitle+1):
                            page[group_counter-i]['column'] = 2
                            group2.append(page[group_counter-i])
                        subtitle = 0
                    # if subtitle:
                    #     page[group_counter-1]['column'] = 2
                    #     group2.append(page[group_counter-1])
                    #     subtitle = False
                    group['column'] = 2
                    group2.append(group)
                else:
                    if subtitle:
                        for i in range(1, subtitle+1):
                            page[group_counter-i]['column'] = 1
                            group1.append(page[group_counter-i])
                        subtitle = 0
                    # if subtitle:
                    #     page[group_counter-1]['column'] = 1
                    #     group1.append(page[group_counter-1])
                    #     subtitle = False
                    group['column'] = 1
                    group1.append(group)
            group_counter += 1
        page_list = [group1, group2, group3]
        document_list.append(page_list)
    return document_list


def divide_subgroups(document_list):
    """
    Given a document whose groups have already been categorized in column types,
    go inside the columns and separate into the columns that it corresponds,
    i.e. If in a 2 column group, separate that group into two groups, left and right.

    :param document_list: document to be processed
    :type document_list: list(list(list(dict)))
    :return: new document
    :rtype: list(list(list(list(dict))))
    """
    new_doc_list = []
    for page in document_list:
        if page[0]:
            page[0] = [page[0]]
        if page[1]:
            # print(page[1])
            subgroup1 = []
            subgroup2 = []
            for group in page[1]:
                if group['bbox'][0] < 40:
                    subgroup1.append(group)
                else:
                    subgroup2.append(group)
            # print(subgroup1)
            # print(subgroup2)
            if subgroup1:
                if subgroup2:
                    col_group2 = [subgroup1, subgroup2]
                else:
                    col_group2 = [subgroup1]
            else:
                col_group2 = [subgroup2]
            # print(col_group2)
        else:
            col_group2 = []
        if page[2]:
            # print(page[2])
            subgroup1 = []
            subgroup2 = []
            subgroup3 = []
            for group in page[2]:
                # print("here")
                # print(group)
                if group['bbox'][0] < 20:
                    subgroup1.append(group)
                elif group['bbox'][0] < 50:
                    subgroup2.append(group)
                else:
                    subgroup3.append(group)
            # print(subgroup1)
            # print(subgroup2)
            # print(subgroup3)
            if subgroup1:
                if subgroup2:
                    if subgroup3:
                        col_group3 = [subgroup1, subgroup2, subgroup3]
                    else:
                        col_group3 = [subgroup1, subgroup2]
                else:
                    if subgroup3:
                        col_group3 = [subgroup1, subgroup3]
                    else:
                        col_group3 = [subgroup1]
            else:
                if subgroup2:
                    if subgroup3:
                        col_group3 = [subgroup2, subgroup3]
                    else:
                        col_group3 = [subgroup2]
                else:
                    if subgroup3:
                        col_group3 = [subgroup3]
                    else:
                        col_group3 = []
            # print(col_group3)
        else:
            col_group3 = []
        # print(page[0])
        # print(page[1])
        # print(page[2])
        # print("\n\n")
        new_doc_list.append([page[0], col_group2, col_group3])
    return new_doc_list


def sort_subgroups(new_document_list):
    """
    Given a document, that contains a list of pages, which contains three groups
    based on column numbers, which contain the columns themselves, order the groups
    inside those columns by the y coordinate in their bounding box

    :param new_document_list: document to be processed
    :type new_document_list: list(list(list(list(dict))))
    :return: new ordered document
    :rtype: list(list(list(list(dict))))
    """
    for page in new_document_list:
        if page[0]:
            page[0][0] = sorted(page[0][0], key=lambda g: g['bbox'][1])
        if page[1]:
            if page[1][0]:
                page[1][0] = sorted(page[1][0], key=lambda g: g['bbox'][1])
            if len(page[1])>1:
                if page[1][1]:
                    page[1][1] = sorted(page[1][1], key=lambda g: g['bbox'][1])
        if page[2]:
            if page[2][0]:
                page[2][0] = sorted(page[2][0], key=lambda g: g['bbox'][1])
            if len(page[2])>1:
                if page[2][1]:
                    page[2][1] = sorted(page[2][1], key=lambda g: g['bbox'][1])
                    if len(page[2])>2:
                        if page[2][2]:
                            page[2][2] = sorted(page[2][2], key=lambda g: g['bbox'][1])
    return new_document_list


def sort_column_type(sorted_subgroups):
    """
    Given a document, that contains a list of pages, which contains three groups
    based on column numbers, order those groups by their y coordinate in
    the bounding box

    :param sorted_subgroups: document to be processed
    :type sorted_subgroups: list(list(list(list(dict))))
    :return: new ordered document
    :rtype: list(list(list(list(dict))))
    """
    new_document_list = []
    for page in sorted_subgroups:
        if page[0]:
            if page[1]:
                if page[2]:
                    if page[1][0][0]['bbox'][1] < page[2][0][0]['bbox'][1]:
                        new_document_list.append([page[0], page[1], page[2]])
                    else:
                        new_document_list.append([page[0], page[2], page[1]])
                else:
                    new_document_list.append([page[0], page[1]])
            else:
                if page[2]:
                    new_document_list.append([page[0], page[2]])
                else:
                    new_document_list.append([page[0]])
        else:
            if page[1]:
                if page[2]:
                    if page[1][0][0]['bbox'][1] < page[2][0][0]['bbox'][1]:
                        new_document_list.append([page[1], page[2]])
                    else:
                        new_document_list.append([page[2], page[1]])
                else:
                    new_document_list.append([page[1]])
            else:
                if page[2]:
                    new_document_list.append([page[2]])
    return new_document_list


def transform_ordering(new_document_list):
    """
    Given a document, that contains a list of pages, which contains three groups
    based on column numbers, which contain the columns themselves, extract the
    groups inside those columns and add it to a page list to keep the format that
    was established throughout the algorithm

    :param new_document_list: document to be processed
    :type new_document_list: list(list(list(list(dict))))
    :return: new simplified document that has the format used throughout the algorithm
    :rtype: list(list(dict))
    """
    doc_list = []
    for page in new_document_list:
        # print("PAGE:")
        page_list = []
        for col_type in page:
            # print("\tCOL_TYPE:")
            for column in col_type:
                # print("\t\tCOLUMN:")
                for group in column:
                    # print("\t\t\t" + str(group))
                    page_list.append(group)
        doc_list.append(page_list)
    return doc_list

# def grouping(doc_list):
#     """
#     Given a document, group the lines into paragraphs or sections based on metadata features such as
#     font size and type and spacing based on bounding box
#
#     :param doc_list: document to be processed
#     :type list(list(dict))
#     :return: new document that has grouped lines
#     :rtype: list(list(list(dict)))
#     """
#     paper_list = []
#     for page in doc_list:
#         first_line = True
#         page_list = []
#         group_list = []
#         space = 0
#         for index in range(len(page) - 1):
#             """
#             for each span, if its the first line of the group (first is true for default),
#             add line to new group, compare next line, and add next line if passes the test,
#             then save spacing, else close group and add next line to a new group. Else if
#             not first line of group, then test if belongs to group, if it does append to group
#             else close group and append to a new group.
#             """
#             if first_line:
#                 #print("\n\nfirst Line")
#                 first_line = False
#                 group_list.append(page[index])
#                 # print("\n\n")
#                 # print(page[index+1])
#                 if h.compare_font(page[index], page[index + 1]) and\
#                         not(page[index]['bbox'][0] > 90):
#                     #print(page[index])
#                     #print(page[index+1])
#                     # print("here")
#                     # print(page[index + 1])
#                     group_list.append(page[index + 1])
#                     space = h.calculate_spacing(page[index], page[index+1])
#                     #print(page[index])
#                     #print(space)
#                 else:
#                     page_list.append(group_list)
#                     #print(group_list)
#                     group_list = []
#                     first_line = True
#                     #print(space)
#                     space = 0
#             else:
#                 if h.compare_font(page[index], page[index + 1]) and\
#                         space == h.calculate_spacing(page[index], page[index + 1]):
#                     # space = h.calculate_spacing(page[index], page[index + 1])
#                     #print(page[index])
#                     #print(space)
#                     group_list.append(page[index + 1])
#                     if index + 2 == len(page):
#                         page_list.append(group_list)
#                 else:
#                     page_list.append(group_list)
#                     #print(group_list)
#                     group_list = []
#                     first_line = True
#                     #print(space)
#                     space = 0
#         paper_list.append(page_list)
#     return paper_list
