import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/login'
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView
    },
    {
      path: '/create-parcel',
      name: 'create-parcel',
      component: () => import('../views/CreateParcelView.vue')
    },
    {
      path: '/trace-parcel',
      name: 'trace-parcel',
      component: () => import('../views/ParcelTraceView.vue')
    },
    {
      path: '/transport-task',
      name: 'transport-task',
      component: () => import('../views/TransportTaskView.vue')
    },
    {
      path: '/delivery-task',
      name: 'delivery-task',
      component: () => import('../views/DeliveryTaskView.vue')
    }
  ]
})

export default router
