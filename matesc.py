from content_extraction import extract, file_list
import argparse
import json
'''
Section Extraction using Metadata

    This extractor focuses on using metadata as the main feature. We get metadata from a python library
    called PyMuPDF (fitz). The input of the algorithm is a pdf file and a list of common words that should
    be ignored ( usually these words are located in the headers ). This is the controller file that gives the
    linear structure of the algorithm.
'''


def get_parser():
    par = argparse.ArgumentParser(description="Section Extraction Using Metadata")
    par.add_argument('-input', nargs='+', required=True, help='path to pdf file(s) to extract data from')
    par.add_argument('-output', type=str, default='./', help='output folder')
    par.add_argument('-output_type', type=str, default='json', help='output type ["json", "html", "docx"]')
    par.add_argument('-subsections', action='store_true', help='extract subsections')
    return par


if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()
    pdfs = []
    for path in args.input:
        pdfs += file_list(path)
    for f in pdfs:
        name = f.split("/")[-1][:-4]
        product = extract(f, subsections=args.subsections, output=args.output_type)
        with open(args.output+"/"+name+"."+args.output_type, "w") as w:
            if args.output_type == "json":
                json.dump(product, w)
            else:
                w.write(product)