# coding=gbk
import requests
from bs4 import BeautifulSoup
import re
import os
import json
from time import sleep


_douban_url = "http://www.douban.com/"
_douban_note = re.compile(r"http://www.douban.com/note/\d+/")
_douban_people = re.compile(r"http://www.douban.com/people/.+/")
_session = None
_cookie_name = 'douban_cookie.json'


def _init():
    global _session
    if _session is None:
        _session = requests.session()
        if os.path.exists(_cookie_name):
            cookie = open(_cookie_name,'r')
            _session.cookies.update(json.load(cookie))
        else:
            print("未登录")
            login()
    else:
        print("不要重复运行")


def get_path(file_path, file_name, mode, dpath, dname):
    if file_path is None:
        file_path = dpath
    if file_name is None:
        file_name = dname
    if os.path.isdir(file_path) is False:
        os.makedirs(file_path)
    return (os.path.join(file_path, file_name.strip())+'.'+mode)


class Note():


    def __init__(self, url, note_title = '', note_author = ''):
        self.url = url
        self.bs()


    def bs(self):
        global _session
        try:
            self.bs = BeautifulSoup(_session.get(self.url).content)
        except Exception as err:
            print("正在修复:"+err)
        finally:
            sleep(1)
            self.bs()

    @property
    def html(self):
        return self.bs.prettify()

    @property
    def title(self):
        return self.bs.find('h1').text

    @property
    def content(self):
        return self.bs.find(id = "link-report")

    @property
    def author(self):
        return self.bs.find(class_ = "note-header note-header-container").find(class_ = "note-author").text

    @property
    def time(self):
        return self.bs.find('span',class_ = "pl").text


    def save(self, mode = "html", file_path = None, file_name = None):
        if mode not in ["html","md"]:
            return
        path = get_path(file_path,
                        file_name,
                        mode,
                        os.getcwd() + "\\note",
                        self.title + '-' + self.author )
        self.process()
        with open(path, 'wb') as f:
            if mode is "html":
                f.write(self.final.encode('utf-8'))
            else:
                import html2text
                h2t = html2text.HTML2Text()
                h2t.body_width = 0
                f.write(h2t.handle(self.final).encode('utf-8'))


    def process(self):
        content = self.bs.new_tag('meta')
        content['http-equiv'] = 'Content-Type'
        content['content'] = "text/html; charset=utf-8"
        # imgs = self.bs.find_all('img')
        # for each in imgs:
        #     new = self.bs.new_tag("a")
        #     new['href'] = each['src']
        #     new.string = "图片"
        #     each.replace_with(new)
        # comment = self.bs.find('div',class_ = "comment-form txd")
        # comment.extract()
        ul = self.bs.find('h2')
        ul.extract()
        content.append(self.bs.find('div', class_ = "article"))
        style = self.bs.find_all('style')
        for each in style:
            content.append(each)
        links = self.bs.find_all('link',type = "text/css")
        for each in links:
            content.append(each)
        scripts = self.bs.find_all('script')
        for each in scripts:
            each.extract()
        self.final = content.prettify()


class People():


    def __init__(self,url):
        self.url = url
        self.bs()


    def bs(self):
        global _session
        try:
            self.bs = BeautifulSoup(_session.get(self.url).content)
        except Exception as err:
            print("正在修复："+err)
        finally:
            sleep(1)
            #self.bs()

    @property
    def name(self):
        pro = self.bs.find('div',id = "db-usr-profile").find('h1').text
        m = re.match(r'\n(.+)\n.+(.+).+',pro)
        return m.group(1).strip()

    @property
    def motto(self):
        return self.bs.find('div',id = "db-usr-profile").find('span').text

    @property
    def notes(self):
        try:
            ns = BeautifulSoup(_session.get(self.url+"notes/").content)
            pages = ns.find(class_="paginator").find_all('a')
            max = 0
            for each in pages:
                num = each.text.strip()
                if num.isnumeric():
                    if max < int(num):
                        max = int(num)
            for i in range(0, max - 1):
                page = BeautifulSoup(_session.get(self.url+"notes/?start=" + str(i*10) + "&type=note").content)
                notes_urls = page.find_all('div',class_ = "note-header-container")
                for each in notes_urls:
                    yield Note(each.find('a')['href'])
        except Exception as err:
            print("正在修复："+err)
        finally:
            sleep(1)
            self.notes()

    @property
    def broadcasts(self):
        page = BeautifulSoup(_session.get(self.url + "statuses/").content)
        while True:
            bds = page.find_all('div', class_ = "status-item")
            if len(bds) == 0:
                break
            for each in bds:
                yield Broadcast(each)


def login():
    global _session
    email = input("请输入邮箱")
    pswd = input("请输入密码")
    data = {'form_email':email,
            'form_password':pswd,
            'remember':True}
    response = requests.post(_douban_url,data)
    with open(_cookie_name,'w') as c:
        json.dump(response.cookies.get_dict(),c)
    return 1


class Broadcast():


    def __init__(self, bs):
        self.bs = bs


    #def save(self):
    #     return self.final
        # if mode not in ['html', 'md']:
        #     return
        # path = get_path(file_path,
        #                 file_name,
        #                 mode,
        #                 os.getcwd() + "\\broadcasts",
        #                 self.time + '-' + self.author )
        # self.process()
        # with open(path, 'wb') as f:
        #     if mode is 'html':
        #         f.write(self.final.encode('utf-8'))
        #     else:
        #         import html2text
        #         h2t = html2text.HTML2Text()
        #         h2t.body_width = 0
        #         f.write(h2t.handle(self.final).encode('utf-8'))

    @property
    def author(self):
        return self.bs.find('div',class_ = "text").a.text.strip()

    @property
    def time(self):
        return self.bs.find('span',class_ = "created_at")['title']

    @property
    def final(self):
        content = self.bs.new_tag('meta')
        content['http-equiv'] = 'Content-Type'
        content['content'] = "text/html; charset=utf-8"
        content.append(self.bs)
        return content.prettify()


def save_broadcasts(p, mode = 'md', file_path = None, file_name = None):
    if mode not in ['html', 'md']:
        return 
    path = get_path(file_path,
                        file_name,
                        mode,
                        os.getcwd() + "\\broadcasts",
                        p.name )
    with open(path, 'ab') as f:
        if mode is 'html':
            for each in p.broadcasts:
                f.write(each.final.encode('utf-8'))
        else:
            import html2text
            h2t = html2text.HTML2Text()
            h2t.body_width = 0
            for each in p.broadcasts:
                f.write(h2t.handle(each.final).encode('utf-8'))

