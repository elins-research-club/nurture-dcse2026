import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginPage.vue'),
      meta: { requiresGuest: true }
    },
    {
      path: '/',
      redirect: '/dashboard'
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('@/views/DashboardPage.vue')
    },
    {
      path: '/nodes',
      name: 'nodes',
      component: () => import('@/views/NodesPage.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/nodes/:id',
      name: 'node-detail',
      component: () => import('@/views/NodeDetailPage.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('@/views/SettingsPage.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/logs',
      name: 'logs',
      component: () => import('@/views/AlertsPage.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/alerts',
      redirect: '/logs'
    },
    {
      path: '/logs-export',
      redirect: '/logs'
    },
    {
      path: '/map',
      name: 'map',
      component: () => import('@/views/MapPage.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/maps',
      redirect: '/map'
    }
  ]
})

router.beforeEach((to, from, next) => {
  const auth = useAuthStore()
  
  if (to.meta.requiresAuth && !auth.isAuthenticated()) {
    next('/login')
  } else if (to.meta.requiresGuest && auth.isAuthenticated()) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router

router.onError((error, to) => {
  if (error.message.includes('Failed to fetch dynamically imported module')) {
    window.location.href = to.fullPath
  }
})
