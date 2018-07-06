#! python3

import requests, bs4, re, sys, pdfkit, PyPDF2, webbrowser
from os import remove, path
from slugify import slugify
from urllib.parse import urljoin
from functools import reduce

def main():
  # Get name of novel
  print('*' * 30)
  print('novel scraper'.upper().center(30, '*'))
  print('*' * 30)
  print('Enter name:')
  novel_name = input()
  page_url = f'https://www.novelupdates.com/series/{slugify(novel_name)}/'

  # Try to get the url at novelupdates
  novelupdates = get_page(page_url)
  while not novelupdates:
    print("Can't get page url. Enter manually (Type exit to quit):")
    page_url = input()

    if page_url.lower() == 'exit':
      sys.exit()

    novelupdates = get_page(page_url)
  
  # Number of chapters to write
  print('Number of chapters ("ALL" for all):')
  chapters_length = input()
  if chapters_length.lower() == 'all':
    # Some large number in which there will never be this many pages
    chapters_length = 10000
  else:
    chapters_length = int(chapters_length) 
  current_chapter = 0 

  # Get last page at novelupdates
  soup = bs4.BeautifulSoup(novelupdates.text, 'html.parser')
  pagination = soup.select('.digg_pagination')
  if (pagination):
    last_page = urljoin(page_url, pagination[0].contents[-2].get('href'))
    novelupdates = get_page(last_page)
    soup = bs4.BeautifulSoup(novelupdates.text, 'html.parser')


  title_path = body_path = None
  new_title = new_body = False
  chapters = []
  while current_chapter < chapters_length:
    # Get chapters
    # Get all anchors that go out of novelupdates from chapter table
    table = soup.select('#myTable > tbody')[0].find_all(rel='nofollow')
    # Get all href link and order then from first to last
    chapter_num = list(map(lambda anchor: anchor.contents[0], table))[::-1]
    links = list(map(lambda anchor: f'https:{anchor.get("href")}', table))[::-1]

    # Download each chapter and write to individual pdf
    for index, link in enumerate(links):
      print('Getting ' + chapter_num[index])
      res = get_page(link)

      soup = bs4.BeautifulSoup(res.text, 'html.parser')

      if current_chapter == 0:
        # Get css from webpage to write to pdf
        write_css(urljoin(res.url, soup.select('link[rel=stylesheet]')[0].get('href')))
        webbrowser.open(res.url, new=2)
      
      title = para = para2 = title_parent = body_parent = None
      # Get css selector path to title
      while not title_parent:
        if not title_path:
          print('Paste chapter title ("->" to skip): ')
          title = input().strip('\n')
          if not title or title == '->':
            title_parent = '<span></span>'
            title_path = 'skip'
            break
          # title = 'The end of the first and second time'
          try:
            title_parent = soup.find(text=re.compile(f'^{title}$')).parent
          except AttributeError:
            print('<Cannot find title> Try inputing a different title or skipping')
          if title_parent:
            title_path = get_css_path(title_parent)
        elif title_path == 'skip':
          break
        else:
          title_parent = soup.select_one(title_path)
          if not title_parent:
            title_path = None
            new_title = True
            print(f'Open: {res.url}')
      # Get css selector path to text
      while not body_parent:
        if not body_path:
          print('Paste first sentence: ')
          para = input().strip('\n')
          # para = 'The ship that the students of Yasaka High School were on for their field trip sank due to a bomb planted by terrorists.'
          print('Paste last sentence: ')
          para2 = input().strip('\n')
          # para2 = 'With no time to object to Rodcorte’s undesirable promise, Hiroto’s mind went blank.'

          if not para or not para2:
            print('<Input cannot be empty>')
            para = para2 = None
            continue

          # Find the closest parent between two nodes para and para2 
          body_parent = get_common_parent(soup, para, para2)
          if body_parent:
            body_path = get_css_path(body_parent)
        else:
          body_parent = soup.select_one(body_path)
          if not body_parent:
            body_path = None
            new_body = True
            print(f'Open: {res.url}')

      # new_title and new_body is true then assume new webpage/translator so download new css
      if new_title and new_body:
        write_css(urljoin(res.url, soup.select('link[rel=stylesheet]')[0].get('href')))
      new_title = new_body = False
        

      # print('title path: ' + title_path)
      # print('body path: ' + body_path)
      # assert title_parent == soup.select(title_path)[0]
      # assert body_parent == soup.select(body_path)[0]

      chapter = f'''
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="utf-8">
      </head>
      <body>
      <h1>{chapter_num[index]}</h1>
      {str(title_parent)}
      {str(body_parent)}
      <body>
      </html>
      '''

      pdfkit.from_string(chapter, f'{current_chapter}.pdf', css=path.abspath('style.css'))

      chapters.append(f'{current_chapter}.pdf')

      current_chapter += 1

      print('Current chapter: ' + str(current_chapter))

      if not current_chapter < chapters_length:
        break

    if current_chapter < chapters_length:
      # Get next page in pagination
      soup = bs4.BeautifulSoup(novelupdates.text, 'html.parser')
      current_page = soup.select('.digg_pagination > em')[0]
      if (current_page.previous_sibling):
        next_page = urljoin(page_url, current_page.previous_sibling.get('href'))
        novelupdates = get_page(next_page)
        soup = bs4.BeautifulSoup(novelupdates.text, 'html.parser')
      else:
        break

  # Pdf name
  print(f'File name (press enter for default - {novel_name}):')
  temp = input()
  if temp.strip():
    novel_name = temp

  # chapters = []
  # for chapter in range(14):
  #   chapters.append(f'{chapter}.pdf')

  # Merge chapters into novel pdf
  merge_pdfs(chapters, novel_name)

  # Remove helper files
  remove('style.css')
  for chapter in chapters:
    remove(chapter)

  print('Open pdf? (y/n)')
  open_pdf = input().lower()
  if open_pdf == 'y':
    webbrowser.open(path.abspath(f'{novel_name}.pdf'))

def get_page(page_url):
  try:
    res = requests.get(page_url)
  except (requests.exceptions.MissingSchema, requests.exceptions.InvalidSchema) as e:
    print('<Invalid Syntax>')
    return None

  try:
    res.raise_for_status()
  except requests.exceptions.HTTPError:
    return None

  return res

def write_css(css_url):
  css = re.sub('@import[^;]+;', '', requests.get(css_url).text)

  with open('style.css', 'w') as css_file:
    css_file.write(css)

# Extract css path of node https://stackoverflow.com/questions/25969474/beautifulsoup-extract-xpath-or-css-path-of-node
def get_element(node):
  def check_of_same_type(count, sibling):
      if sibling.name == node.name:
          count += 1
      return count
  siblings = list(node.previous_siblings)
  length = reduce(check_of_same_type, siblings, 0) + 1
  if (length) > 1:
    return f'{node.name}:nth-of-type({length})'
  else:
    return node.name

def get_css_path(node):
  path = [get_element(node)]
  for parent in node.parents:
    if parent.name == '[document]':
      break
    path.insert(0, get_element(parent))
    if parent.name == 'body':
      break
  return ' > '.join(path)

# https://stackoverflow.com/questions/17786301/beautifulsoup-lowest-common-ancestor
def get_common_parent(soup, node1, node2):
  try:
    link_1_parents = list(soup.find(text=re.compile(node1)).parents)[::-1]
    link_2_parents = list(soup.find(text=re.compile(node2)).parents)[::-1]

    body_parent = [x for x,y in zip(link_1_parents, link_2_parents) if x is y][-1]
    return body_parent
  except AttributeError:
    print('<Cannot find common parent> Try inputing again with a substring of the sentence')
    return False

def merge_pdfs(chapters, name):
  pdfs = []
  pdfWriter = PyPDF2.PdfFileWriter()
  for index, chapter in enumerate(chapters):
    pdfs.append(open(chapter, 'rb'))
    chapter_reader = PyPDF2.PdfFileReader(pdfs[index])
    for page in range(chapter_reader.numPages):
      pdfWriter.addPage(chapter_reader.getPage(page))
  
  with open(f'{name}.pdf', 'wb') as novel:
    pdfWriter.write(novel)
  
  for pdf in pdfs:
    pdf.close()
  

if __name__ == '__main__':
    main()