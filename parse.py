import pymongo
from ebooklib import epub
from tqdm import trange
import os


# MongoDB数据库
client = pymongo.MongoClient()
db = client.wenku8


def book2bid(title: str):
    data = db.book.find_one({'title': title}, {'_id': 0})
    if data is None:
        return None
    return data['id']


def bid2book(bid: int):
    data = db.book.find_one({'id': bid}, {'_id': 0})
    if data is None:
        return None
    return data['title']


def get_reviews(bid: int = None, title: str = None, order=-1):
    if bid is None and title is None:
        return None
    if bid is not None:
        title = bid2book(bid)
    # if title is not None:
    #     bid = book2bid(title)
    return db.review.find({'title': title}, {'_id': 0}).sort([('id', order)])


def review2text(review: dict):
    result = ''
    for r in review['reviews']:
        one = '[{time}]<br>{username}:{content}'.format(
            time=r['time'], username=r['username'], content=r['content']
        )
        result += '%s<br>' % one
    return result


def utf8_save(string: str):
    temp = string.encode()
    string = temp.decode("UTF8", errors='ignore')
    if string == '':
        string = '_'
    # ValueError: All strings must be XML compatible:
    # Unicode or ASCII, no NULL bytes or control characters
    return string


def review2epub_all(bid_start=1, bid_stop=2596, order=-1):
    # bid_start, bid_stop = 1, 2596
    book = epub.EpubBook()
    # 目录管理
    toc = []
    # 主线
    spine = ['cover', 'nav']
    # 使用网站封面
    with open('logo.jpg', 'rb') as f:
        data_cover = f.read()
    if bid_start == bid_stop:
        g_title = bid2book(bid_start)
        range_ = range
    else:
        g_title = 'Wenku8评论整合'
        range_ = trange
    author = 'wenku8.net'
    book.set_identifier("%s, %s" % (g_title, author))
    book.set_title(g_title)
    book.add_author(author)
    book.set_cover('cover.jpg', data_cover)
    for bid in range_(bid_start, bid_stop+1, 1):
        # 这个地方有错误
        if bid == 1024:
            continue
        title = bid2book(bid)
        reviews = get_reviews(title=title, order=order)
        if reviews is None:
            continue
        reviews = list(reviews)
        # print(reviews)
        volume_text = utf8_save(title)
        toc.append((epub.Section(volume_text), []))
        volume = epub.EpubHtml(title=volume_text, file_name='%s.html' % bid)
        volume.set_content(utf8_save("<h1>%s</h1><br>" % volume_text).encode())
        book.add_item(volume)
        for review in reviews:
            page = epub.EpubHtml(title=utf8_save(review['subject']), file_name='%s.xhtml' % review['id'])
            review_content = review2text(review)
            # print(review_content)
            page_content = '{主题:%s}<br>%s' % (review['subject'], review_content)
            page.set_content(utf8_save(page_content))
            book.add_item(page)
            toc[-1][1].append(page)
            spine.append(page)
        # break
    book.toc = toc
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = spine
    path = 'reviews/'
    if bid_start == bid_stop:
        path = '.'
    epub.write_epub(os.path.join(path, '%s-%s.epub' % (g_title, author)), book)


def review2epub_split():
    bid_start, bid_stop = 1, 2596
    for bid in trange(bid_start, bid_stop+1, 1):
        try:
            review2epub_all(bid, bid)
        except ValueError:
            print('ValueError: bid=%s' % bid)


# 不需要的用户的特点：
# [username == nickname], points == 10,
# sex == '保密', email == '', qq == 0, motto == ''
def user_clean():
    db.user2.drop()
    total = db.user.find({
        'points': {'$gt': 10},
        # 'sex': {'$ne': '保密'},
        # 'email': {'$ne': ''},
        # 'qq': {'$ne': 0},
        # 'motto': {'$ne': ''},
    }).count()
    it = db.user.find({
        'points': {'$gt': 10},
        # 'sex': {'$ne': '保密'},
        # 'email': {'$ne': ''},
        # 'qq': {'$ne': 0},
        # 'motto': {'$ne': ''},
    }, {'_id': 0}).__iter__()
    for _ in trange(total):
        try:
            data = it.__next__()
            # print(data)
            # return
            db.user2.insert(data)
        except StopIteration:
            break


def count_user_date():
    total = db.user2.find({'sign_in_time': {'$gt': '2017-03-16'}}).count()
    size = 1000
    last = None
    for t in range(1, total, size):
        it = db.user2.find({'sign_in_time': {'$gt': '2017-03-16'}}, {'_id':0, 'sign_in_time':1}).sort([('sign_in_time', 1)]).limit(size).skip(t).__iter__()
        # for data in db.user2.find({}, {'_id':0, 'sign_in_time':1}).sort({'sign_in_time':1}):
        while True:
            try:
                data = it.__next__()
                date = data['sign_in_time']
                if date == last:
                    continue
                print(date, end=':')
                count = db.user2.find({'sign_in_time': date}).count()
                print(count)
                last = date
                db.result_user_date.insert({'date': date, 'count': count})
            except StopIteration:
                break


if __name__ == '__main__':
    # print(list(get_reviews(bid=1)))
    # review2epub_split()
    # user_clean()
    # count_user_date()
    review2epub_all()
