import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import { configureApiAuth } from './api/client'
import router from './router'
import { useAuthStore } from './stores/auth'
import './styles.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)

const authStore = useAuthStore(pinia)
configureApiAuth({
  getAccessToken: () => authStore.access,
  getRefreshToken: () => authStore.refresh,
  setAccessToken: (access) => authStore.setAccessToken(access),
  clearAuth: () => authStore.clearSession(),
})

app.use(router)
app.mount('#app')
