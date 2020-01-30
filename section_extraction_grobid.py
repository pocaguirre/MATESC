"""
Script to extract sections from grobid's 
xml output. 

"""

from bs4 import BeautifulSoup as bs4
import json 
import os

def sections(file):
    """
    name: sections - extract sections from grobid's output
    param: file - file containing grobid's output (xml)
    type: file - string path to xml file
    return: writes a json file containing sections
    """
    jd = {}
    with open(file) as fp:
        content = bs4(fp, "html.parser")
        
        # Get title
        for link in content.find_all('title'):
            try:
               link['type']
               if link['type'] == 'main':
                  jd['Title'] = link.text
                  break
            except:
               pass
        
        # Get Authors
        authors = ''
        for author in content.find_all('author'):
            if author.parent.parent.parent.name.upper() == 'SOURCEDESC':
               authors += author.text.replace('\n','') + " , "
        jd['Authors'] = authors
        
        # Get Abstract
        jd['Abstract'] = content.find('abstract').text


        # Get Sections
        for link in content.find_all('head'):
          try:
              link.contents[0].upper().find('FIGURE')
              k = link.text
              text = ''
              while link.next_sibling is not None:
                 text += link.next_sibling.text + " "
                 link = link.next_sibling
              jd[k] = text
          except:
              pass
    # Write json file
    with open(file + ".json", 'w') as jf:
        jf.write(json.dumps(jd))


def main():
  """
  Loop through every xml file to extract in the current directory
  """
  indir = os.getcwd()
  for root, dirs, filenames in os.walk(indir):
    for f in filenames:
        if f.endswith('.xml'):
            sections(f)
            
main()
