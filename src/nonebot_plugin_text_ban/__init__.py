import json

from pypinyin import lazy_pinyin
from nonebot import on_message, require, logger, get_driver

require("nonebot_plugin_alconna")
require("nonebot_plugin_localstore")

from nonebot_plugin_alconna import Args, Alconna, on_alconna, Match, Field, Arparma
from nonebot_plugin_localstore import get_plugin_data_file
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Bot, GROUP_ADMIN, GROUP_OWNER, MessageEvent
from nonebot.permission import SUPERUSER
from nonebot_plugin_alconna.uniseg import Image, Target, SupportScope, UniMessage, Text
from .config import plugin_config, Config
from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="违禁词撤回",
    description="违禁词检测，检测到违禁词则禁言",
    usage="发送：前缀+help查看方法",
    config=Config,
    type= "application",
    homepage="https://github.com/zhongwen-4/nonebot-plugin-text-ban",
    supported_adapters={"~onebot.v11"}
)

driver = get_driver()
path = get_plugin_data_file("data.json")
is_msg = on_message(block= False)
help = on_alconna(Alconna("help"), permission= SUPERUSER | GROUP_ADMIN | GROUP_OWNER, use_cmd_start= True)
add_text = on_alconna(Alconna("add", Args['text', str]["model", int]), permission= SUPERUSER | GROUP_ADMIN | GROUP_OWNER)
del_text = on_alconna(Alconna("del", Args['text', str]["model", int]), permission= SUPERUSER | GROUP_ADMIN | GROUP_OWNER)
add_group = on_alconna(Alconna("add_group", Args['group?', int]), permission= SUPERUSER | GROUP_OWNER | GROUP_ADMIN)
del_group = on_alconna(Alconna("del_group", Args['group?', int]), permission= SUPERUSER | GROUP_OWNER | GROUP_ADMIN)
operate = on_alconna(Alconna("operate", Args["operate", str]["user", int]["ban?", str]), permission= SUPERUSER | GROUP_OWNER | GROUP_ADMIN)
get_list = on_alconna(Alconna("list"), permission= SUPERUSER | GROUP_ADMIN | GROUP_OWNER)

alc = Alconna(
    "appeal",
    Args["user_id", int, Field(completion=lambda: "请输入你的QQ号")],
    Args["group_id", int, Field(completion=lambda: "你在哪个群被禁言了[群号]")],
    Args["appeal", str | Image, Field(completion=lambda: "你发了什么[图片/文本]")],
    Args["sure", str, Field(completion=lambda: "你确定要申诉吗？[y/n]\n注意：如果你使用的是虚假信息管理可能直接把你飞出群聊, 且本消息一经发送无法修改")]
)
appeal = on_alconna(alc, comp_config={"lite": True}, skip_for_unmatch=False)


def load_data(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
    

def with_data(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


async def ban(bot: Bot, event: GroupMessageEvent):
    await bot.delete_msg(message_id= event.message_id)
    await bot.set_group_ban(group_id= event.group_id, user_id= event.user_id, duration= 60 * 60)

    if plugin_config.kick:
        data = load_data(path)
        if str(event.user_id) not in data:
            data[str(event.user_id)] = 1
        
        else:
            data[str(event.user_id)] = data[str(event.user_id)] + 1
            if data[str(event.user_id)] == 3:
                await bot.set_group_kick(group_id= event.group_id, user_id= event.user_id)
                del data[str(event.user_id)]
        
        with_data(data, path)
        return f"你的消息中含有违禁词，请修改后发送。\nPS: 你也可以私聊我使用 appeal 申诉\n警告: 你已触发{data[str(event.user_id)]}次违禁词，再触发{3 - data[str(event.user_id)]}将被踢出群聊"
    
    else:
        return "你的消息含有违禁词，请修改后发送。\nPS: 你也可以私聊我使用 appeal 申诉"


@driver.on_startup
async def on_startup():
    try:
        load_data(path)
    except FileNotFoundError:
        data= {}
        with_data(data, path)
        logger.info("未找到数据文件，已创建")
        
    logger.info(str(path))


@is_msg.handle()
async def is_msg_handle(bot: Bot, event: GroupMessageEvent):
    msg = event.message.extract_plain_text()
    data = load_data(path)

    user_info = await bot.get_group_member_info(group_id= event.group_id, user_id= event.user_id)
    if user_info["role"] == "owner" or user_info["role"] == "admin":
        logger.debug("发送人是管理员或者群主，已忽略")
        return
    
    admin = driver.config.superusers
    if str(event.user_id) in admin:
        logger.debug("发送人是超级用户，已忽略")
        return
    
    if event.group_id not in data["group"]:
        logger.debug("群聊未添加，已忽略")
        return
    
    if plugin_config.strict:
        for i in data["msg"]:
            set_a = set(i["text"])
            set_b = set(msg)

            if set_a.issubset(set_b):
                set_msg = await ban(bot, event)
                await add_text.finish(set_msg, at_sender= True)

    if plugin_config.pinyin:
        pinyin= set(i for i in data["msg"] for i in lazy_pinyin(i["text"]))
        pinyin_a = set(i for i in lazy_pinyin(msg))

        for i in data["msg"]:
            if i["type"] == 1:
                if pinyin == pinyin_a:
                    set_msg = await ban(bot, event)
                    await add_text.finish(set_msg, at_sender= True)
            
            if i["type"] == 2:
                if pinyin_a.issubset(pinyin) and pinyin_a != set():
                    set_msg = await ban(bot, event)
                    await add_text.finish(set_msg, at_sender= True)

    if plugin_config.ocr:
        for i in event.message:
            
            if i.type == "image":
                text = await bot.call_api("ocr_image", image= i.data["url"])
                try:
                    is_text = [a["text"] for a in text["texts"] if "text" in a]
                except TypeError:
                    logger.debug("OCR识别失败(你无需理会)")
                    break

                for i in data["msg"]:
                    if i["text"] in is_text:
                        set_msg = await ban(bot, event)
                        await add_text.finish(set_msg, at_sender= True)
    
    for i in data["msg"]:
        if i["type"] == 1:
            if i["text"] == msg:
                set_msg = await ban(bot, event)
                await add_text.finish(set_msg, at_sender= True)
        
        if i["type"] == 2:
            if i["text"] in msg:
                set_msg = await ban(bot, event)
                await add_text.finish(set_msg, at_sender= True)


@add_text.handle()
async def add_text_handle(text: Match[str], model: Match[int]):
    data = load_data(path)
    
    if model.result != 1 and model.result != 2:
        await add_text.finish("添加失败，参数错误")

    if "msg" not in data:
        data["msg"] = []
        data["msg"].append({"type": model.result, "text": text.result})
        with_data(data, path)
        await add_text.finish("添加成功")

    if not any(i["text"] == text.result and i["type"] == model.result for i in data["msg"]):
        data["msg"].append({"type": model.result, "text": text.result})
        with_data(data, path)
        await add_text.finish("添加成功")
    
    else:
        await add_text.finish("添加失败，词条已存在")


@del_text.handle()
async def del_text_handle(text: Match[str], model: Match[int]):
    data = load_data(path)

    if "msg" not in data:
        await del_text.finish("没有添加任何违禁词")
        
    if any(i["text"] == text.result and i["type"] == model.result for i in data["msg"]):
        data["msg"].remove(next(i for i in data["msg"] if i["text"] == text.result and i["type"] == model.result))
        with_data(data, path)
        await del_text.finish("删除成功")
    
    else:
        await del_text.finish("没有添加该违禁词")


@add_group.handle()
async def add_group_handle(event: GroupMessageEvent, group: Match[int]):
    data = load_data(path)

    if group.available:
        group_id = group.result
    else:
        group_id = event.group_id

    if "group" not in data:
        data["group"] = []
        data["group"].append(group_id)
        with_data(data, path)
        await add_group.finish("开启成功")

    if group_id not in data["group"]:
        data["group"].append(group_id)
        with_data(data, path)
        await add_group.finish("开启成功")
    
    if group_id in data["group"]:
        await add_group.finish("该群聊已存在")


@del_group.handle()
async def del_group_handle(event: GroupMessageEvent, group: Match[int]):
    data = load_data(path)

    if group.available:
        group_id = group.result
    else:
        group_id = event.group_id

    if "group" not in data:
        await del_group.finish("没有添加任何群聊")

    if group_id not in data["group"]:
        await del_group.finish("没有添加该群聊")

    data["group"].remove(group_id)
    with_data(data, path)
    await del_group.finish("关闭成功")


@appeal.handle()
async def appeal_handle(event: MessageEvent, cmd_data: Arparma):
    data = load_data(path)
    user_id = cmd_data.all_matched_args["user_id"]
    group_id = cmd_data.all_matched_args["group_id"]
    appeal_a = cmd_data.all_matched_args["appeal"]
    sure = cmd_data.all_matched_args["sure"]
    
    if isinstance(appeal_a, Image):
        msg = UniMessage(f"申诉通知：\n用户：{user_id}\n 群：{group_id}\n申诉内容：")
        msg += Image(url = appeal_a.url)
        msg += Text(f"PS：你可以使用 operate 同意 {user_id} 来同意该次申诉（更多参数请使用help命令查看，注意：help命令需要带上命令头）")

    else:
        msg = UniMessage(f"申诉通知：\n用户：{user_id}\n 群：{group_id}\n申诉内容：{appeal_a}")
    
    if "appeal" in data:
        if str(user_id) in data["appeal"]:
            target1 = Target(id= str(event.user_id), scope=SupportScope.qq_client, private= True)
            await UniMessage("你已经申诉过了").send(target1)
            return
    
    if sure == "n" or sure == "N":
        target1 = Target(id= str(event.user_id), scope=SupportScope.qq_client, private= True)
        await UniMessage("已取消申诉").send(target1)
        return

    data["appeal"] = {user_id: group_id}
    target1 = Target(id= str(event.user_id), scope=SupportScope.qq_client, private= True)
    await UniMessage("申诉成功，待管理员处理中").send(target1)

    with_data(data, path)
    for i in driver.config.superusers:
        target1 = Target(id= i, scope=SupportScope.qq_client, private= True)
        await msg.send(target1)
    return

@operate.handle()
async def agree_handle(bot: Bot, cmd_data: Arparma, event: MessageEvent, ban: Match[str]):
    data = load_data(path)
    user_id = cmd_data.all_matched_args["user"]
    Target1 = Target(user_id, private= True, scope=SupportScope.qq_client)

    if event.sub_type == "group":
        await operate.finish("该命令仅支持私聊使用")
    
    if "appeal" not in data:
        await operate.finish("当前没有申诉")

    if str(user_id) not in data["appeal"]:
        await operate.finish("该用户未申请/其他人同意过了")

    if cmd_data.all_matched_args["operate"] == "同意":
        
        if str(user_id) in data:
            if data[str(user_id)] > 1:
                data[str(user_id)] = data[str(user_id)] - 1
            else:
                del data[str(user_id)]

        await bot.set_group_ban(group_id=data["appeal"][str(user_id)], user_id= user_id, duration=0)
        del data["appeal"][str(user_id)]
        with_data(data, path)
        await UniMessage("申诉已通过").send(Target1)
        await operate.finish("操作成功")
    
    elif cmd_data.all_matched_args["operate"] == "拒绝":
        
        if ban.available:
            if ban.result == "t":
                await bot.set_group_kick(group_id=data["appeal"][str(user_id)], user_id= user_id)
            
            elif ban.result == "tm":
                await bot.set_group_kick(group_id=data["appeal"][str(user_id)], user_id= user_id, reject_add_request= True)

            else:
                await operate.finish("参数错误，可选参数：t/tm， 例：operate 拒绝 123456 t")

        del data["appeal"][str(user_id)]
        with_data(data, path)
        await UniMessage("申诉被拒绝").send(Target1)
        await operate.finish("拒绝成功")

    else:
        await operate.finish("参数错误, 可用参数：同意/拒绝，例：operate 同意 123456")


@help.handle()
async def help_handle():
    msg = [
        "违禁词帮助：",
        "add [text] [type]: 添加违禁词，type为1时是精确，为2是模糊",
        "del [text] [type]: 删除违禁词，type为1时是精确，为2是模糊",
        "add_group [group_id?]: 开启本群聊违禁词, group_id为群号",
        "del_group [group_id?]: 关闭本群聊违禁词, group_id为群号",
        "appeal: 申诉（内置会话补全，发送此命令会自动提示输入参数）",
        "operate [同意/拒绝] [ban?]: 同意/拒绝申诉，ban为t时是踢出，为tm时是踢出并拒绝加群申请",
        "PS: 参数中带?为可选参数"
    ]

    await help.finish("\n--------\n".join(msg))

@get_list.handle()
async def get_list_handle(bot: Bot, event: MessageEvent):
    from nonebot.adapters.onebot.v11 import MessageSegment, Message

    data = load_data(path)
    text_list = []

    if "msg" not in data:
        await get_list.finish("违禁词列表是空的")

    if not data["msg"]:
        await get_list.finish("违禁词列表是空的")

    for i in data["msg"]:
        if i["type"] == 1:
            text_list.append(f"{i['text']} --- 精确")
        
        if i["type"] == 2:
            text_list.append(f"{i['text']} --- 模糊")

    msg = Message(
        [
            MessageSegment.node_custom(
                user_id= event.user_id,
                nickname= event.sender.nickname if event.sender.nickname else "匿名用户",
                content= "违禁词列表"
            ),
            MessageSegment.node_custom(
                user_id= event.user_id,
                nickname= event.sender.nickname if event.sender.nickname else "匿名用户",
                content= "\n------\n".join(text_list)
            )
        ]
    )

    res_id = await bot.call_api("send_forward_msg", messages= msg)
    await get_list.finish(
        Message(
            MessageSegment.forward(res_id)
        )
    )