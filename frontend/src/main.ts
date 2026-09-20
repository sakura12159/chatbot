import { createApp } from 'vue'
import App from '@/App.vue'
import { createPinia } from 'pinia'

import TDesign from 'tdesign-vue-next'
import TDesignChat from '@tdesign-vue-next/chat'; // 引入 Chat 组件
import 'tdesign-vue-next/es/style/index.css'; // 引入少量全局样式变量
import '@tdesign-vue-next/chat/es/style/index.css';

import router from '@/routers/index.ts';

const app = createApp(App);
app.use(createPinia())
   .use(TDesign)
   .use(TDesignChat)
   .use(router)
   .mount('#app');
