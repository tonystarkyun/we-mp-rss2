import requests
import json
from core.models import Feed
from driver.wx import DoSuccess
from core.db import DB
from core.models.feed import Feed
from .cfg import cfg,wx_cfg
from core.print import print_error,print_info
from core.rss import RSS
from driver.success import WX_LOGIN_ED,WX_LOGIN_INFO
import random
# 定义一些常见的 User-Agent
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Android 11; Mobile; rv:89.0) Gecko/89.0 Firefox/89.0",
    # Chrome 桌面端
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    # Firefox 桌面端
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13.4; rv:109.0) Gecko/20100101 Firefox/114.0",
    # Safari 桌面端
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
    # Edge 桌面端
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.67",
    # Android 移动端 Chrome
    "Mozilla/5.0 (Linux; Android 13; SM-S901B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36",
    # Android 移动端 Firefox
    "Mozilla/5.0 (Android 13; Mobile; rv:109.0) Gecko/109.0 Firefox/114.0",
    # iOS 移动端 Safari
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1"
]
# 定义基类
class WxGather:
    articles=[]
    aids=[]
    def all_count(self):
        if getattr(self, 'articles', None) is not None:
            return len(self.articles)
        return 0
    def RecordAid(self,aid:str):
        self.aids.append(aid)
        pass
    def HasGathered(self,aid:str):
        if aid in self.aids:
            return True
        self.RecordAid(aid)
        return False
    def Model(self):
        type=cfg.get("gather.model","web")
        
        if type=="app":
            from core.wx import MpsAppMsg
            wx=MpsAppMsg()
        elif type=="web":
            from core.wx import MpsWeb
            wx=MpsWeb()
        else:
            from core.wx import MpsApi
            wx=MpsApi()
        return wx
    def __init__(self,is_add:bool=False):
        self.articles=[]
        self.is_add=is_add
        self._cookies={}
        session=  requests.Session()
        timeout = (5, 10)  
        session.timeout = timeout
        self.session=session
        self.get_token()
    def get_token(self):
        cfg.reload()
        wx_cfg.reload()
        self.Gather_Content=cfg.get('gather.content',False)
        self.user_agent = cfg.get('user_agent', '')
        self.cookies = wx_cfg.get('cookie', '')
        self.token=wx_cfg.get('token','')
        self.headers = {
            "Cookie":self.cookies,
            "User-Agent": self.user_agent 
        }
    def content_extract(self,  url):
        text=""
        try:
            session=self.session
            # 随机选择一个 User-Agent
            user_agent = random.choice(USER_AGENTS)
            # 更新请求头
            headers = self.headers.copy()
            headers.update({
                "User-Agent": user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive"
            })
            r = session.get(url, headers=headers)
            if r.status_code == 200:
                text = r.text
                if "当前环境异常，完成验证后即可继续访问" in text:
                    print_error("当前环境异常，完成验证后即可继续访问")
                    text=""
        except:
            pass
        return text
    def FillBack(self,CallBack=None,data=None,Ext_Data=None):
        if CallBack is not None:
            if data is not  None:
                WX_LOGIN_ED=True
                from core.models import Article
                from datetime import datetime
                art={
                    "id":str(data['id']),
                    "mp_id":data['mp_id'],
                    "title":data['title'],
                    "url":data['link'],
                    "pic_url":data['cover'],
                    "content":data.get("content",""),
                    "publish_time":data['update_time'],
                }
                if 'digest' in data:
                    art['description']=data['digest']
                if CallBack(art):
                    art["ext"]=Ext_Data
                    # art.pop("content")
                    self.articles.append(art)


    #通过公众号码平台接口查询公众号
    def search_Biz(self,kw:str="",limit=10,offset=0):

        self.get_token()
        url = "https://mp.weixin.qq.com/cgi-bin/searchbiz"
        params = {
            "action": "search_biz",
            "begin":offset,
            "count": limit,
            "query": kw,
            "token":  self.token,
            "lang": "zh_CN",
            "f": "json",
            "ajax": "1"
        }
        headers = {
            "Cookie": self.cookies,
            "User-Agent":self.user_agent
        }
        if self.token is None or self.token == "":
            self.Error("请先扫码登录公众号平台")
            return
        data={}
        try:
            response = requests.get(
            url,
            params=params,
            headers=headers,
            )
            response.raise_for_status()  # 检查状态码是否为200
            data = response.text  # 解析JSON数据
            msg = json.loads(data)  # 手动解析
            if msg['base_resp']['ret'] == 200013:
                self.Error("frequencey control, stop at {}".format(str(kw)))
                return
            if msg['base_resp']['ret'] != 0:
                self.Error("错误原因:{}:代码:{}".format(msg['base_resp']['err_msg'],msg['base_resp']['ret']),code="Invalid Session")
                return 
            if 'publish_page' in msg:
                msg['publish_page']=json.loads(msg['publish_page'])
        except Exception as e:
            print_error(f"请求失败: {e}")
            raise e
        return msg
    
    
    
    def Start(self,mp_id=None):
        self.articles=[]
        self.get_token()
        if self.token=="" or self.token is None:
             self.Error("请先扫码登录公众号平台")
             return
        import time
        self.update_mps(mp_id,Feed(
          sync_time=int(time.time()),
          update_time=int(time.time()),
        ))

    def Item_Over(self,item=None,CallBack=None):
        print(f"item end")
        _cookies=[{'name': c.name, 'value': c.value, 'domain': c.domain,'expiry':c.expires,'expires':c.expires} for c in self._cookies]
        _cookies.append({'name':'token','value':self.token})
        if len(_cookies) > 0:   
            # DoSuccess(_cookies)
            pass
        if CallBack is not None:
            CallBack(item)
        pass
    def Error(self,error:str,code=None):
        self.Over()
        if code=="Invalid Session":
            from jobs.failauth import send_wx_code
            WX_LOGIN_ED=False
            send_wx_code(f"公众号平台登录失效,请重新登录")
            pass
        raise Exception(error)

    def Over(self,CallBack=None):
        if getattr(self, 'articles', None) is not None:
            print(f"成功{len(self.articles)}条")
            rss=RSS()
            mp_id=""
            try:
                mp_id=self.articles[0]['mp_id']
            except:
                pass
            rss.clear_cache(mp_id=mp_id)  
        if CallBack is not None:
            CallBack(self)

    def dateformat(self,timestamp:any):
        from datetime import datetime, timezone
        # UTC时间对象
        utc_dt = datetime.fromtimestamp(int(timestamp), timezone.utc)
        t=(utc_dt.strftime("%Y-%m-%d %H:%M:%S")) 

        # UTC转本地时区
        local_dt = utc_dt.astimezone()
        t=(local_dt.strftime("%Y-%m-%d %H:%M:%S"))
        return t

    # 更新公众号更新状态
    def update_mps(self,mp_id:str, mp:Feed):
        """更新公众号同步状态和时间信息
        Args:
            mp_id: 公众号ID
            mp: Feed对象，包含公众号信息
        """
        from datetime import datetime
        import time
        try:
            
            # 更新同步时间为当前时间
            current_time = int(time.time())
            update_data = {
                'sync_time': current_time,
                # 'updated_at': dateformat(current_time)
                'updated_at': datetime.now(),
            }
            
            # 如果有新文章时间，也更新update_time
            if hasattr(mp, 'update_time') and mp.update_time:
                update_data['update_time'] = mp.update_time
            if hasattr(mp,'status') and mp.status is not None:
                update_data['status']=mp.status

            # 获取数据库会话并执行更新
            session = DB.get_session()
            try:
                feed = session.query(Feed).filter(Feed.id == mp_id).first()
                if feed:
                    for key, value in update_data.items():
                        print(f"更新公众号{mp_id}的{key}为{value}")
                        setattr(feed, key, value)
                    session.commit()
                else:
                    print_error(f"未找到ID为{mp_id}的公众号记录")
            finally:
                pass
                
        except Exception as e:
            print_error(f"更新公众号状态失败: {e}")
            raise NotImplementedError(f"更新公众号状态失败:{str(e)}")