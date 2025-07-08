from wxauto import WeChat

wx = WeChat()
# 精确匹配群名，避免同名干扰
wx.SendMsg("你好", who="文件传输助手")
