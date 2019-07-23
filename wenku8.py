from bs4 import BeautifulSoup as Soup
import requests
import requests.cookies
import re
import copy


class Wenku8:

    class NoCopyright(BaseException):
        def __init__(self, *args, **kwargs):
            pass

    def __init__(self):
        self.cookie = {}
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:68.0) Gecko/20100101 Firefox/68.0'

    def login(self, username='LanceTest', password='1352040930'):
        url_login = 'http://www.wenku8.com/wap/login.php'
        payload = {'action': 'login', 'jumpurl': '', 'username': username, 'password': password}
        response = requests.request("POST", url_login, data=payload, headers={'User-Agent': self.user_agent})
        # print(response.text)
        if '密码错误' in response.text:
            self.cookie = {}
            print('密码错误!')
            return False
        c = requests.cookies.RequestsCookieJar()  # 利用RequestsCookieJar获取
        c.set('cookie-name', 'cookie-value')
        response.cookies.update(c)
        self.cookie = response.cookies.get_dict()
        # print(self.cookie)
        print('登陆完成!')
        return True

    def fetch_user_info(self, uid: int, callback=None):
        url_user_info = 'http://www.wenku8.com/wap/userinfo.php?id=%s' % uid
        html = requests.get(url_user_info, cookies=self.cookie, headers={'User-Agent': self.user_agent})
        soup = Soup(html.content, 'html.parser')
        text = soup.getText()
        # print(text)
        try:
            uid = int(re.findall('I D：[0-9]{1,7}', text)[0][4:])
            username = re.findall('用户：.*', text)[0][3:-1]
            nickname = re.findall('昵称：.*', text)[0][3:-1]
            sign_in_time = re.findall('注册：[0-9]{4}-[0-9]{2}-[0-9]{2}', text)[0][3:]
            points = int(re.findall('积分：[0-9]{1,5}', text)[0][3:])
            level = re.findall('等级：.*', text)[0][3:-1]
            sex = re.findall('性别：.*', text)[0][3:-1]
            email = re.findall('邮箱：.*', text)[0][3:-1]
            qq = re.findall('Q Q：[0-9]{0,14}', text)[0][4:]
            if qq == '':
                qq = 0
            else:
                qq = int(qq)
            motto = re.findall('简介：.*', text)[0][3:-1]
        except ValueError or IndexError as e:
            print("Error Occurs:", e)
            return None
        result = {
            'uid': uid,
            'username': username,
            'nickname': nickname,
            'sign_in_time': sign_in_time,
            'points': points,
            'level': level,
            'sex': sex,
            'email': email,
            'qq': qq,
            'motto': motto,
        }
        if callback is not None:
            callback(result)
            return None
        return result

    def fetch_book_info(self, bid: int, callback = None):
        url_book_info = 'http://www.wenku8.com/wap/article/articleinfo.php?id=%s' % bid
        html = requests.get(url_book_info, cookies=self.cookie, headers={'User-Agent': self.user_agent}).text
        soup = Soup(html, 'html.parser')
        text = soup.getText()
        # text = text.encode('utf8').decode('gbk', errors='ignore')
        # text = text.encode('gbk').decode('utf8')
        # text = text.encode("utf-8").decode('utf-8','ignore')
        text = text.replace('\r', '').replace('\u3000', '')
        if '对不起，该文章不存在' in text:
            return None
        # print(text)

        author = None
        sortlist = None
        brief = None
        title = None
        try:
            # author = soup.find_all('anchor')[0].get_text()
            title = re.findall('全本\.\n新书\n.+', text)[0][7:]
            author = re.findall('作者:.+', text)[0][3:].replace('\r', '')
            sortlist = Soup(re.findall('<a href="sortlist.php.+?/>', html)[0], 'html.parser').get_text()
            # brief = print(re.findall('\[作品简介\][\s\D]*联系管理员', text)[0][8:-7])
            brief = re.findall('\[作品简介\][\s\D]*联系管理员', text)
            if len(brief) != 0:
                brief = brief[0][8:-7]
            else:
                brief = text.split('[作品简介]')[-1].split('联系管理员')[0]
                # print("ERR, TRY:", brief)
            if '因版权问题，文库不再提供该小说的在线阅读与下载服务' in text:
                raise self.NoCopyright
            has_copyright = True
            status = re.findall('状态:.*', text)[0][3:].replace('\r', '')
            size = re.findall('字数:[0-9]+?字', text)
            if len(size) == 0:
                size = 0
            else:
                size = int(size[0][3:-1])
            update = re.findall('更新:[0-9]{2,4}-[0-9]{2}-[0-9]{2}', text)
            if len(update) == 0:
                update = 0
            else:
                update = update[0][3:]
            p_f = re.findall('[0-9]+?推 有[0-9]+?位会员关注', text)
            if len(p_f) == 0:
                push, follow = 0, 0
            else:
                push, follow = p_f[0].split('推 有')
                push = int(push)
                follow = int(follow[:-5])
        except self.NoCopyright:
            status = '无版权'
            size = None
            update = None
            push = None
            follow = None
            has_copyright = False
            result = {
                'id': bid,
                'title': title,
                'author': author,
                'sortlist': sortlist,
                'status': status,
                'size': size,
                'update': update,
                'push': push,
                'follow': follow,
                'brief': brief,
                'has_copyright': has_copyright,
            }
            if callback is not None:
                callback(result)
                return None
            return result
        except IndexError or ValueError as e:
            print('(bid=%s)Error Occurs:' % bid, e)
            # print('Err TEXT:', text)
            return None
        result = {
            'id': bid,
            'title': title,
            'author': author,
            'sortlist': sortlist,
            'status': status,
            'size': size,
            'update': update,
            'push': push,
            'follow': follow,
            'brief': brief,
            'has_copyright': has_copyright,
        }
        if callback is not None:
            callback(result)
            return None
        return result

    def fetch_reviews(self, rid: int, page: int = 1, appending = None, callback = None):
        url_fetch_reviews = 'http://www.wenku8.com/wap/article/reviewshow.php?rid=%s&page=%s' % (rid, page)
        html = requests.get(url_fetch_reviews, cookies=self.cookie, headers={'User-Agent': self.user_agent}).text
        soup = Soup(html, 'html.parser')
        text = soup.getText()
        if '对不起，该评论或文章不存在' in text:
            print("(rid=%s)ERR: 该评论或文章不存在" % rid)
            return None
        text = text.replace('\r', '')
        # print(html)
        review_one = {
            'username': '', 'content': '', 'time': '',
        }

        try:
            title = re.findall('《.+?》书评', text)[0][1:-3]
            subject = re.findall('主题：.+', text)[0][3:]
            # content = re.findall('<a href="http://www.wenku8.com/wap/userinfo.php.[\s\D]+\]', html)
            # content = re.findall('[0-9]{4}-[0-9]{2}-[0-9]{2}', html)
            content = re.findall('<a href=.+[\s\D]*\[[0-9]{4}-[0-9]{2}-[0-9]{2}\]<br/>', html)
            # print(content)

            reviews = []
            for review_html in content:
                # print('review_html:', review_html)
                username = re.findall('>.*?</a>', review_html)[0][1:-4]
                review = re.findall('</a>:\r\n.+[\s\D]*.+?<br/>', review_html)
                if len(review) == 0:
                    return None
                review = review[0]
                review_content = review[7:-19]
                # 过滤一下
                # filters = ['<br />', '<br/>', '\r']
                # for f in filters:
                #     review_content = review_content.replace(f, '')
                review_time = re.findall('[0-9]{4}-[0-9]{2}-[0-9]{2}', review)[0]
                review_content = Soup(review_content, 'html.parser').get_text()
                # print(review_content, review_time)
                review_one['username'] = username
                review_one['content'] = review_content
                review_one['time'] = review_time
                reviews.append(copy.deepcopy(review_one))

            pages = re.findall('到第页跳转<<[ {2}?0-9]+? \[[0-9]+?/[0-9]+?\]', text)[0]
            page_total = int(pages.split('/')[-1][:-1])
            # print(page_total)
        except IndexError or ValueError as e:
            print('Error Occur:', e)
            return None

        if type(appending) is dict and 'reviews' in appending \
                and type(appending['reviews']) is list:
            reviews.extend(appending['reviews'])

        result = {
            'id': rid,
            'title': title,
            'subject': subject,
            'reviews': reviews,
        }
        if page < page_total:
            self.fetch_reviews(rid, page=page+1, appending=result)
        if callback is not None:
            callback(result)
            return None
        return result


if __name__ == '__main__':
    wk = Wenku8()
    wk.login()
    # print(wk.fetch_user_info(530523))
    # print(wk.fetch_reviews(119246))
    print(wk.fetch_user_info(405019))
