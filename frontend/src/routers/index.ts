import { createRouter, createWebHistory } from 'vue-router'

import { useStatusStore } from '@/stores/useStatusStore'

const routes = [
    {
        path: '',
        name: 'Index',
        component: () => import('@/views/Index.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/login',
        name: 'Login',
        component: () => import('@/views/Login.vue')
    },
    {
        path: '/chat',
        name: 'Chat',
        component: () => import('@/views/Chat.vue'),
        meta: { requiresAuth: true }
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

router.beforeEach(to => {
    const statusStore = useStatusStore();

    if (to.meta.requiresAuth && !statusStore.isLoggedIn) {
        return '/login'   // 重定向到登录页
    }
})

export default router
