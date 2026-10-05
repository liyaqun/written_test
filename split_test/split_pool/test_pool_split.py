"""
test_pool_split.py —— split_pool 的单元测试

核心不变量：对任意输入，分配结果之和必须恰好等于池子总额。
"""

import random
import unittest

# from pool_split import split_pool # 旧的函数 
from pool_split_new import split_pool # 修复之后的函数

class TestSplitPool(unittest.TestCase):
    def test_01_docstring_example(self):
        pool, weights = 10000, [1, 1, 1]
        self.assertEqual(sum(split_pool(pool, weights)), pool)

    def test_02_property_based_many_inputs(self):
        """固定种子随机扫 2000 组输入，逐一断言 sum == pool（比手写样例更不易漏）。"""
        rng = random.Random(0)
        for _ in range(2000):
            n = rng.randint(1, 20)
            weights = [rng.randint(1, 1000) for _ in range(n)]
            pool = rng.randint(1, 10 ** 6)
            result = split_pool(pool, weights)
            self.assertEqual(
                sum(result), pool,
                f"pool={pool} weights={weights} -> sum={sum(result)} result={result}",
            )

    def test_03_each_share_within_one_cent(self):
        """每个人拿到的钱与精确比例值相差不超过 1 分（比例近似正确）。"""
        pool, weights = 999, [1, 2, 3, 5]
        total = sum(weights)
        for w, got in zip(weights, split_pool(pool, weights)):
            self.assertLess(abs(got - pool * w / total), 1.0)

    def test_04_zero_weight_gets_zero(self):
        """权重为 0 的人应拿 0 分，其他人照常分。"""
        pool, weights = 1000, [0, 1, 1]
        result = split_pool(pool, weights)
        self.assertEqual(result[0], 0)
        self.assertEqual(sum(result), pool)

    def test_05_empty_and_invalid(self):
        """空列表返回空；全零权重 / 负数权重应报 ValueError。"""
        self.assertEqual(split_pool(100, []), [])
        with self.assertRaises(ValueError):
            split_pool(100, [0, 0, 0])
        with self.assertRaises(ValueError):
            split_pool(100, [1, -1])


if __name__ == "__main__":
    unittest.main(verbosity=2)
