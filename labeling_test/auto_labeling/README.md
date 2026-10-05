# Auto-Labeling Demo (Qwen2.5-7B-Instruct)

用本地部署的 Qwen2.5-7B-Instruct（vllm启动的）对文本分类数据集自动打标。

## 文件 Files

| 文件 | 说明 |
|---|---|
| `demo_code.py` | 可运行代码 |
| `example_output.json` | 示例输出：在此为了节省时间，只运行产出100条数据的打标结果 |
| `report.md` | 书面报告 |
| `requirements.txt` | Python 依赖 |

## 运行 Run

```bash
pip install -r requirements.txt

python demo_code.py --n 100        # 只打 100 条(消极和积极的评论各自100条)
```

## 配置 Config

如果模型服务地址 / 模型名不同，改 `demo_code.py` 顶部的常量，或设置环境变量：

```bash
export LLM_API_URL=http://localhost:7860
export LLM_MODEL=qwen2.5-7B-Instruct
```

## 输出 Output

结果写入 `outputs/<key>_labels.json`（完整字段）和 `outputs/<key>_labels.csv`（表格），
并在终端打印准确率、每类 precision/recall 以及若干 “样本 → 模型标签” 示例。
