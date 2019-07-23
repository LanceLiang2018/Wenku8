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
    return string


def review2epub_all(order=-1):
    bid_start, bid_stop = 1, 2596
    book = epub.EpubBook()
    # 目录管理
    toc = []
    # 主线
    spine = ['cover', 'nav']
    # 使用网站封面
    with open('logo.jpg', 'rb') as f:
        data_cover = f.read()
    g_title = 'Wenku8评论整合'
    author = 'wenku8.net'
    book.set_identifier("%s, %s" % (g_title, author))
    book.set_title(g_title)
    book.add_author(author)
    book.set_cover('cover.jpg', data_cover)
    for bid in trange(bid_start, bid_stop+1, 1):
        title = bid2book(bid)
        reviews = get_reviews(title=title, order=order)
        if reviews is None:
            continue
        reviews = list(reviews)
        # print(reviews)
        volume_text = title
        toc.append((epub.Section(volume_text), []))
        volume = epub.EpubHtml(title=volume_text, file_name='%s.html' % bid)
        volume.set_content(utf8_save("<h1>%s</h1><br>" % volume_text).encode())
        book.add_item(volume)
        for review in reviews:
            page = epub.EpubHtml(title=review['subject'], file_name='%s.xhtml' % review['id'])
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
    epub.write_epub(os.path.join('.', '%s - %s.epub' % (g_title, author)), book)


if __name__ == '__main__':
    # print(list(get_reviews(bid=1)))
    review2epub_all()
