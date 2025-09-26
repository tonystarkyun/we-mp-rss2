import axios from 'axios'
import { getToken } from '@/utils/auth'
import { Message } from '@arco-design/web-vue'
import router from '@/router'
// 创建axios实例
const http = axios.create({
  baseURL: (import.meta.env.VITE_API_BASE_URL || '') + 'api/v1/',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
})

// 请求拦截器
http.interceptors.request.use(
  config => {
    const token = getToken()
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
http.interceptors.response.use(
  response => {
    // 处理标准响应格式
    if (response.data?.code === 0) {
      return response.data?.data||response.data?.detail||response.data||response
    }
    if(response.data?.code==401){
      router.push("/login")
      return Promise.reject("未登录或登录已过期，请重新登录。")
    }
    
    // 对于其他状态码，如果HTTP状态是成功的（200-299），返回原始响应
    if (response.status >= 200 && response.status < 300) {
      return response.data
    }
    
    const data=response.data?.detail||response.data
    const errorMsg = data?.message || '请求失败'
    if(response.headers['content-type']==='application/json') {
      Message.error(errorMsg)
    }else{
      return response.data
    }
    return Promise.reject(response.data)
  },
  error => {
     if(error.status==401){
      router.push("/login")
    } 
    console.log(error)
    // 统一错误处理
    const errorMsg = error?.response?.data?.detail?.message || 
                    error?.response?.data?.message || 
                    error.response?.data?.detail || 
                    error.message || 
                    '请求错误'
    
    // 检查是否是微信会话失效错误
    if (errorMsg.includes('invalid session') || 
        errorMsg.includes('代码:200003') || 
        errorMsg.includes('请重新扫码授权') ||
        errorMsg.includes('登录会话已失效')) {
      Message.error({
        content: '微信公众号平台登录会话已失效，请重新扫码登录',
        duration: 5000
      })
    }
    
    return Promise.reject(errorMsg)
  }
)

export default http