from wenku8 import Wenku8
import threading
import pymongo
import time

# 整体配置
max_thread = 9 + 1
max_bid = 2596
max_uid = 530655
max_rid = 191767

# MongoDB数据库！
client = pymongo.MongoClient()
db = client.wenku8

# Wenku8 的爬虫对象
wk = Wenku8()
wk.login()


def db_book_info(result: dict):
    print(result)
    db.book.insert_one(result)


def db_review_info(result: dict):
    print(result)
    db.review.insert_one(result)


def get_books_info():
    top = 1
    while top <= max_bid:
        # 先开满进程，发现缺了就补
        while len(threading.enumerate()) < max_thread and top <= max_bid:
            t = threading.Thread(target=wk.fetch_book_info, args=(top, db_book_info))
            top += 1
            t.setDaemon(True)
            t.start()
            time.sleep(0.01)


def get_review_info():
    top = 51912
    while top <= max_rid:
        # 先开满进程，发现缺了就补
        while len(threading.enumerate()) < max_thread * 2 and top <= max_rid:
            t = threading.Thread(target=wk.fetch_reviews, args=(top, 0, None, db_review_info))
            top += 1
            t.setDaemon(True)
            t.start()
            time.sleep(0.01)


def main():
    # get_books_info()
    get_review_info()


if __name__ == '__main__':
    main()