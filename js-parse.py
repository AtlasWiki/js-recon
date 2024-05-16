import re, os, requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import jsbeautifier
import argparse
import colorama

pretty_files = []
get_py_filename = os.path.basename(__file__)
target= ""
file_name = ""
logo = """\u001b[31m

░░░░░██╗░██████╗░░░░░░██████╗░░█████╗░██████╗░░██████╗███████╗
░░░░░██║██╔════╝░░░░░░██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔════╝
░░░░░██║╚█████╗░█████╗██████╔╝███████║██████╔╝╚█████╗░█████╗░░
██╗░░██║░╚═══██╗╚════╝██╔═══╝░██╔══██║██╔══██╗░╚═══██╗██╔══╝░░
╚█████╔╝██████╔╝░░░░░░██║░░░░░██║░░██║██║░░██║██████╔╝███████╗
░╚════╝░╚═════╝░░░░░░░╚═╝░░░░░╚═╝░░╚═╝╚═╝░░╚═╝╚═════╝░╚══════╝
      




--------------------------------------------------------------\u001b[0m"""
class NewlineFormatter(argparse.RawDescriptionHelpFormatter, argparse.ArgumentDefaultsHelpFormatter):
    pass

parser = argparse.ArgumentParser(prog= f"python {get_py_filename}", description='\u001b[96mdescription: parses urls from js files', epilog=
f'''
\u001b[91mbasic usage:\u001b[0m python {get_py_filename } https://youtube.com
\u001b[91msingle file:\u001b[0m python {get_py_filename } https://youtube.com -m
\u001b[91mmulti-file:\u001b[0m python {get_py_filename } https://youtube.com -i   
''', formatter_class=NewlineFormatter, usage=f'{logo}\n\u001b[32m%(prog)s [options] url\u001b[0m')

parser.add_argument("url", help="\u001b[96mspecify url with the scheme of http or https")
parser.add_argument("-s", "--save", help="save prettified js files", action="store_true")
parser.add_argument("-b", "--blacklist", help="blacklist subdomains/domains", nargs="+", default="")
group = parser.add_mutually_exclusive_group()
group.add_argument("-m", "--merge", help="create file and merge all urls into it", action="store_true")
group.add_argument("-i", "--isolate", help="create multiple files and store urls where they were parsed from", action="store_true")
args = parser.parse_args()

print(logo)
target_url = args.url
print('main url: ' + target_url)
def verify_files():

    blacklist = args.blacklist
    custom_bar_format = "\033[32m{desc}\033[0m: [{n}/{total} {percentage:.0f}%] \033[31mCurrent:\033[0m [{elapsed}] \033[31mRemaining:\033[0m [{remaining}] "
    total_items = len(list(extract_files(target_url)))
    
    for js_file in tqdm(extract_files(target_url), desc="Extracted", unit='URL', bar_format=custom_bar_format, total=total_items, position=0, dynamic_ncols=True, leave=True):
       if any(domain in js_file for domain in blacklist):
           print('not extracted: ' + js_file)
           pass
       else:
            if 'http' in js_file or 'https' in js_file:
                if target_url in js_file:
                    print(js_file, flush=True)
                    store_urls(js_file)
            else:
                print(js_file, flush=True)
                store_urls(target_url + js_file)
    if(args.save):
        move_store_files()
        print('saved js files')
        print('done')
    else:
        print("done")
    

def extract_files(url):
    for tags in fetch_html(url):
        try: 
            js_file = tags['src']
            yield js_file
        except KeyError:
            pass


def fetch_html(url):
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246'}
    req=""

    try:
        req = requests.get(url, headers=headers)
        soup = BeautifulSoup(req.content, "html.parser")
        list_tags = soup.find_all('script')
    except ( requests.exceptions.MissingSchema, requests.exceptions.InvalidSchema, requests.exceptions.InvalidURL):
            print(f'NOT FOUND: invalid url, missing, or does not start with http/https protocol in {url}')
            quit()

    req = requests.get(url, headers=headers)
    soup = BeautifulSoup(req.content, "html.parser")
    list_tags = soup.find_all('script')
    return list_tags

def store_urls(url):
    try:
        global target
        global file_name
        target, file_name = re.search("(?:[a-zA-Z0-9-](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9-])?\.)+[a-zA-Z]{2,}", url).group(0), re.search("([^/]*\.js)", url).group(0)
        
        if (args.isolate or args.merge):
            os.mkdir(target)
            os.mkdir(target + '/parsed-urls/')
            if(args.save):
                os.mkdir(target + '/parsed-files/')

    except FileExistsError:
        pass
    except AttributeError:
        pass
   
    for quoted_dir in extract_urls(url):
        try:
            if (args.isolate):
                dir = quoted_dir.strip('"')
                with open(f"{target}/parsed-urls/{file_name}+dirs.txt", "a", encoding="utf-8") as directories:
                    directories.write(dir + '\n')
            elif (args.merge):
                dir = quoted_dir.strip('"')
                with open(f"{target}/parsed-urls/urls+dirs.txt", "a", encoding="utf-8") as directories:
                    directories.write(dir + '\n')
            else:
                dir = quoted_dir.strip('"')
                print(dir)
            

        except FileNotFoundError:
            directory_path = f"{target}/parsed-js/"
            if not os.path.exists(directory_path):
                os.makedirs(directory_path)
            dir = quoted_dir.strip('"')

            if(args.isolate):
                file = open(f"{target}/parsed-js/{file_name}+dirs.txt", "w")
                file.close()
                with open(f"{target}/parsed-js/{file_name}+dirs.txt", "a", encoding="utf-8") as directories:
                    directories.write(dir + '\n')
            if(args.merge):
                file = open(f"{target}/parsed-js/urls+dirs.txt", "w")
                file.close()
                with open(f"{target}/parsed-js/urls+dirs.txt", "a", encoding="utf-8") as directories:
                    directories.write(dir + '\n')

def extract_urls(url):
    req = fetch_js(url)
    absolute_pattern = r'(["\'])(https?://(?:www\.)?\S+?)\1'
    relative_dirs = re.findall('["\'][\w\.\?\-\_]*/[\w/\_\-\s\?\.=]*["\']*', req)
    absolute_urls = re.findall(absolute_pattern, req)
    absolute_urls = [url[1] for url in absolute_urls] 
    all_dirs = relative_dirs + absolute_urls
    unique_dirs = list(dict.fromkeys(all_dirs))
    unique_dirs.sort()
    return unique_dirs

def fetch_js(url):
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246'}
    req = requests.get(url, headers=headers).text
    req = jsbeautifier.beautify(req)
    if(args.save):
        pretty_files.append(url)
        with open(f"pretty-file{len(pretty_files)}.txt", 'w', encoding="utf-8") as prettyJsFile:
            prettyJsFile.write(url + '\n') 
            prettyJsFile.write(req) 
    return req

def move_store_files():
    for prettyfile in range(1, len(pretty_files) + 1):
        source_path = os.getcwd()
        source_filename = f"pretty-file{prettyfile}.txt"
        source_file = os.path.join(source_path, source_filename)
        destination_dir = os.path.join(source_path, f"{target}/parsed-files")
        destination_file = os.path.join(destination_dir, source_filename)
        os.replace(source_file, destination_file)
    
         
if verify_files():
    pass
    