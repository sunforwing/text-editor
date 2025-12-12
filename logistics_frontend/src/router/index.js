import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '@/layout/MainLayout.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/login/LoginView.vue'),
      meta: { title: '登录' }
    },
    {
      path: '/',
      component: MainLayout,
      redirect: '/station/entry',
      children: [
        {
          path: 'station/entry',
          name: 'ParcelEntry',
          component: () => import('@/views/station/ParcelEntry.vue'),
          meta: { title: '运单录入' }
        },
        {
          path: 'tracking',
          name: 'Tracking',
          component: () => import('@/views/tracking/TraceResult.vue'),
          meta: { title: '轨迹查询' }
        }
      ]
    },
    // 移动端独立路由（不使用 MainLayout）
    {
      path: '/courier/tasks',
      name: 'CourierTasks',
      component: () => import('@/views/courier/MyTasks.vue'),
      meta: { title: '我的派送' }
    }
  ]
})

export default router