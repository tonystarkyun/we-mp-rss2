from core.config import Config,cfg
# 确保data目录和wx.lic文件存在
import os
lic_path="./data/wx.lic"
os.makedirs(os.path.dirname(lic_path), exist_ok=True)
if not os.path.exists(lic_path):
    with open(lic_path, "w") as f:
        f.write("{}")
wx_cfg = Config(lic_path)

def set_token(data:any):
    """
    设置微信登录的Token和Cookie信息
    :param data: 包含Token和Cookie信息的字典
    """
    wx_cfg.set("token", data.get("token", ""))
    wx_cfg.set("cookie", data.get("cookies_str", ""))
    wx_cfg.set("expiry", data.get("expiry", {}))
    wx_cfg.save_config()
    wx_cfg.reload()
    from jobs.notice import sys_notice
    sys_notice(f"WeRss授权成功", cfg.get("server.code_title","WeRss授权成功"))
    # cfg.set("token", data.get("token", ""))
    # cfg.save_config()
def get(key:str,default:any=None):
    wx_cfg.get(f"{key}",default)