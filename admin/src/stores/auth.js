import { defineStore } from 'pinia'
import { api, setToken } from '../api/client'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: localStorage.getItem('cms_token'),
    loading: false,
    error: '',
  }),
  actions: {
    async register(payload) {
      this.loading = true
      this.error = ''
      try {
        const { data } = await api.post('/auth/register', payload)
        this.token = data.token
        this.user = data.user
        setToken(data.token)
      } catch (err) {
        this.error = err.response?.data?.error || 'Register failed'
        throw err
      } finally {
        this.loading = false
      }
    },
    async login(payload) {
      this.loading = true
      this.error = ''
      try {
        const { data } = await api.post('/auth/login', payload)
        this.token = data.token
        this.user = data.user
        setToken(data.token)
      } catch (err) {
        this.error = err.response?.data?.error || 'Login failed'
        throw err
      } finally {
        this.loading = false
      }
    },
    async fetchMe() {
      if (!this.token) return null
      try {
        const { data } = await api.get('/auth/me')
        this.user = data.user
        return data.user
      } catch {
        this.logout()
        return null
      }
    },
    logout() {
      this.user = null
      this.token = null
      setToken(null)
    },
  },
})
