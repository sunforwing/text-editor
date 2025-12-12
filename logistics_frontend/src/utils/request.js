import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建 axios 实例
const service = axios.create({
  // Vite 环境变量，开发时通过 proxy 代理到后端 Python 服务
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1', 
  timeout: 10000 
})

// 请求拦截器 (添加 Token)
service.interceptors.request.use(
  config => {
    // 假设 Token 存在 localStorage
    const token = localStorage.getItem('token')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  error => Promise.reject(error)
)

// 响应拦截器
service.interceptors.response.use(
  response => response.data,
  error => {
    ElMessage.error(error.response?.data?.message || '网络请求错误')
    return Promise.reject(error)
  }
)

export default service