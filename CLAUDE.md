# Claude Code Instructions

- 使用中文沟通。
- 文件保持 UTF-8 无 BOM。
- 不要泄露密钥、令牌、凭据或内部链接。
- 除非用户明确要求，不要执行破坏性命令。

## 发布与构建触发

- 本仓库 Docker 构建只会被 `v*.*.*` 版本 tag 触发，普通 push 到 `main` 不会触发 Release Docker workflow。
- 每次需要推送仓库并触发构建时，必须先在原版本基础上递增一个版本号，默认递增 patch 版本。例如：`0.2.13` -> `0.2.14`。
- 必须同步更新：
  - `pyproject.toml` 的 `version`
  - `module/__init__.py` 的 `__version__`
- 提交版本号后，创建并推送同名 annotated tag：

```bash
git tag -a vX.Y.Z -m "Release X.Y.Z"
git push origin main
git push origin vX.Y.Z
```

- 如果已经 push 了 `main` 但 GitHub Actions 没触发，优先检查是否漏推 tag；漏了就补推对应 tag，不要为了触发构建随便空提交。
- 完成发布触发后，向用户说明 commit hash 和 tag 名称。

## 测试

- 代码变更先跑相关测试；影响共享链路时再跑更大范围测试。
- 仅改版本号时，可以只做轻量语法检查，除非同时改了代码。
