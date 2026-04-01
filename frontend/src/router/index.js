import { createRouter, createWebHistory } from 'vue-router'
import { api } from '../services/api'
import LoginPage from '../pages/LoginPage.vue'
import RegisterPage from '../pages/RegisterPage.vue'
import DashboardPage from '../pages/DashboardPage.vue'

const routes = [
  { path: '/login', name: 'login', component: LoginPage, meta: { guestOnly: true } },
  { path: '/register', name: 'register', component: RegisterPage, meta: { guestOnly: true } },
  { path: '/', name: 'dashboard', component: DashboardPage, meta: { requiresAuth: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  try {
    await api.me()
    if (to.meta.guestOnly) {
      return { name: 'dashboard' }
    }
  } catch {
    if (to.meta.requiresAuth) {
      return { name: 'login' }
    }
  }
  return true
})

export default router
