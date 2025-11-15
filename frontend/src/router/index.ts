/**
 * Vue Router configuration
 */
import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: () => import('@/views/Dashboard.vue')
    },
    {
      path: '/terminal',
      name: 'terminal',
      component: () => import('@/views/TerminalTest.vue')
    }
  ]
})

export default router
