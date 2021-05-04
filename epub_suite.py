from zipfile import ZipFile
import argparse
import sys
import os

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", help="What to do to EPUB file given")
    parser.add_argument("location", help="Name of EPUB file or directory")
    args = parser.parse_args()

    return args.mode, args.location


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


def main(mode, location):
    if mode == 'r':
        read_epub(location)
    elif mode == 'w':
        write_epub(location)
    else:
        print('INVALID MODE GIVEN: ' + mode)
        sys.exit(1)


if __name__ == '__main__':
    mode_arg, loc_arg = get_args()
    main(mode_arg, loc_arg)
    print('SUCCESS')
    sys.exit(0)
