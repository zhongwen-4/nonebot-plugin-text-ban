<div align="center">
  <a href="https://v2.nonebot.dev/store"><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/nbp_logo.png" width="180" height="180" alt="NoneBotPluginLogo"></a>
  <br>
  <p><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/NoneBotPlugin.svg" width="240" alt="NoneBotPluginText"></p>
</div>

<div align="center">

# nonebot-plugin-text-ban

_✨ 违禁词撤回 ✨_

</div>

什么？又有司马仔发tx的广告触发词了？快用它ban掉吧~

## 📖 介绍

一个基于Lagrange.OneBot和NoneBot的违禁词撤回插件

> [!WARNING]
> 该插件只能用Lagrange.OneBot作为协议端，其他协议端暂不支持

### 已实现的功能

- 违禁词撤回
- 误判申诉
- 图片检测
- 谐音检测
- 自动踢出

## 💿 安装

<details open>
<summary>使用 nb-cli 安装</summary>
在 nonebot2 项目的根目录下打开命令行, 输入以下指令即可安装

    nb plugin install nonebot-plugin-text-ban

</details>

<details>
<summary>使用包管理器安装</summary>
在 nonebot2 项目的插件目录下, 打开命令行, 根据你使用的包管理器, 输入相应的安装命令

<details>
<summary>pip</summary>

    pip install nonebot-plugin-text-ban
</details>
<details>
<summary>pdm</summary>

    pdm add nonebot-plugin-text-ban
</details>
<details>
<summary>poetry</summary>

    poetry add nonebot-plugin-text-ban
</details>
<details>
<summary>conda</summary>

    conda install nonebot-plugin-txt_ban
</details>

打开 nonebot2 项目根目录下的 `pyproject.toml` 文件, 在 `[tool.nonebot]` 部分追加写入

    plugins = ["nonebot_plugin_text_ban"]

</details>

## ⚙️ 配置

| 配置项 | 必填 | 默认值 | 说明 | 数据类型 |
|:-----:|:----:|:----:|:----:|:----:|
| strict | 否 | False | 严格模式（一个一个字检测，例如你的违禁词是 "你好"，如果开了这项，那么只要消息中包含“你”和“好”，那么就会撤回） | bool |
| ocr | 否 | False | 检测图片中的违禁词（精度稍低） | bool |
| pinyin | 否 | False | 检测谐音字 | bool |
| kick | 否 | False | 是否自动踢出（群员触发3次违禁词后自动踢出 | bool |

## 🎉 使用
### 指令表
| 指令 | 权限 | 需要@ | 范围 | 说明 |
|:-----:|:----:|:----:|:----:|:----:|
| help | 管理/群主/主人 | 否 | all | 插件帮助（需要加上命令头） |
| add [text] [type] | 管理/群主/主人 | 是 | all | 添加违禁词，text代表违禁词，type代表模式，目前可选1（精确），2（模糊） |
| del [text] [type] | 管理/群主/主人 | 是 | all | 删除违禁词，text代表违禁词，type代表模式，目前可选1（精确），2（模糊） |
| add_group [group_id?] | 管理/群主/主人 | 否 | all | 开启本插件，group_id代表群号，不填则默认为当前群（如果是私聊的话得加上group_id） |
| del_group [group_id?] | 管理/群主/主人 | 否 | all | 关闭本插件，group_id代表群号，不填则默认为当前群（如果是私聊的话得加上group_id） |
| appeal | all | 否 | 私聊 | 当机器人误判违禁词时，可发送此指令以申诉 |
| operate [同意/拒绝] [user_id] [ban?] | 管理/群主/主人 | 是 | 私聊 | 同意/拒绝申诉，ban代表是否踢出，目前可选t（踢出），tm（踢出且不接受此人申请）不填则不踢出|