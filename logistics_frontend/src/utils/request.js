import axios from 'axios'

const service = axios.create({
  baseURL: '/api/v1', // Matches the proxy configuration in vite.config.js and backend prefix
  timeout: 5000
})

// Request interceptor
service.interceptors.request.use(
  config => {
    // You can add token here if needed
    return config
  },
  error => {
    console.log(error)
    return Promise.reject(error)
  }
)

// Response interceptor
service.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    console.log('err' + error)
    return Promise.reject(error)
  }
)

export default service
