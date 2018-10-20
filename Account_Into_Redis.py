import re
import redis

db_account = redis.StrictRedis(host='127.0.0.1', port=6379, db=3, decode_responses=True)


def user_pass_item():
    itemname = insert_account()
    usernames, passwords = get_from_redis()
    account = list(zip(usernames, passwords))
    for k, v in account:
        info = (k, v, itemname)
        yield info


def insert_account():
    """
    读取文件，往redis插入用户名和密码
    """
    with open('weibo.txt', 'r') as f:
        print('正在读取txt文件')
        accounts = f.readlines()
        itemname = f.name.replace('.txt', '')

    for account in accounts:
        # if re.mat
        username = re.search('(.*?)----', account.strip(), re.S).group(1)
        password = re.search('----(.*)', account.strip(), re.S).group(1)
        db_account.hset('account:' + itemname, username, password)
        print('用户:{0},密码:{1}入库成功'.format(username, account))
    return itemname


def get_from_redis():
    """
    从redis读取用户名和密码
    """
    usernames = db_account.hkeys('account:weibo')
    passwords = db_account.hvals('account:weibo')
    return usernames, passwords


if __name__ == '__main__':
    user_pass_item()
