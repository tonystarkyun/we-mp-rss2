 
from bs4 import BeautifulSoup
import re
from core.log import logger
def format_content(content:str,content_format:str='html'):
    #格式化内容
    # content_format: 'text' or 'markdown' or 'html'
    # content: str
    # return: str
    try:
        if content_format == 'text':
            # 去除HTML标签，保留纯文本
            soup = BeautifulSoup(content, 'html.parser')
            text = soup.get_text().strip()
            content = re.sub(r'\n\s*\n', '\n\n', text)
        elif content_format == 'markdown':
            from markdownify import markdownify as md
            # 转换HTML到Markdown
            content = md(content, heading_style="ATX", bullets='-*+', code_language='python')
            # 替换多个连续换行符为单个换行符
            # content = re.sub(r'\n\s*', '', content)
            content = re.sub(r'\n+', '\n', content)
    except Exception as e:
        logger.error('format_content error: %s',e)
    return content