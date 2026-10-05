import csv
import re
import sys
from pathlib import Path

GOLD_DIR = Path(__file__).resolve().parent.parent / "gold"

BASIS_ANY = {
    "SV-001": [["62"], ["机柜", "超"]],
    "SV-002": [["告警"]],
    "SV-003": [["返修"], ["保修"]],
    "SV-004": [["75"]],
}

PROG_POINTS = {
    "判定":    {"SV-001": 4, "SV-002": 2, "SV-003": 2, "SV-004": 2},
    "触发条款": {"SV-001": 1, "SV-002": 1, "SV-003": 1, "SV-004": 1},
    "判定依据": {"SV-001": 2, "SV-002": 1, "SV-003": 1, "SV-004": 1},
}

# 语义判分点分值 (判「判定说明.md」理由是否自洽), 本程序不判定。
SEM_POINTS = {"SV-001": 3, "SV-002": 2, "SV-003": 2, "SV-004": 2}

PROG_TOTAL = sum(sum(d.values()) for d in PROG_POINTS.values())
SEM_TOTAL = sum(SEM_POINTS.values())
TOTAL = PROG_TOTAL + SEM_TOTAL



def clean(s):
    return re.sub(r"\s+", "", (s or ""))


def extract_clause(s):
    """从「触发条款」列提取 4.x, 容忍『第/条/空格/中文句点』等写法。"""
    m = re.search(r"4\s*[.．·]\s*[123]", s or "")
    if not m:
        return ""
    return "4." + m.group(0)[-1]


def basis_ok(dev, text):
    for must_all in BASIS_ANY[dev]:
        if all(sub in text for sub in must_all):
            return True
    return False


def read_table(path):
    rows = {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dev = clean(row.get("设备编号", ""))
            if dev:
                rows[dev] = row
    return rows


def read_gold():
    g = read_table(GOLD_DIR / "检修判定表.csv")
    verdicts = {dev: clean(row["判定"]) for dev, row in g.items()}
    clauses = {dev: extract_clause(row["触发条款"]) for dev, row in g.items()}
    return verdicts, clauses



def score(sub_dir, verdicts, clauses):
    sub = Path(sub_dir)
    table_path = sub / "检修判定表.csv"
    note_path = sub / "判定说明.md"

    if not table_path.is_file():
        print(f"错误: 找不到提交物 {table_path}")
        sys.exit(1)

    table = read_table(table_path)
    note_exists = note_path.is_file()

    lines = []  # (编号, 名称, 得分, 满分, 类型, 说明)

    #  程序化判分 
    rid = 0
    for field, points in PROG_POINTS.items():
        for dev, pt in points.items():
            rid += 1
            row = table.get(dev)
            if row is None:
                lines.append((f"R{rid}", f"{dev} {field}", 0, pt, "程序化", "未找到该设备行"))
                continue
            val = row.get(field, "")
            if field == "判定":
                ok = clean(val) == verdicts[dev]
                note = f"得「{val.strip() or '空'}」, 期望「{verdicts[dev]}」"
            elif field == "触发条款":
                got = extract_clause(val)
                ok = got == clauses[dev]
                note = f"得「{val.strip() or '空'}」→ {got or '未识别'}, 期望「{clauses[dev]}」"
            else:  # 判定依据
                ok = basis_ok(dev, val)
                note = f"依据「{val.strip() or '空'}」, 关键事实{'命中' if ok else '未命中'}"
            lines.append((f"R{rid}", f"{dev} {field}", pt if ok else 0, pt,
                          "程序化", note))

    #  语义判分 (待判定) 
    if not note_exists:
        print("提示: 未找到 判定说明.md, 语义判分点将无法被人工/模型判定。")
    sid = 0
    for dev, pt in SEM_POINTS.items():
        sid += 1
        lines.append((f"S{sid}", f"{dev} 判定说明", None, pt, "语义", "待人工/模型判定"))

    return lines


def main():
    if len(sys.argv) != 2:
        print("用法: python verify.py <提交目录>")
        sys.exit(2)
    verdicts, clauses = read_gold()
    lines = score(sys.argv[1], verdicts, clauses)

    prog_got = sum(g for (_, _, g, _, typ, _) in lines if typ == "程序化")

    print("机房设备停机检修判定 · 评分结果")
    print(f"提交目录: {sys.argv[1]}")
    print(f"gold 基准: {GOLD_DIR}")
    print()
    print("── 程序化判分点 ──")
    for cid, name, got, full, typ, note in lines:
        if typ == "程序化":
            mark = "通过" if got == full else "不通过"
            print(f"  {cid:>3}  {name:<14} {got}/{full}  {mark}  ({note})")
    print()
    print("── 语义判分点 ──")
    for cid, name, got, full, typ, note in lines:
        if typ == "语义":
            print(f"  {cid:>3}  {name:<14} ?/{full}  待人工/模型判定")
    print()
    print("── 小计 ──")
    print(f"  程序化小计: {prog_got}/{PROG_TOTAL}")
    print(f"  语义小计:   待判定 (满分 {SEM_TOTAL})")
    print(f"  总分:       {prog_got}/{TOTAL}  (语义未判定, 当前仅含程序化)")


if __name__ == "__main__":
    main()
