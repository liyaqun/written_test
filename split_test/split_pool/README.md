# 奖池分账 —— split_pool 修复说明

## 1. 会出错的输入

当前实现 `[round(pool_cents * w / total) for w in weights]` 对**每个人独立**做四舍五入。
舍入误差方向不固定（有人被进、有人被舍），n 个独立误差相加通常不等于 0，
于是分配之和会偏离池子总额。

### 反例 A
- 输入：`pool_cents = 100`，`weights = [1, 1, 1]`
- 实际返回：`[33, 33, 33]`
- 实际的和：`99`
- 应有的和：`100`

精确份额是 33.33…，Python 的 `round(33.33…)` 得到 33，三人合计 99，少 1 分。

### 反例 B（题目自带的示例）
- 输入：`pool_cents = 10000`，`weights = [1, 1, 1]`
- 实际返回：`[3333, 3333, 3333]`
- 实际的和：`9999`
- 应有的和：`10000`

## 2. 修复方案：最大余数法

全程整数运算，步骤：

1. `shares[i] = floor(pool_cents * w_i / total)` 作为基础份额；
2. `remainder = pool_cents - sum(shares)` 为尚未分出的差额，必落在 `[0, n-1]`；
3. 按「小数余数」`(pool_cents * w_i) % total` 从大到小排序，把差额逐分补给排在最前面的 `remainder` 个人。

性质：
- 每人拿到的钱 = 精确份额的 floor 或 ceil，与精确值相差 < 1 分（比例近似正确）；
- 总和恒等于 pool_cents，数学上必然成立。

## 3. 测试与两次运行输出

测试命令（在 split_pool 目录下执行）：

    python -m unittest test_pool_split -v
（注意：导入 from pool_split import split_pool ）
### 第一次运行：未修改的 split_pool —— 失败



关键输出（FAILED，failures=3, errors=1）：

    test_01_docstring_example (test_pool_split.TestSplitPool.test_01_docstring_example) ... FAIL
    test_02_property_based_many_inputs (test_pool_split.TestSplitPool.test_02_property_based_many_inputs)
    固定种子随机扫 2000 组输入，逐一断言 sum == pool（比手写样例更不易漏）。 ... FAIL
    test_03_each_share_within_one_cent (test_pool_split.TestSplitPool.test_03_each_share_within_one_cent)
    每个人拿到的钱与精确比例值相差不超过 1 分（比例近似正确）。 ... ok
    test_04_zero_weight_gets_zero (test_pool_split.TestSplitPool.test_04_zero_weight_gets_zero)
    权重为 0 的人应拿 0 分，其他人照常分。 ... ok
    test_05_empty_and_invalid (test_pool_split.TestSplitPool.test_05_empty_and_invalid)
    空列表返回空；全零权重 / 负数权重应报 ValueError。 ... ERROR

    Ran 5 tests in 0.007s

    FAILED (failures=2, errors=1)

### 第二次运行：修改后的 split_pool（最大余数法）—— 通过

关键输出（OK）：

   
    test_01_docstring_example (test_pool_split.TestSplitPool.test_01_docstring_example) ... ok
    test_02_property_based_many_inputs (test_pool_split.TestSplitPool.test_02_property_based_many_inputs)
    固定种子随机扫 2000 组输入，逐一断言 sum == pool（比手写样例更不易漏）。 ... ok
    test_03_each_share_within_one_cent (test_pool_split.TestSplitPool.test_03_each_share_within_one_cent)
    每个人拿到的钱与精确比例值相差不超过 1 分（比例近似正确）。 ... ok
    test_04_zero_weight_gets_zero (test_pool_split.TestSplitPool.test_04_zero_weight_gets_zero)
    权重为 0 的人应拿 0 分，其他人照常分。 ... ok
    test_05_empty_and_invalid (test_pool_split.TestSplitPool.test_05_empty_and_invalid)
    空列表返回空；全零权重 / 负数权重应报 ValueError。 ... ok

    Ran 5 tests in 0.079s

    OK


## 4. AI 使用情况

使用了 AI 助手（Claude Code）。

- **提出的问题**：直接给出本题的 `pool_split.py` 与全部要求，请其找反例、修复代码、编写测试并说明思路。
- **得到的回答**：
  1) 根因是「对每人独立 round，误差不保证相消」；
  2) 反例 `pool=100, weights=[1,1,1]`（round 后 99 ≠ 100）；
  3) 用「最大余数法」重写：整数 floor 打底，差额按小数余数从大到小补 1 分；
  4) 测试 = 具体反例 + 固定种子属性测试 + 比例误差 < 1 分 + 边界用例。
- **是否直接采用**：思路直接采用；代码经人工逐条核对后采用。
- **如何确认正确**：
  a) 数学论证：floor 份额求和后补足差额，`sum = 基础份额之和 + remainder = pool` 恒成立；`remainder ∈ [0, n-1]` 由「n 个 [0,1) 的小数之和 < n」保证，故补分人数一定足够。
  b) 属性测试：固定种子随机 2000 组输入全部满足 `sum == pool`。
  c) 边界逐项核对：空列表返回空、全零权重报错、负数权重报错、零权重拿 0。
  d) 手工样例核对每个数字，如 `999 / [1,2,3,5] -> [91,182,272,454]`、`1000 / [0,1,1] -> [0,500,500]`。

## 5. 补充

- **测试覆盖**：固定种子的属性测试（随机 2000 组）比手写若干样例更不容易漏掉问题——它会自动扫到各种「总额 / 权重 / 人数」组合下的舍入冲突。
- **多出/缺少的那几分分给了谁**：分给了「小数余数」最大（最接近进位）的人，依据是最大余数法。换一个人（第二大的）同样可行——差额补给谁只影响「谁多得 1 分」，不影响总和守恒。并列时取下标最小者，保证结果确定。