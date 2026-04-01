import { defineStore } from 'pinia'
import { api } from '../api/client'

export const useContentStore = defineStore('content', {
  state: () => ({
    contentTypes: [],
    selectedType: null,
    entries: [],
    entryMeta: null,
    loading: false,
    error: '',
  }),
  actions: {
    async fetchContentTypes() {
      this.loading = true
      this.error = ''
      try {
        const { data } = await api.get('/content-types')
        this.contentTypes = data
        if (!this.selectedType && data.length) {
          this.selectedType = data[0]
        }
      } catch (err) {
        this.error = err.response?.data?.error || 'Failed to load content types'
      } finally {
        this.loading = false
      }
    },
    async createContentType(payload) {
      const { data } = await api.post('/content-types', payload)
      this.contentTypes.unshift(data)
      this.selectedType = data
    },
    async updateContentType(id, payload) {
      const { data } = await api.put(`/content-types/${id}`, payload)
      this.contentTypes = this.contentTypes.map((ct) => (ct.id === id ? data : ct))
      this.selectedType = data
    },
    async fetchEntries(apiId, params = {}) {
      const search = new URLSearchParams()
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null && v !== '') search.set(k, String(v))
      })

      const { data } = await api.get(`/${apiId}?${search.toString()}`)
      this.entries = data.data
      this.entryMeta = data.meta
    },
    async createEntry(apiId, payload) {
      await api.post(`/${apiId}`, payload)
      await this.fetchEntries(apiId)
    },
    async updateEntry(apiId, id, payload) {
      await api.put(`/${apiId}/${id}`, payload)
      await this.fetchEntries(apiId)
    },
    async deleteEntry(apiId, id) {
      await api.delete(`/${apiId}/${id}`)
      await this.fetchEntries(apiId)
    },
  },
})
