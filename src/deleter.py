import copy
import src.helpers as h


def delete_irrelevant(doc_list, ignore_list):
    """
    Given a document loop through document and delete the words that are part of
    the ignore list. return the new cleaned document

    :param doc_list: document that is a list of pages, each page a list of spans, each span a dict
    :type doc_list: list(list(dict))
    :param ignore_list: list of words to ignore/delete from document
    :type ignore_list: list(str)
    :return: new document without words in ignore list
    :rtype: list(list(dict))
    """
    new_doc_list = copy.deepcopy(doc_list)
    page_count = 0
    span_count = 0
    line_count = 0
    for page in doc_list:
        for line in page:
            for span in line['spans']:
                span_count += 1
                if h.contains(span["text"], ignore_list):
                    # print(new_doc_list[page_count][span_count-1])
                    del new_doc_list[page_count][line_count]['spans'][span_count - 1]
                    span_count -= 1
                else:
                    new_doc_list[page_count][line_count]['spans'][span_count-1]['text'] =\
                        new_doc_list[page_count][line_count]['spans'][span_count-1]['text'].encode("ascii", "ignore").decode("utf-8", "ignore")
            span_count=0
            line_count+=1

        page_count += 1
        line_count = 0
    return new_doc_list


def delete_figures(doc_list):
    """
    Given a document, loop through the document and delete figure captions. Structure of
    the document is a list of pages, each page is a list of groups, each group is a list
    of spans.

    :param doc_list: the document to be looped through
    :type doc_list: list(list(list(dict)))
    :return: new doc_list without figure captions
    :rtype: list(list(list(dict)))
    """
    temp_list = copy.deepcopy(doc_list)
    count_page = 0
    count_group = 0
    for page in doc_list:
        for group in page:
            count_group += 1
            if h.test_figures(group[0]['text']) and len(group) < 8:
                    #print("Figure \n\n")
                    #print(temp_list[count_page][count_group - 1])
                    #print("\n\n\n\n\n")
                    del temp_list[count_page][count_group - 1]
                    count_group -= 1
        count_page += 1
        count_group = 0
    return temp_list


def delete_headers_footers(sorted_list):
    """
    Given a document, find groups that are in headers or footers and delete them from document.
    Document format: list of pages, each page is a list of groups, each group is a dict, containing
    bbox and font information and text. Only tests on top y coordinate (where it begins), whether a
    group starts in the top 5% or bottom 5% of the document

    :param sorted_list: document to be looped through
    :type sorted_list: list(list(dict))
    :return: new document without headers and footers
    :rtype: list(list(dict))
    """
    new_doc = []
    for page in sorted_list:
        new_page = []
        for group in page:
            if 5 < group['bbox'][1] < 95 and not find_group_in_other_pages(group, sorted_list):
                # print(group['text'])
                new_page.append(group)
        new_doc.append(new_page)
    return new_doc


def find_group_in_other_pages(group, sorted_list):
    for page in sorted_list:
        for g in page:
            try:
                if group['bbox'] == g['bbox'] and group['font'] == g['font'] and not group['lines'][0]['page'] == g['lines'][0]['page']:
                    return True
            except KeyError:
                pass
    return False
