import { createRouter, createWebHistory } from 'vue-router';
import HomeView from '@/views/HomeView.vue';

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    // Future routes:
    // {
    //   path: '/workbench/:taskId',
    //   name: 'workbench',
    //   component: () => import('@/views/WorkbenchView.vue'),
    // },
  ],
});

export default router;
