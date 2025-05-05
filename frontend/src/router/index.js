import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '@/views/auth/LoginView/LoginView.vue'
import RegisterView from '@/views/auth/RegisterView/RegisterView.vue'
import Dashboard from '@/components/system/Dashboard/Dashboard.vue'
import { supabase } from '@/utils/supabase.js'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/login',
    },
    {
      path: '/login',
      name: 'Login',
      component: LoginView,
    },
    {
      path: '/register',
      name: 'Register',
      component: RegisterView,
    },
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: Dashboard,
      meta: { requiresAuth: true }, // mark as protected
    },
  ],
})

// 🔐 Global navigation guard
router.beforeEach(async (to, from, next) => {
  const {
    data: { session },
  } = await supabase.auth.getSession()

  if (to.meta.requiresAuth && !session) {
    next('/login') // redirect to login if not authenticated
  } else {
    next()
  }
})

export default router
