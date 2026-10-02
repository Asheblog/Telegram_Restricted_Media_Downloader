# coding=UTF-8
"""量化 composition_root 的 50 个 getter：哪些是"服务定位器伪装成回调"？

判定思路：
- 若 getter 返回的对象**在构造期已经存在**（同名 self 属性已赋值），
  那它本质是"把 self 的绑定方法/属性传回给下游"，属于可收敛的对象引用；
- 若 getter 用于**延迟解析**（构造期该属性还是 None，之后才赋值），
  那它是真实的时序解耦手段，**不应**改成直接传对象（会把时序耦合变成崩溃）。
"""
import ast
import pathlib
import re

REPO = pathlib.Path(r"E:\codebase\tgbot")
SRC = (REPO / "module" / "composition_root.py").read_text(encoding="utf-8")
TREE = ast.parse(SRC)

# 1) 收集所有 *_getter= 实参
getter_args = []
for node in ast.walk(TREE):
    if isinstance(node, ast.keyword) and node.arg and node.arg.endswith("_getter"):
        getter_args.append((node.arg, node.value, node.lineno))

# 2) 收集 self.<attr> = ... 的赋值行（构造期）
assigned = {}
for node in ast.walk(TREE):
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == "self":
                assigned[t.attr] = node.lineno

# 3) 每个 getter 指向的 self.<attr>，以及该属性是否在 getter 被传入之前已赋值
late_bound, early_bound = [], []
for name, value, lineno in getter_args:
    target = None
    if isinstance(value, ast.Attribute) and isinstance(value.value, ast.Name) and value.value.id == "self":
        target = value.attr
    elif isinstance(value, ast.Name):
        target = f"<local {value.id}>"
    assign_line = assigned.get(target) if target else None
    if assign_line is None:
        late_bound.append((name, target, lineno))
    elif assign_line < lineno:
        early_bound.append((name, target, assign_line, lineno))
    else:
        late_bound.append((name, target, lineno))

print(f"getter 实参总数: {len(getter_args)}")
print(f"  指向构造期已存在的对象（可收敛）: {len(early_bound)}")
print(f"  指向构造期尚不存在/局部变量（真延时）: {len(late_bound)}")
print()
print("=== 可收敛（构造期已存在）===")
seen = set()
for name, target, al, gl in sorted(early_bound, key=lambda r: r[1] or ""):
    if target in seen:
        continue
    seen.add(target)
    print(f"  {name:42s} -> self.{target:24s} 赋值于 L{al}，传出于 L{gl}")
print()
print("=== 真延时（构造期没有，之后才赋值）===")
for name, target, gl in sorted(late_bound, key=lambda r: r[1] or ""):
    print(f"  {name:42s} -> {target}  (L{gl})")

# 4) 统计 composition_root 内 kwarg 总数
kwarg_count = sum(1 for n in ast.walk(TREE) if isinstance(n, ast.keyword))
print(f"\n文件中 keyword 实参总数（含非 getter）: {kwarg_count}")
