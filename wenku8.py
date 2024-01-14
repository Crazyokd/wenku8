from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import requests
import os
import time
import urllib3
import argparse
import sys

os.environ['NO_PROXY']="pt.csust.edu.cn" # cancel proxy

baseurl = ''
header = {
    'User-Agent': UserAgent().random
}

volumes = []
title = ''

def request_url(url):
    while True:
        try:
            response = requests.get(url, headers=header)
            if response.status_code == 200:
                return response
            else:
                time.sleep(1.5)
                continue
        except ConnectionResetError | urllib3.exceptions.ProtocolError | requests.exceptions.ConnectionError:
            time.sleep(2)
            continue


def get_contents():
    response = request_url(baseurl)
    current_volume = None

    if response.status_code == 200:
        html_data = response.content

        soup = BeautifulSoup(html_data, 'html.parser')

        # 找到小说名
        global title
        title = soup.find('div', {'id': 'title'}).text.strip()
        # 找到包含章节信息的表格
        chapter_table = soup.find('table', class_='css')


        # 遍历表格中的行
        for row in chapter_table.find_all('tr'):
            # 检查是否为卷标题行
            volume_tag = row.find('td', class_='vcss')
            if volume_tag:
                current_volume = volume_tag.text.strip()
                volumes.append({
                    'volume': current_volume,
                    'chapters': []
                })
                continue

            # 检查是否为章节行
            chapter_tag = row.find('td', class_='ccss')
            while chapter_tag:
                if current_volume:
                    if not chapter_tag.a:
                        break
                    chapter_title = chapter_tag.a.text.strip()
                    chapter_href = chapter_tag.a.get('href', '')
                    volumes[-1]['chapters'].append({
                        'title': f"{chapter_title}",
                        'href': chapter_href
                    })
                chapter_tag = chapter_tag.find_next_sibling('td', class_='ccss')
    else:
        print("network error", response.status_code, response.content)


def print_contents():
    # 输出提取的章节目录
    for volume in volumes:
        for chapter in volume['chapters']:
            print(volume['volume'], chapter)

def create_dir(path:str):
    try:
        os.mkdir(path)
    except FileExistsError:
        pass
    except OSError as error:
        print(f"Creation of directory '{path}' failed: {error}")


def get_chapter():
    valid_request = 1
    while valid_request > 0:
        valid_request = 0
        for volume in volumes:
            create_dir(volume['volume'])
            for chapter in volume['chapters']:
                if (os.path.exists(f"{volume['volume']}/{chapter['title']}.txt")):
                    continue
                time.sleep(2)
                try:
                    response = requests.get(baseurl+chapter['href'], headers=header)
                except ConnectionResetError | urllib3.exceptions.ProtocolError | requests.exceptions.ConnectionError:
                    print("connection error but continue next")
                    continue
                if response.status_code == 200:
                    html_data = response.content
                    with open(f"{volume['volume']}/{chapter['title']}.txt", 'w', encoding='utf-8') as f:
                        f.write(html_data.decode('gbk'))
                    valid_request += 1
                else:
                    print("network error", response.status_code, response.content)


def strip_file(file:str):
    with open(file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    soup = BeautifulSoup(html_content, 'html.parser')

    content_div = soup.find('div', {'id': 'content'})
    contentdp_ul_list = content_div.find_all('ul', {'id': 'contentdp'})
    for contentdp_ul in contentdp_ul_list:
        contentdp_ul.extract()
    # 替换<br>标签为换行
    for br_tag in content_div.find_all('br'):
        br_tag.replace_with('')

    # 替换&nbsp;为空格
    for nbsp_tag in content_div.find_all(string=lambda x: isinstance(x, str) and '&nbsp;' in x):
        nbsp_tag.replace_with(nbsp_tag.replace('&nbsp;', ' '))

    # 输出替换后的文本
    return content_div.get_text().strip()


def synthesize_file():
    book = ''
    for volume in volumes:
        for chapter in volume['chapters']:
            book += f"{volume['volume']} - {chapter['title']}" + '\n\n'
            book += '\t' + strip_file(f"{volume['volume']}/{chapter['title']}.txt") + '\n\n'
    with open(f"{title}.txt", 'w', encoding='utf-8') as f:
        f.write(book)


def fix_baseurl():
    global baseurl
    last_slash_pos = baseurl.rfind('/')
    if last_slash_pos == -1 or last_slash_pos < 1:
        sys.exit("Invalid url, maybe you can try: "
                 "https://www.wenku8.net/novel/2/2542/")
    baseurl = baseurl[:last_slash_pos+1]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
                        prog='wenku8',
                        description='wenku8 crawler',
                        add_help=False,
                        epilog='paste uri and get novel')
    parser.add_argument('-u', '--url',
                        help='the url for the novel catalog',
                        required=True,
                        dest='url')
    parser.add_argument('-h', '--help', action='help',
                        help='show this help message and exit')
    parser.add_argument('-v', '--version', action='version',
                        version='%(prog)s 0.0.1')

    args = parser.parse_args()
    baseurl = args.url

    fix_baseurl()
    
    get_contents()
    print_contents()
    get_chapter()
    synthesize_file()

