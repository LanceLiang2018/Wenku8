from wenku8 import Wenku8
import threading
import pymongo
import time

# 整体配置
max_thread = 5 + 1
max_bid = 2596
max_uid = 530655
max_rid = 191767

# MongoDB数据库！
db = pymongo.MongoClient()
col = db['wenku8']

# Wenku8 的爬虫对象
wk = Wenku8()
wk.login()


def db_book_info(result: dict):
    print(result)


def get_books_info():
    # target_list = list(range(1, max_bid+1, 1))
    threads = []
    top = 1
    while top <= max_bid:
        # 先开满进程，发现缺了就补
        while len(threading.enumerate()) < max_thread and top <= max_bid:
            t = threading.Thread(target=wk.fetch_book_info, args=(top, db_book_info))
            top += 1
            t.setDaemon(True)
            t.start()
            time.sleep(0.01)


def main():
    get_books_info()


if __name__ == '__main__':
    main()