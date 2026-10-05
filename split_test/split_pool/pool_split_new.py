"""
pool_split.py —— 每日瓜分奖池的分账逻辑

这是我们线上「每日瓜分奖池」的真实代码，为这道题做了简化
（去掉了数据库读写和日期处理，只留下算钱的部分）。

背景：
  平台每天放一个奖池。当天达标的用户，按各自的贡献权重瓜分池子里的钱。

约定：
  · 所有金额都是整数「分」，系统里不存在半分钱。
  · weights 是每个人的贡献权重（线上用的是「合格采集秒数」）。

硬规则（产品定的，不能破）：
  分完之后，所有人拿到的钱加起来必须【正好等于】池子总额。
  多一分 = 平台凭空多发了钱。
  少一分 = 有人的钱卡在系统里没发出去。
"""


def split_pool(pool_cents: int, weights: list[int]) -> list[int]:
    """把 pool_cents 按 weights 的比例分给每个人，返回每人拿到多少分。

    返回列表与 weights 一一对应。

    实现采用最大余数法,保证对任意合法输入，返回值之和恒等于 pool_cents：
      1. 全程整数运算，先按 floor(pool_cents * w / total) 分配基础份额；
      2. 差额 remainder = pool_cents - sum(base) 必落在 [0, n-1]；
      3. 按小数余数(pool_cents * w) % total 从大到小排序，
         把差额逐分补给排在最前面的 remainder 个人。
    """
    if not weights:
        return []
    if any(w < 0 for w in weights):
        raise ValueError("weights 不能为负数")
    total = sum(weights)
    if total == 0:
        raise ValueError("weights 之和必须大于 0，无法瓜分")

    # 1) 保证发的钱是整数
    shares = [pool_cents * w // total for w in weights]

    # 2) 差额 = 还没分出去的分，范围 [0, len(weights) - 1]
    remainder = pool_cents - sum(shares)
    if remainder:
        # 3) 小数余数越大代表越接近进位，优先把差额补给小数余数最大的人
        order = sorted(
            range(len(weights)),
            key=lambda i: (pool_cents * weights[i]) % total,
            reverse=True,
        )
        for i in order[:remainder]:
            shares[i] += 1
    return shares


if __name__ == "__main__":
    result = split_pool(10000, [1, 1, 1])
    print(result)       # [3334, 3333, 3333]
    print(sum(result))  # 10000，恰好等于池子总额
