import fitz


def make_pages(document):
    """
    Given a document object (from PyMuPDF) it extracts xml representation of the pdf for each page.
    Then transforms xml to json then to a dictionary for easier handling on python and appends the
    dictionary page to a list

    :param document: Document object from PyMuPDF
    :return: list of dictionaries each representing each page of a document
    :rtype: list(dict)
    """
    '''
    document_xml = []
    for i in range(document.pageCount):
        page = document.loadPage(i)
        try:
            page_xml = etree.fromstring(page.getText(output="xml"))
            document_xml.append(page_xml)
        except UnicodeEncodeError:
            print("unicode error")
    return document_xml
    '''
    document_json = []
    for i in range(document.pageCount):
        page = document.loadPage(i)
        try:
            page_xml = page.getText(output="rawdict")
            document_json.append(page_xml)
        except UnicodeEncodeError:
            print("unicode error")
    return document_json


def make_json(document_xml):
    """
    Transforms json format extracted from PyMuPDF to standard format that algorithm can work with. Some
    problems where having '@bbox' instead of just 'bbox' in key values. Also having a list of characters
    instead of just having a string that contains all characters

    :param document_json: list of dictionaries representing each page output from PyMuPDF
    :return: list of dictionaries representing each page that uses a standard format
    """
    page_list = []
    for page in document_xml:
        page_dict = {"width": page["width"], "height": page["height"], "blocks": []}
        try:
            for block in page['blocks']:
                if block['type'] != 0:
                    continue
                block_dict = {
                    'bbox': get_new_bbox(block["bbox"], page_dict['width'], page_dict['height']),
                    'lines': []
                }
                try:
                    for line in block['lines']:
                        line_dict = {
                            'bbox': get_new_bbox(line["bbox"], page_dict['width'], page_dict['height']),
                            'wmode': line['wmode'],
                            'dir': line["dir"],
                            'spans': []
                        }
                        for span in line['spans']:
                            span_dict = {'font': span['font'], 'size': span['size'], 'bbox': [], 'text': ""}
                            for i, c in enumerate(span['chars']):
                                if i == 0:
                                    span_dict['bbox'].append(c['bbox'][0])
                                    span_dict['bbox'].append(c['bbox'][1])
                                if i == len(list(span['chars'])) - 1:
                                    span_dict['bbox'].append(c['bbox'][2])
                                    span_dict['bbox'].append(c['bbox'][3])
                                span_dict['text'] += c['c']
                            span_dict['bbox'] = get_new_bbox(span_dict['bbox'], page_dict['width'], page_dict['height'])
                            line_dict['spans'].append(span_dict)
                        block_dict['lines'].append(line_dict)
                except KeyError:
                    print("Key error while processing block")
                    print(block_dict)
                page_dict['blocks'].append(block_dict)
            page_list.append(page_dict)
        except KeyError:
            print("Key error while processing page: ")
            print(page_dict)
    return page_list


def check_list(obj):
    """
    Checking if the object passed is a list or not. if its a list it just returns it,
    else it creates a list containing just that object.

    :param obj:
    :return:
    """
    if isinstance(obj, list):
        return obj
    else:
        return [obj]


def get_bbox_from_string(string, width, height):
    """
    Given a string containing the bounding box of span, the width of the page and height,
    get the bounding box in form of a list and based of a 100 depending on width and height
    of page

    :param string: string containing the bounding box given by PyMuPDF
    :type string: str
    :param width: number in pixels of width of page
    :type width: float
    :param height: number in pixels of height of page
    :type height: float
    :return: new bounding box in form of a list [x1, y1, x2, y2]
    :type: list(float)
    """
    bbox_string = string.split(" ")
    bbox = []
    for number in bbox_string[0:2]:
        bbox.append(float(number))
    for number in bbox_string[-2:]:
        bbox.append(float(number))
    return get_new_bbox(bbox, width, height)


def get_new_bbox(bbox, width, height):
    """
    Given bbox, width and height, calculate the new coordinates based on a scale of
    100 given the width and height

    :param bbox: bouding box in form of a list given by PyMuPDF
    :type bbox: list(float)
    :param width: number in pixels of width of page
    :type width: float
    :param height: number in pixels of height of page
    :type height: float
    :return: new bounding box in form of a list [x1, y1, x2, y2]
    :type: list(float)
    """
    try:
        x1 = round(bbox[0]*100/float(width), 4)
        x2 = round(bbox[2]*100/float(width), 4)
        y1 = round(bbox[1]*100/float(height), 4)
        y2 = round(bbox[3]*100/float(height), 4)
    except IndexError:
        print(bbox)
    return [x1, y1, x2, y2]


def test():
    file = "/Users/caguirre97/extractor/input/01.pdf"
    doc = fitz.Document(file)
    document_json = make_pages(doc)
    page_list = make_json(document_json)
    for page in page_list:
        print("PAGE:")
        print("width:\t" + str(page['width']))
        print("height:\t" + str(page['height']))
        for block in page["blocks"]:
            print("\tBLOCK:")
            for line in block["lines"]:
                print("\t\tLINE:")
                for span in line["spans"]:
                    print("\t\t\t" + str(span))

