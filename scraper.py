#! python3

import requests, bs4, re, sys, pdfkit
from slugify import slugify
from urllib.parse import urljoin

def main():
  # Get name of novel
  print('*' * 30)
  print('novel scraper'.upper().center(30, '*'))
  print('*' * 30)
  print('Enter name:')
  pageURL = f'https://www.novelupdates.com/series/{slugify(input())}/'

  # Try to get the url at novelupdates
  res = getPage(pageURL)
  while not res:
    print("Can't get page url. Enter manually (Type exit to quit):")
    pageURL = input()

    if pageURL.lower() == 'exit':
      sys.exit()

    res = getPage(pageURL)

  # Get last page at novelupdates
  soup = bs4.BeautifulSoup(res.text, 'html.parser')
  pagination = soup.select('.digg_pagination')
  if (pagination):
    lastPage = urljoin(pageURL, pagination[0].contents[-2].get('href'))
    res = getPage(lastPage)
    soup = bs4.BeautifulSoup(res.text, 'html.parser')

  # Get chapters
  # Get all anchors that go out of novelupdates from chapter table
  table = soup.select('#myTable > tbody')[0].find_all(rel='nofollow')
  # Get all href link and order then from first to last
  links = list(map(lambda anchor: f'https:{anchor.get("href")}', table))[::-1]
  res = getPage(links[0])
  soup = bs4.BeautifulSoup(res.text, 'html.parser')
  pdfkit.from_url(links[0], 'out.pdf')

def getPage(pageURL):
  try:
    res = requests.get(pageURL)
  except (requests.exceptions.MissingSchema, requests.exceptions.InvalidSchema) as e:
    print('<Invalid Syntax>')
    return None

  try:
    res.raise_for_status()
  except requests.exceptions.HTTPError:
    return None

  return res

if __name__ == '__main__':
    main()