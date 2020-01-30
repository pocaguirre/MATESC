import fitz
import os
import json
import re
import src.helpers as h
import src.xml_extraction as xml
import src.subtitles as subs
import src.deleter as delete
import src.grouper as group
import src.sectioner as section
import src.tester as test
import collections
from copy import deepcopy
import pypandoc
'''
Section Extraction using Metadata

    This extractor focuses on using metadata as the main feature. We get metadata from a python library
    called PyMuPDF (fitz). The input of the algorithm is a pdf file and a list of common words that should
    be ignored ( usually these words are located in the headers ). This is the controller file that gives the
    linear structure of the algorithm.
'''


def clean(pdf, ignore_list):
    """
    clean is the main function that takes as input a pdf file address and a list of words to be ignored in that
    document. The list of words is recommended to be a list of characters or header words that are often seen in
    pdf documents that are of no interest to the output of the program. The algorithm consists of:

    - Extracting the text and metadata information from document using fitz
    - Checking if the extracted text is not unicode (not usable)
    - Delete specified irrelevant words and symbols
    - Correct lines (merging lines)
    - group lines by paragraph or sections
    - delete figure captions
    - extract and clean section titles
    - merge groups (recalculate groups)
    - sort groups by grouping them in columns
    - order the section titles with new order of document
    - extract sections

    The output is an object that contains the title, authors and all the sections in the corresponding format:
    {
    title: "this is a title",
    authors: "this is, an author, and another "
    contents: [
        "section1" : "content of section one",
        "section2" : "content of section two"
    ]
    }

    :param pdf: a file path to the pdf to be extracted
    :type pdf: str
    :param ignore_list: a list of words or symbols to be ignored/deleted automatically
    :type ignore_list: list(str)
    :return: dictionary containing all sections of the pdf
    :rtype: dict
    """
    doc = fitz.Document(pdf)
    document_xml = xml.make_pages(doc)
    page_list = xml.make_json(document_xml)
    line_list = make_lines(page_list)
    if not test.detect_unrendered(line_list):
        document_json = delete.delete_irrelevant(line_list, ignore_list)
        merged_lines = group.merging_lines(document_json)
        grouped1 = group.grouping(merged_lines)
        # print_all(grouped1)
        grouped = delete.delete_figures(grouped1)
        subs_list = subs.extract_subtitles(grouped)
        # print_subs(subs_list)
        final_subs = subs.clean_subs(subs_list)
        dynamic_list2 = group.recalculate_groups(grouped)
        # print_all(dynamic_list2)
        sorted_list = group.group_into_columns(dynamic_list2, final_subs)
        # print_all(sorted_list)
        sorted_list = delete.delete_headers_footers(sorted_list)
        final_subs2 = subs.re_get_subtitles(sorted_list, final_subs)
        extracted = section.section_extraction(sorted_list, final_subs2)
        # print(final_subs2)
        # print_subs(final_subs2)
        # print_all(sorted_list)
        # print("***************************************************************************************************\n\n\n")
        """
        print("TITLE:")
        print("\t" + str(extracted['title']))
        print("AUTHORS:")
        print("\t" + str(extracted['authors']))
        print("CONTENTS")
        for k in extracted["contents"]:
            print("\n\n\t" + str(k))
            print("\t\t" + str(extracted["contents"][k]))
            """
        return extracted
    else:
        return None


# TODO: correctly output the type of text and subsections
# TODO: support html along with subscripts and superscripts and unicode characters
# TODO: move abstract outside of contents
def extract(pdf, ignore_list, subsections=False, output='.json'):
    """
        extract is the main function that takes as input a pdf file address and a list of words to be ignored in that
        document. The list of words is recommended to be a list of characters or header words that are often seen in
        pdf documents that are of no interest to the output of the program. The algorithm consists of:

        - Extracting the text and metadata information from document using fitz
        - Checking if the extracted text is not unicode (not usable)
        - Delete specified irrelevant words and symbols
        - Correct lines (merging lines)
        - group lines by paragraph or sections
        - delete figure captions
        - extract and clean section titles
        - merge groups (recalculate groups)
        - sort groups by grouping them in columns
        - order the section titles with new order of document
        - extract sections

        if subsection is false output is an object that contains the title, authors and all the sections in the corresponding format:
        {
        title: "this is a title",
        authors: "this is, an author, and another "
        contents: [
            "section1" : "content of section one",
            "section2" : "content of section two"
        ]
        }

        :param pdf: a file path to the pdf to be extracted
        :type pdf: str
        :param ignore_list: a list of words or symbols to be ignored/deleted automatically
        :type ignore_list: list(str)
        :return: dictionary containing all sections of the pdf
        :rtype: dict
    """
    doc = fitz.Document(pdf)
    document_xml = xml.make_pages(doc)
    page_list = xml.make_json(document_xml)
    line_list = make_lines(page_list)
    #if not test.detect_unrendered(line_list):
    #document_json = delete.delete_irrelevant(line_list, ignore_list)
    merged_lines = group.merging_lines(line_list)
    # for i, p in enumerate( merged_lines):
    #     for l in p:
    #         l['page'] = i + 1
    # return merged_lines

    print_all(merged_lines)
    grouped1 = group.grouping(merged_lines)
    grouped = delete.delete_figures(grouped1)
    subs_list = subs.extract_subtitles(grouped)
    final_subs = subs.clean_subs(subs_list)
    dynamic_list2 = group.recalculate_groups(grouped)
    sorted_list = group.group_into_columns(dynamic_list2, final_subs)
    sorted_list = delete.delete_headers_footers(sorted_list)
    final_subs2 = subs.re_get_subtitles(sorted_list, final_subs)
    extracted = section.section_extraction(sorted_list, final_subs2)
    if not subsections:
        if output == '.json':
            return extracted
    else:
        for k in extracted['contents']:
            if k != 'abstract':
                subtitles = subs.extract_section_subtitles(extracted['contents'][k])
                subtitles = subs.clean_section_subs(subtitles)
                extracted['contents'][k] = subs.order_sub(extracted['contents'][k])
                new_section = section.sub_section_extraction(extracted['contents'][k], subtitles)
                extracted['contents'][k] = new_section
        if output == '.json':
            t = ""
            product = {'title': "", 'authors': "", "contents": deepcopy(extracted['contents'])}
            for line in extracted['title']['lines']:
                t = h.add_string(t, line['text'])
            product['title'] = t
            t = ""
            for line in extracted['authors']['lines']:
                t = h.add_string(t, line['text'])
            product['authors'] = t
            for k in extracted["contents"]:
                t = ""
                if str(k) == 'abstract':
                    for g in extracted['contents'][k]:
                        for line in g['lines']:
                            t = h.add_string(t, line['text'])
                    product["contents"][k] = t
                else:
                    for g in extracted['contents'][k]['free']:
                        for line in g['lines']:
                            t = h.add_string(t, line['text'])
                    product['contents'][k]["free"] = t
                    product['contents'][k]['subsections'] = []
                    for s in extracted['contents'][k]['subsections']:
                        new_s = []
                        t = ""
                        for line in s[0]['lines']:
                            t = h.add_string(t, line['text'])
                        new_s.append(t)
                        t = ""
                        for g in s[1]:
                            for l in g['lines']:
                                t = h.add_string(t, l['text'])
                        new_s.append(t)
                        product['contents'][k]['subsections'].append(new_s)
            return product
        elif output == ".html":
            html_string = "<!DOCTYPE html>\n<html>\n<head>\n<style>\nsup {\nvertical-align: super;\nfont-size: small;\n}\n</style>\n</head>\n<body>"
            t = ""
            product = {'title': "", 'authors': "", "contents": deepcopy(extracted['contents'])}
            for line in extracted['title']['lines']:
                if "html" in line.keys():
                    t = h.add_string(t, line['html'])
                else:
                    t = h.add_string(t, line['text'])
            html_string += "\n<h1>\n{}\n</h1>".format(t)
            t = ""
            for line in extracted['authors']['lines']:
                if "html" in line.keys():
                    t = h.add_string(t, line['html'])
                else:
                    t = h.add_string(t, line['text'])
            html_string += "\n<p>\n{}\n</p>".format(t)
            for k in extracted["contents"]:
                t = ""
                if str(k) == 'abstract':
                    html_string += "\n<h2>Abstract</h2>"
                    for g in extracted['contents'][k]:
                        for line in g['lines']:
                            if "html" in line.keys():
                                t = h.add_string(t, line['html'])
                            else:
                                t = h.add_string(t, line['text'])
                    html_string += "\n<p>\n{}\n</p>".format(t)
                else:
                    html_string += "\n<h2>{}</h2>".format(k)
                    t = ""
                    for g in extracted['contents'][k]['free']:
                        for line in g['lines']:
                            if "html" in line.keys():
                                t = h.add_string(t, line['html'])
                            else:
                                t = h.add_string(t, line['text'])
                    html_string += "\n<p>\n{}\n</p>".format(t)
                    product['contents'][k]['subsections'] = []
                    for s in extracted['contents'][k]['subsections']:

                        t = ""
                        for line in s[0]['lines']:
                            if "html" in line.keys():
                                t = h.add_string(t, line['html'])
                            else:
                                t = h.add_string(t, line['text'])
                        html_string += "\n<h4>{}</h4>".format(t)
                        t = ""
                        for g in s[1]:

                            for l in g['lines']:
                                if "html" in l.keys():
                                    t = h.add_string(t, l['html'])
                                else:
                                    t = h.add_string(t, l['text'])
                        html_string += "\n<p>\n{}\n</p>".format(t)
            html_string += "\n</body>\n</html>"
            return html_string
        else:
            product = extracted
        return product



def handle_output_type(extracted, output):
    if output == 'json':
        return extracted
    elif output == 'json_s':
        return extracted
    elif output == 'text':
        final_string = ""
        for line in extracted['title']['lines']:
            final_string += line['text'] + ' '
        final_string += '\n\n'

        return extracted
    else:
        return "option not supported"


def print_all(dynamic_list):
    """
    This is a function for debuging purposes. It loops through a document list and prints in an orderly manner

    :param dynamic_list: list to be printed
    :type dynamic_list: list(str)
    """
    for page in dynamic_list:
        print("PAGE:")
        for group in page:
            # print("\tGROUP:")
            #print("\t\t" + str(group['column']) + "\t" + str(group))
            print("\t\t" + str(group))
            # for span in group['lines']:
            #     print("\t\t" + str(span))


def print_subs(sub_list):
    """
    This is a function for debuging purposes. It loops through a subtitle list and prints it

    :param sub_list: list to be printed
    :type sub_list: list(str)
    """
    for sub in sub_list:
        print(sub)


def make_lines(document_json):
    """
    Function that takes the output of PyMuPDF and extracts all spans in order to discard the order
    in which the library extracted it as. Returns a list of pages, each page is a list of spans

    :param document_json: output from PyMuPDF, dictionary
    :type document_json: dict
    :return: list(list(dict))
    """
    document_list = []
    for i, page in enumerate(document_json):
        page_list = []
        for blocks in page["blocks"]:
            for line in blocks["lines"]:
                for span in line["spans"]:
                    span['page'] = i + 1
                    page_list.append(span)
        document_list.append(page_list)
    '''
    document_list = []
    for page in document_json:
        page_list = []
        for blocks in page["blocks"]:
            for line in blocks["lines"]:
                page_list.append(line)
        document_list.append(page_list)
        '''
    return document_list


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


def send_to_json(references, json_path):
    with open(json_path, 'r') as json_file:
        data = json.load(json_file)
        data['raw_text']['extracted_sections']['references'] = references
    with open(json_path, 'w') as json_file:
        json_file.write(json.dumps(data))
    with open(json_path, 'r') as json_file:
        data = json.load(json_file)
        data['multiline_word_fix_text']['extracted_sections']['references'] = references
    with open(json_path, 'w') as json_file:
        json_file.write(json.dumps(data))


# TODO: call extract() rather than clean()
# TODO: ask team what is the best way to keep new subsections on mongo and show them on fingolfin
def main(output_path):
    connection = MongoClient('mongodb://localhost:27017/')
    db = connection.live
    document_list = file_list(output_path)
    ignore_list = ["copyright", "journal", "publisher", "downloaded", "licensed", "download",
                "doi", "ip", '■', 'XXX','org/', 'org']
    counter = 1
    # grobid_dictionary = grobid.extract_from_json()
    print(output_path)
    for file in document_list:
        product = extract(file, ignore_list, True)
        paper_id = file.split('/')[-1].replace('.pdf', '')
        # try:
        #     doi = grobid_dictionary[paper_id]['DOI']
        # except:
        #     pass

        if product:
            print("******************************************************************************\n{}"
                  "  {}".format(counter, file))

            temp_dictionary = db.papers.find_one(
                {'paper_id' : paper_id}
            )
            if temp_dictionary:
                for key, value in temp_dictionary['content'].items():
                    if key:
                        db.papers.update_one(
                            {'paper_id' : paper_id},
                            {
                                '$set' : {
                                    'misc.' + key : value
                                }
                            }
                        )
            db.papers.update_one(
                {'paper_id' : paper_id},
                {
                    '$set' : {
                        'content' : {}
                    }
                }
            )

            try:
                json_path = '{}/{}/{}.json'.format(output_path, paper_id, paper_id)
                send_to_json(product['contents']['references'], json_path)
            except:
                pass

            product['authors'] = re.sub('[^A-Za-z0-9\.\,]+', ' ', product['authors'])
            product['authors'] = product['authors'].split(',')
            # product['DOI'] = doi
            author_ids = []
            for author in product['authors']:
                author_item = db.authors.find_one({'name': author})
                if author_item is None:
                    author_id = db.authors.insert_one({'name': author}).inserted_id
                else:
                    author_id = author_item.get('_id')
                author_ids.append(author_id)
            product['authors'] = author_ids
            db.papers.update_one(
                {'paper_id' : paper_id},
                {
                    '$set' : {
                        'title' : product['title'],
                        'authors' : product['authors']
                        # 'doi' : product['DOI']
                    }
                }
            )
            new_contents = collections.OrderedDict()
            for key, value in product['contents'].items():
                new_key = re.sub(r'([^\s\w]|_)+', '', key)
                try:
                    while new_key[0].isdigit() or ' ' in new_key[0]:
                        new_key = new_key[1:]
                except:
                    pass
                finally:
                    new_contents[new_key.title()] = value
                    pass
            product['contents'] = new_contents
            db.papers.update_one(
                {'paper_id': paper_id},
                {
                    '$set': {
                        'content': product['contents']
                    }
                }
            )
        else:
            print("********************************************************************************\n\nUNRENDERABLE"
                  "\n\n********************************************************************************")
        counter += 1


def debug():
    products = []
    for i in range(1,12):
        product = extract("/Users/caguirre97/developer/KDD/extractor/input/0{}.pdf".format(i),
                        ["copyright", "journal", "publisher", "downloaded", "licensed", "download",
                         "doi", "ip", '■', 'XXX', 'org/', 'org'], subsections=True, output='.html')

        products.append(product)


        """print("____________________________________________________")
        print("{}.".format(i))
        print("TITLE:")
        print("\t" + product['title'] + "\n")
        print("AUTHORS:")
        print("\t" + product['authors'] + "\n")
        print("CONTENTS")
        for k in product["contents"]:
            # # t = ""
            # # for group in product['contents'][k]:
            # #     for line in group['lines']:
            # #         t = h.add_string(t, line['text'])
            # if str(k) == 'abstract':
            #     print("\n\n\t" + str(k))
            #     for g in product['contents'][k]:
            #         for line in g['lines']:
            #             print("\t\t", line['text'])
            # else:
            #     print("\n\n\t" + str(k))
            #     for g in product['contents'][k]['free']:
            #         for line in g['lines']:
            #             print("\t\t\t", line['text'])
            #     for s in product['contents'][k]['subsections']:
            #         for line in s[0]['lines']:
            #             print("\t\t", line['text'])
            #         for g in s[1]:
            #             for l in g['lines']:
            #                 print("\t\t\t", l['text'])
            
            if str(k) == "abstract":
                print("\n\n\t" + str(k))
                print("\t\t", product['contents'][k])
            else:
                print("\n\n\t" + str(k))
                print("\t\t\t", product['contents'][k]['free'])
                for s in product['contents'][k]['subsections']:
                    print("\t\t", s[0])
                    print("\t\t\t", s[1])
        """
        pypandoc.convert(product, format="html", to="docx", outputfile="/Users/caguirre97/developer/KDD/html_files/0{}.docx".format(i), extra_args=['-RTS'])
        # print("\n\n")
    return products

# debug()
# main()