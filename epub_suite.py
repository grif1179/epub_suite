from zipfile import ZipFile
from bs4 import BeautifulSoup
from time import sleep
from jinja2 import Environment, FileSystemLoader, select_autoescape
import requests
import argparse
import sys
import os
import shutil
import uuid
import textwrap

env = Environment(
    loader=FileSystemLoader('templates'),
    autoescape=select_autoescape()
)

WAIT_TIME = 0.5


class Page:
    'Represents a web-page that is going to be converted into an epub chapter'
    def __init__(self, idx, num, src, link, title):
        self.idx = idx
        self.num = num
        self.src = src
        self.link = link
        self.title = title


def get_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("mode", choices=['r', 'w', 'g'],
                        help=textwrap.dedent('''\
                             What to do to EPUB file given.
                             r -> Print the structure of the epub file.
                             w -> Create an epub file from a folder.
                             g -> Given the url to a table of contents
                                   page uses the links on the page to
                                   generate an epub.'''))
    parser.add_argument("location", help="Name of EPUB file or directory")
    parser.add_argument('-b', '--book', nargs='?', default='Unknown',
                        help='Name of book used in generation')
    parser.add_argument('-a', '--author', nargs='?', default='Unknown',
                        help='Name of author used in generation')
    args = parser.parse_args()

    if args.mode == 'g':
        print("--book and --author must be set if 'g' mode is used.")
        sys.exit(1)

    return args.mode, args.location, args.book, args.author


def read_epub(filename):
    with ZipFile(filename, 'r') as z:
        z.printdir()


def get_all_file_paths(dir_name):
    file_paths = []

    for root, directories, files in os.walk(dir_name):
        for f in files:
            filepath = os.path.join(root, f)
            file_paths.append(filepath)

    return file_paths


def write_epub(dir_name):
    curr_dir = os.getcwd()
    os.chdir(dir_name)

    file_paths = get_all_file_paths('./')
    epub_name = dir_name + '.epub'
    epub_path = os.path.join(curr_dir, epub_name)

    print(f"Adding the following files to EPUB({epub_name}): ")
    with ZipFile(epub_path, 'w') as z:
        for f in file_paths:
            print(f)
            z.write(f)


def generate_epub(url, book, author):
    print(f"Generating {book} by {author}")
    last_slash = (len(url)-1) - url[::-1].find('/')
    base_url = url[:last_slash]
    dir_name = '_'.join(book.split(' ')) + '__BY__' + '_'.join(author.split(' '))
    dir_path = os.path.join('./', dir_name)
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    os.mkdir(dir_name)
    os.mkdir(os.path.join(dir_name, 'META-INF'))

    linkToFile = {}
    uniqueLinks = []
    pages = []
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    anchors = soup.find_all('a')
    for num, anchor in enumerate(anchors):
        link = anchor.get('href')
        if link is None:
            continue

        # Remove hash
        hashLoc = link.find('#')
        if hashLoc != -1:
            link = link[:hashLoc]

        if link not in linkToFile:
            linkToFile[link] = createFileFromLink(link)
            uniqueLinks.append(link)
            filepath = os.path.join(dir_path, linkToFile[link])
            pageId = link[:link.find('.')]
            fullLink = f"{base_url}/{link}"
            pages.append(
                Page(pageId, num+1, linkToFile[link], fullLink, anchor.string))

            with open(filepath, 'w') as f:
                lines = createChapter(fullLink)
                f.write(str(lines))

    # mimetype
    mimetype = 'mimetype'
    env.get_template(mimetype).stream().dump(
        os.path.join(dir_path, mimetype))

    # container.xml
    container = 'META-INF/container.xml'
    env.get_template(container).stream().dump(
        os.path.join(dir_path, container))

    # metadata.opf
    metadata = 'metadata.opf'
    myuuid = uuid.uuid4()
    env.get_template(metadata) \
       .stream(pages=pages, title=book, uuid=str(myuuid), author=author) \
       .dump(os.path.join(dir_path, metadata))

    # toc.ncx
    toc = 'toc.ncx'
    myuuid = uuid.uuid4()
    env.get_template(toc) \
        .stream(pages=pages, title=book, uuid=myuuid) \
        .dump(os.path.join(dir_path, toc))

    write_epub(dir_path)

    print('Generated files')


def createFileFromLink(link):
    if '.' in link:
        index_of_dot = link.find('.')
        return link[:index_of_dot] + '.html'

    return link+'.html'


def createChapter(link):
    r = requests.get(link)
    soup = BeautifulSoup(r.text, 'html.parser')
    body = soup.find('body')
    return body


def main(mode, location, book, author):
    if mode == 'r':
        read_epub(location)
    elif mode == 'w':
        write_epub(location)
    elif mode == 'g':
        generate_epub(location, book, author)
    else:
        print('INVALID MODE GIVEN: ' + mode)
        sys.exit(1)


if __name__ == '__main__':
    mode_arg, loc_arg, book_arg, author_arg = get_args()
    main(mode_arg, loc_arg, book_arg, author_arg)
    print('SUCCESS')
    sys.exit(0)
