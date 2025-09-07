export const RES_BASE_URL = "/static/res/logo/"
export const Avatar = (url) => {
  if (!url) {
    return '/static/logo.svg'; // 默认头像
  }
  if (url.startsWith('http://') || url.startsWith('https://')) {
      return url; // 远程URL直接返回
    }
    if (url.startsWith('/')) {
      return url; // 绝对路径直接返回
    }
    return `${RES_BASE_URL}${url}`; // 相对路径加上基础路径
}