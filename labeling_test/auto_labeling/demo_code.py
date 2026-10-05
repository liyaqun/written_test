"""
读数据 → 构造 prompt（系统提示 + few-shot + JSON 约束）→ 调模型 → 解析 JSON → 输出 + 算准确率/每类 precision/recall
"""

import argparse
import csv
import glob
import json
import os
import random
import re
import sys
import time

import requests

# API_URL = os.environ.get("LLM_API_URL", "http://localhost:8000/v1/chat/completions")
# MODEL = os.environ.get("LLM_MODEL", "qwen2.5-7B-Instruct")
API_KEY = os.environ.get("MODELSCOPE_API_KEY", "ms-018622e3-5368-4a2d-91b7-f1d78ec2193d")
API_URL = os.environ.get("LLM_API_URL", "https://api-inference.modelscope.cn/v1/chat/completions")
MODEL = os.environ.get("LLM_MODEL", "Qwen/Qwen3.8-27B")
TEMPERATURE = 0.0        
MAX_TOKENS = 200         
REQUEST_TIMEOUT = 120    

LABEL_NAMES = ["negative", "positive"]
FEWSHOT_EXAMPLES = [
    ("房间很干净，服务也很周到，下次还会再来。", "positive"),
    ("隔音太差了，半夜吵得根本睡不着，很失望。", "negative"),
]

POS_CANDIDATES = ["pos.txt", "pos.csv", "pos", "positive.txt", "positive",
                  "pos_2000.txt", "pos.2000.txt", "pos_2k.txt"]
NEG_CANDIDATES = ["neg.txt", "neg.csv", "neg", "negative.txt", "negative",
                  "neg_2000.txt", "neg.2000.txt", "neg_2k.txt"]


def detect_encoding(path):
    for enc in ("utf-8", "gb18030", "gbk"):
        try:
            with open(path, "r", encoding=enc) as f:
                f.read(4096)
            return enc
        except (UnicodeDecodeError, UnicodeError):
            continue
    return "utf-8" 

def read_text(path):
    enc = detect_encoding(path)
    with open(path, "r", encoding=enc, errors="replace") as f:
        return f.read()


def read_lines(path):
    return [ln.strip() for ln in read_text(path).splitlines() if ln.strip()]


def find_pos_neg(data_dir):
    pos_file = next((os.path.join(data_dir, n) for n in POS_CANDIDATES
                     if os.path.isfile(os.path.join(data_dir, n))), None)
    neg_file = next((os.path.join(data_dir, n) for n in NEG_CANDIDATES
                     if os.path.isfile(os.path.join(data_dir, n))), None)
    if not pos_file:
        pos_file = _glob_first(data_dir, "pos*.txt")
    if not neg_file:
        neg_file = _glob_first(data_dir, "neg*.txt")
    if pos_file and neg_file:
        return read_lines(pos_file), read_lines(neg_file)

    pos_dir = os.path.join(data_dir, "pos")
    neg_dir = os.path.join(data_dir, "neg")
    if os.path.isdir(pos_dir) and os.path.isdir(neg_dir):
        pos = [read_text(os.path.join(pos_dir, f)).strip()
               for f in sorted(os.listdir(pos_dir)) if f.endswith(".txt")]
        neg = [read_text(os.path.join(neg_dir, f)).strip()
               for f in sorted(os.listdir(neg_dir)) if f.endswith(".txt")]
        pos = [t for t in pos if t]
        neg = [t for t in neg if t]
        if pos and neg:
            return pos, neg

    raise FileNotFoundError(
        f"未在 {data_dir} 下找到正负例数据。支持两种目录结构：\n"
        "  A. data/pos.txt + data/neg.txt（每行一条评论）\n"
        "  B. data/pos/*.txt + data/neg/*.txt（每个文件一条评论）\n"
        "请把语料放到 data/ 目录下，或改用 --data-dir 指定路径。"
    )


def _glob_first(data_dir, pattern):
    matches = sorted(glob.glob(os.path.join(data_dir, pattern)))
    return matches[0] if matches else None


def load_data(data_dir, n_per_class):
    pos_texts, neg_texts = find_pos_neg(data_dir)
    rows = []
    for text in neg_texts[:n_per_class]:
        rows.append({"text": text, "gold": "negative"})
    for text in pos_texts[:n_per_class]:
        rows.append({"text": text, "gold": "positive"})
    random.seed(42)
    random.shuffle(rows)  # mix classes so outputs are not clustered
    for i, r in enumerate(rows):
        r["id"] = i
    return rows, len(pos_texts), len(neg_texts)


def build_messages(text):
    return [
        {"role": "system", "content": system_prompt()},
        {"role": "user", "content": f"Text:\n{text}"},
    ]


def system_prompt():
    labels = ", ".join(LABEL_NAMES)
    lines = [
        "你是一个文本情感分类助手。请把输入的评论文本分类为以下两类之一。",
        f"类别: {labels}（negative=差评，positive=好评）",
        "",
        "规则:",
        "1. 选择唯一最合适的类别。",
        "2. 只输出一个 JSON 对象，不要额外文字，不要代码块:",
        '   {"label": "<negative 或 positive>", "confidence": <0.0-1.0>, "reason": "<一句话理由>"}',
        "3. label 必须严格使用 negative 或 positive。",
        "",
        "示例:",
    ]
    for text, lab in FEWSHOT_EXAMPLES:
        lines.append(f'Text: "{text}"')
        lines.append(f'{{"label": "{lab}", "confidence": 0.95, "reason": "情感倾向明确"}}')
    return "\n".join(lines)


def call_model(messages, retries=3):
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.post(API_URL, json=payload, headers=headers, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:  # network / HTTP / schema errors
            last_err = e
            time.sleep(2 * attempt)
    raise RuntimeError(f"model call failed after {retries} attempts: {last_err}")


def parse_label(raw, labels):
    """Extract {label, confidence, reason} from the model's (possibly noisy) reply."""
    raw = (raw or "").strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    obj = None
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            try:
                obj = json.loads(m.group(0))
            except json.JSONDecodeError:
                obj = None

    if isinstance(obj, dict):
        label = str(obj.get("label", "")).strip()
        confidence = obj.get("confidence")
        reason = str(obj.get("reason", "")).strip()
    else:
        label, confidence, reason = raw, None, ""

    matched = match_label(label, labels)
    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        confidence = None

    return {"label": matched, "confidence": confidence, "reason": reason, "raw": raw}


def match_label(label, labels):
    if not label:
        return None
    low = label.lower().strip()
    for name in labels:                     
        if name.lower() == low:
            return name
    for name in labels:                     
        if name.lower() in low or low in name.lower():
            return name
    return None


def evaluate(results, label_names):
    scored = [r for r in results if r["correct"] is not None]
    if not scored:
        print("No ground-truth labels available; skipping accuracy evaluation.")
        return

    acc = sum(1 for r in scored if r["correct"]) / len(scored)
    print(f"\n=== Evaluation (n={len(scored)}) ===")
    print(f"Accuracy: {acc:.2%}")

    print("\nPer-class (gold -> pred):")
    for name in label_names:
        g = [r for r in scored if r["gold"] == name]
        if not g:
            continue
        right = sum(1 for r in g if r["pred"] == name)
        p = [r for r in scored if r["pred"] == name]
        precision = right / len(p) if p else 0.0
        recall = right / len(g)
        print(f"  {name:<12} support={len(g):<4} precision={precision:.2f} recall={recall:.2f}")

    print("\n=== Example outputs (sample -> model label) ===")
    for r in scored[:8]:
        mark = "OK" if r["correct"] else "MISS"
        print(f"[{mark}] gold={r['gold']!r} -> pred={r['pred']!r} (conf={r['confidence']})")
        print(f"     text: {r['text'][:60]}")
        print(f"     reason: {r['reason']}")


def main():
    ap = argparse.ArgumentParser(description="Auto-label Tan Songbo reviews with a local LLM")
    ap.add_argument("--data-dir", default="data", help="folder containing pos/neg reviews")
    ap.add_argument("--n-per-class", type=int, default=100,
                    help="number of samples per class (2000 = use all)")
    ap.add_argument("--dry-run", action="store_true", help="print prompts without calling the model")
    ap.add_argument("--out-dir", default="outputs")
    ap.add_argument("--out", help="output JSON path (default: <out-dir>/tansongbo_labels.json)")
    args = ap.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    if not os.path.isdir(args.data_dir):
        alt = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.data_dir)
        if os.path.isdir(alt):
            args.data_dir = alt

    rows, n_pos, n_neg = load_data(args.data_dir, args.n_per_class)

    print(f"Dataset : Tan Songbo hotel review corpus (谭松波评论语料)")
    print(f"Found   : {n_pos} positive / {n_neg} negative reviews in {args.data_dir}")
    print(f"Labeling: {len(rows)} samples | Labels: {LABEL_NAMES}")
    print(f"Endpoint: {API_URL} | Model: {MODEL}\n")

    results = []
    for row in rows:
        messages = build_messages(row["text"])
        if args.dry_run:
            print("=" * 70)
            print(f"[{row['id']}] GOLD={row.get('gold')}")
            print(messages[-1]["content"])
            continue

        raw = call_model(messages)
        parsed = parse_label(raw, LABEL_NAMES)
        correct = (parsed["label"] == row["gold"]) if row.get("gold") is not None else None
        results.append({
            "id": row["id"],
            "text": row["text"],
            "gold": row.get("gold"),
            "pred": parsed["label"],
            "confidence": parsed["confidence"],
            "reason": parsed["reason"],
            "raw_output": parsed["raw"],
            "correct": correct,
        })
        print(f"[{row['id']}] pred={parsed['label']!r} gold={row.get('gold')!r} "
              f"conf={parsed['confidence']} {'OK' if correct else ('X' if correct is False else '-')}")
        time.sleep(0.05) 

    if args.dry_run:
        print("\n(dry run: no model calls were made)")
        return

    # --- save ---
    os.makedirs(args.out_dir, exist_ok=True)
    out_json = args.out or os.path.join(args.out_dir, "tansongbo_labels.json")
    out_csv = os.path.splitext(out_json)[0] + ".csv"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "text", "gold", "pred", "confidence", "reason", "correct"])
        w.writeheader()
        for r in results:
            w.writerow({k: r.get(k) for k in w.fieldnames})
    print(f"\nSaved {len(results)} results to {out_json} and {out_csv}")

    evaluate(results, LABEL_NAMES)


if __name__ == "__main__":
    main()
