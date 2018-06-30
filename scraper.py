#! python3

import requests, bs4, re
from slugify import slugify

def main():
  # Get name of novel
  print('*' * 30)
  print('novel scraper'.upper().center(30, '*'))
  print('*' * 30)
  print('Enter name:')
  pageURL = f'https://www.novelupdates.com/series/{slugify(input())}'

  # TODO: Try to get the url at novelupdates
  res = getPage(pageURL)
  while not res:
    print("Can't get page url. Enter manually:")
    pageURL = input()
    res = getPage(pageURL)

  # TODO: Get last page at novelupdates

  # TODO: Get chapters

def getPage(pageURL):
  res = requests.get(pageURL)
  try:
    res.raise_for_status()
  except requests.exceptions.HTTPError:
    return None
  return res

if __name__ == '__main__':
    main()