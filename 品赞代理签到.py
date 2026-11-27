# 品赞HTTP代理签到
# 账号：环境变量 pzhttp，格式 账号#密码，多账号用换行或 & 分隔；也可直接改下面的 ACCOUNTS
# 推送：环境变量 PUSH_PLUS_TOKEN（可选，pushplus）
# 依赖：pip install requests

import os
import base64
import random
import requests

ACCOUNTS = os.environ.get("pzhttp", "").strip()
PUSH_TOKEN = os.environ.get("PUSH_PLUS_TOKEN", "").strip()

BASE = "https://service.ipzan.com"
TIMEOUT = 30


def headers(token=None, login=False):
    h = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36",
        "Connection": "Keep-Alive",
        "Origin": "https://kip.ipzan.com",
        "Referer": "https://kip.ipzan.com/",
        "Content-Type": "application/json",
    }
    if token and not login:
        h["Authorization"] = "Bearer " + token
    return h


def encode_login(account, password):
    """把账号密码插进随机串里，和网页端一致"""
    raw = "%sQWERIPZAN1290QWER%s" % (account, password)
    encoded = base64.b64encode(raw.encode()).decode()
    rnd = "".join(random.choice("0123456789abcdef") for _ in range(400))
    return (rnd[:100] + encoded[:8] + rnd[100:200] + encoded[8:20]
            + rnd[200:300] + encoded[20:] + rnd[300:400])


def login(account, password):
    try:
        resp = requests.post(
            BASE + "/users-login",
            headers=headers(login=True),
            json={"account": encode_login(account, password), "source": "ipzan-home-one"},
            timeout=TIMEOUT,
        )
        result = resp.json()
        if resp.status_code == 200 and result.get("code") == 0:
            return result.get("data", {}).get("token")
        print("  登录失败:", result.get("message", "未知错误"))
    except Exception as e:
        print("  登录异常:", e)
    return None


def get_balance(token):
    try:
        resp = requests.get(BASE + "/home/userWallet-find", headers=headers(token), timeout=TIMEOUT)
        result = resp.json()
        if resp.status_code == 200 and result.get("code") == 0:
            return result.get("data", {}).get("balance")
        print("  查余额失败:", result.get("message", "token 可能失效"))
    except Exception as e:
        print("  查余额异常:", e)
    return None


def sign_in(token):
    try:
        resp = requests.get(BASE + "/home/userWallet-receive", headers=headers(token), timeout=TIMEOUT)
        result = resp.json()
        if resp.status_code == 200 and result.get("code") == 0:
            return "签到成功: %s" % result.get("data", "")
        msg = result.get("message", "")
        if "已领取" in msg:
            return "本周已签到"
        return "签到失败: %s" % msg
    except Exception as e:
        return "签到异常: %s" % e


def notify(title, content):
    if not PUSH_TOKEN:
        return
    try:
        requests.post(
            "http://www.pushplus.plus/send",
            json={"token": PUSH_TOKEN, "title": title, "content": content, "template": "txt"},
            timeout=TIMEOUT,
        )
    except Exception as e:
        print("推送失败:", e)


def main():
    items = [x.strip() for x in ACCOUNTS.replace("\r", "").replace("&", "\n").split("\n") if x.strip()]
    if not items:
        print("未配置账号：请设置环境变量 pzhttp（账号#密码，多账号用换行或 & 分隔）")
        return

    print("共 %d 个账号" % len(items))
    lines = []
    for i, item in enumerate(items, 1):
        print("[%d] 处理中..." % i)
        if "#" in item:
            account, password = item.split("#", 1)
            token = login(account, password)
            if not token:
                lines.append("[%d] 登录失败" % i)
                continue
        else:
            token = item

        balance = get_balance(token)
        if balance is not None:
            print("[%d] 余额: %s" % (i, balance))
            lines.append("[%d] 余额: %s" % (i, balance))

        msg = sign_in(token)
        print("[%d] %s" % (i, msg))
        lines.append("[%d] %s" % (i, msg))

    notify("品赞签到结果", "\n".join(lines))


if __name__ == "__main__":
    main()
