# envlit

一个简单的 CLI 工具，用于组织、加载和切换项目的环境变量上下文。


## 使用场景

- **开发环境** - 在开发/生产配置之间切换
- **ML/AI 工作流** - 便捷管理 CUDA 设备、模型路径、后端、环境变量
- **多项目设置** - 每个项目的独立环境
- **团队一致性** - 通过 git 共享通用环境配置，同时保留本地覆盖

## 安装

```bash
pip install envlit
```

## 快速开始

在 shell 中初始化 envlit（添加到 `.bashrc` 或 `.zshrc`）：

```bash
eval "$(envlit init)"
```

在 `.envlit/default.yaml` 创建配置文件：

```yaml
env:
  PROJECT_MODE: "Development"
  DEBUG: "true"
```

加载和卸载环境变量：

```bash
el                       # 加载默认配置
echo $PROJECT_MODE       # 输出: Development (由 envlit 设置的变量)
echo $DEBUG              # 输出: true (由 envlit 设置的变量)

eul                      # 卸载环境变量
echo $PROJECT_MODE       # 输出: (空 - 变量恢复到原始状态)
echo $DEBUG              # 输出: (空 - 变量恢复到原始状态)
```

## 功能特性

### 智能状态追踪
自动检测并保留加载/卸载周期之间的手动环境更改。不会覆盖您修改的变量。

示例：
```bash
el dev                    # 加载开发环境 (设置 DEBUG=true)
export DEBUG=false        # 手动更改 DEBUG
export CUSTOM_VAR=foo     # 添加您自己的变量
eul                       # 卸载: 恢复原始 DEBUG，保留 CUSTOM_VAR
```

envlit 仅恢复它管理的变量，保留您的手动更改。

### 动态标志
在 YAML 中定义短 CLI 标志，映射到长环境变量名称和值。减少输入负担：

```yaml
flags:
  cuda:
    flag: ["--cuda", "-g"]
    default: "0"
    target: "CUDA_VISIBLE_DEVICES"

  backend:
    flag: ["--backend", "-b"]
    default: "c"
    target: "ML_COMPUTE_BACKEND"
    map:
      c: "CPU"
      g: "GPU"
      t: "TPU"
```

用法：`el dev --cuda 2 -b g` 设置 `CUDA_VISIBLE_DEVICES=2` 和 `ML_COMPUTE_BACKEND=GPU`

### 环境变量操作
envlit 支持三种设置环境变量的语法：

**1. 字符串快捷方式（用于简单的设置操作）：**
```yaml
env:
  DEBUG: "true"
  API_URL: "https://api.example.com"
```

**2. 单个操作的字典：**
```yaml
env:
  PATH:
    op: prepend
    value: "./venv/bin"

  PRODUCTION_KEY:
    op: unset
```

**3. 操作列表（管道）：**
```yaml
env:
  PATH:
    - op: remove
      value: "/old/path"
    - op: prepend
      value: "./bin"
    - op: append
      value: "/usr/local/tools"
```

**可用操作：**
- `set` - 设置值（可使用字符串快捷方式）
- `unset` - 取消设置变量
- `prepend` - 添加到类路径变量的前面
- `append` - 添加到类路径变量的末尾
- `remove` - 从类路径变量中移除

### 生命周期钩子
在四个生命周期点执行自定义脚本：

```yaml
hooks:
  pre_load:
    - name: "Validate setup"
      script: "echo 'Loading...'"
  post_load:
    - name: "Show status"
      script: "echo 'Ready!'"
  pre_unload:
    - name: "Cleanup"
      script: |
        echo "Unloading..."
        echo "Goodbye!"
  post_unload:
    - name: "Confirm"
      script: "echo 'Environment restored.'"
```

### 配置继承
扩展基础配置以减少重复：

```yaml
extends: "./base.yaml"
env:
  EXTRA_VAR: "value"
```

!!! note "值中的特殊字符"
    **变量扩展**：使用 shell 语法

    - `$VAR` 或 `${VAR}` - 运行时扩展
    - `${VAR:-default}` - 带默认值

    **字面美元符号**：使用占位符

    - `{{DOLLAR}}` - 变成字面 `$`
    - 示例：`PRICE: "{{DOLLAR}}100"` → `$100`

    **其他特殊字符**：

    - 反引号、引号、反斜杠会自动转义
    - 对引号使用 YAML 引号交替：
        - `"value 'with' singles"`
        - `'value "with" doubles'`

    **示例**：

    | 输入 (YAML) | 脚本中的输出 | Shell 解释 | 使用场景 |
    |--------------|------------------|------------------|----------|
    | `$HOME` | `$HOME` | `/Users/you` | 变量扩展 |
    | `${HOME}` | `${HOME}` | `/Users/you` | 变量扩展 |
    | `{{DOLLAR}}100` | `\$100` | `$100` | 字面美元符号 |
    | `` `cmd` `` | `` \`cmd\` `` | `` `cmd` `` | 字面反引号 |
    | `"quoted"` | `\"quoted\"` | `"quoted"` | 转义引号 |

    **对于复杂逻辑**：使用钩子而不是 `env:` 部分

### 多配置文件
在开发、测试和生产环境之间切换：

```bash
el dev      # 加载 .envlit/dev.yaml
el prod     # 加载 .envlit/prod.yaml
```

## 配置

创建 `.envlit/<profile>.yaml` 文件：

```yaml
# 可选：从基础配置继承
extends: "./base.yaml"

# 动态 CLI 标志 - 短标志映射到长环境变量名称和值
flags:
  cuda:
    flag: ["--cuda", "-g"]
    default: "0"
    target: "CUDA_VISIBLE_DEVICES"

  backend:
    flag: ["--backend", "-b"]
    default: "c"
    target: "ML_COMPUTE_BACKEND"
    map:
      c: "CPU"
      g: "GPU"
      t: "TPU"

# 环境变量
env:
  # 简单值（'set' 操作的字符串快捷方式）
  DEBUG: "true"
  API_URL: "https://api.example.com"

  # 取消设置变量
  LEGACY_VAR:
    op: unset

  # Shell 扩展
  DATA_PATH: "${HOME}/data"

  # 单个操作（字典语法）
  PRODUCTION_MODE:
    op: set
    value: "true"

  # 路径操作（操作列表 - 管道）
  PATH:
    - op: remove
      value: "/deprecated/path"
    - op: prepend
      value: "./bin"
    - op: append
      value: "/usr/local/tools"

  # 单个路径操作（字典语法）
  PYTHONPATH:
    op: prepend
    value: "./src"

# 生命周期钩子
hooks:
  pre_load:
    - name: "Check dependencies"
      script: "command -v docker >/dev/null || echo 'Warning: docker not found'"
  post_load:
    - name: "Show environment"
      script: "echo '✓ Environment loaded'"
  pre_unload:
    - name: "Cleanup"
      script: "echo 'Unloading...'"
  post_unload:
    - name: "Confirm"
      script: "echo '✓ Environment restored'"
```

## 命令

```bash
# 初始化 shell 集成
eval "$(envlit init)"

# 加载环境
el                    # 加载默认配置
el dev                # 加载开发配置
el dev --cuda 1       # 使用标志加载

# 卸载环境
eul

# 将追踪的变量导出到 .env 文件
envlit state          # 显示 envlit 状态中的变量
envlit state --from-env  # 显示当前环境值
envlit state > .env   # 导出到 .env 文件

# 检查安装
envlit doctor
```

## Shell 集成

`init` 命令创建包装 envlit 的 shell 函数：
- `el` - 加载环境
- `eul` - 卸载环境

在初始化期间自定义别名：

```bash
eval "$(envlit init --alias-load myload --alias-unload myunload)"
```

## 工作原理

1. **加载阶段**：
   - 捕获当前环境状态（快照 A）
   - 运行 pre-load 钩子
   - 导出环境变量
   - 运行 post-load 钩子
   - 捕获新状态（快照 B）并保存差异

2. **卸载阶段**：
   - 运行 pre-unload 钩子
   - 从保存的状态恢复原始环境
   - 运行 post-unload 钩子

3. **状态追踪**：
   - 检测快照之间的手动更改
   - 在卸载期间保留用户修改
   - 仅恢复由 envlit 更改的变量（注意：在钩子期间更改的变量不被追踪，应在钩子本身中处理）

## 链接

- [GitHub](https://github.com/luocfprime/envlit)
- [PyPI](https://pypi.org/project/envlit/)
