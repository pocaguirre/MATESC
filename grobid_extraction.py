import os 
import subprocess
import xmltodict as xd
from pprint import pprint
import shutil
import ntpath
import json

DATA_STORAGE = "/data/grobid_data"

def _finditem(obj, key):
    if key in obj: return obj[key]
    for k, v in obj.items():
        if isinstance(v,dict):
            item = _finditem(v, key)
            if item is not None:
                return item


def get_directory_base(directory):
    if directory[-1] == "/" or directory[-1] == "\\":
        location = directory[:-1]
    else:
        location = directory
    return ntpath.basename(location)


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


def doi_ref(input_path):
    #os.chdir('/llnl/grobid')
    pdf_list = file_list(input_path)
    for file in pdf_list:
        shutil.copyfile(file, "{}/papers/{}".format(DATA_STORAGE, get_directory_base(file)))
        # print("{}/papers/{}".format(DATA_STORAGE, get_directory_base(file)))
    
    papers_path = DATA_STORAGE + "/papers"
    cmd = 'sudo java -Xmx4G -jar grobid-core/build/libs/grobid-core-0.5.1-SNAPSHOT-onejar.jar -gH grobid-home -dIn %s -dOut /llnl/grobid/output -exe processFullText' % (papers_path, )
    output = subprocess.call(cmd, shell=True)
    result = {}
    path = "/llnl/grobid/output"
    for filename in os.listdir(path):
        if not filename.endswith('.xml'): continue
        fullname = os.path.join(path, filename)
        fl = str(filename).replace('.tei.xml', '')
        with open(fullname) as fd:
            doc = xd.parse(fd.read())
            doi = _finditem(doc, 'idno')
            ref = _finditem(doc, 'listBibl')
        if doi is not None:
            result[fl] = {'DOI': doi['#text'] }
        if ref is not None:
            result[fl].update({'REF' : 'ref' })
    print(result)
    return result

def extract_from_json():
    with open("/llnl/recipes_extractor/metadata_extractor/grobid_extraction.json", "r") as fd:
    #   print(json.load(fd))
       return json.load(fd)

