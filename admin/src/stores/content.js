import { defineStore } from 'pinia'
import { api } from '../api/client'

export const useContentStore = defineStore('content', {
  state: () => ({
    datasets: [],
    selectedDataset: 'production',
    contentTypes: [],
    selectedType: null,
    entries: [],
    entryMeta: null,
    deliveryTokens: [],
    loading: false,
    error: '',
  }),
  actions: {
    async fetchDatasets() {
      const { data } = await api.get('/datasets')
      this.datasets = data
      if (!this.datasets.some((d) => d.name === this.selectedDataset) && this.datasets.length) {
        this.selectedDataset = this.datasets[0].name
      }
    },
    async createDataset(payload) {
      const { data } = await api.post('/datasets', payload)
      this.datasets.push(data)
      return data
    },
    async fetchContentTypes() {
      this.loading = true
      this.error = ''
      try {
        const { data } = await api.get('/content-types', { params: { dataset: this.selectedDataset } })
        this.contentTypes = data
        if (!this.selectedType && data.length) {
          this.selectedType = data[0]
        } else if (this.selectedType) {
          const latest = data.find((ct) => ct.id === this.selectedType.id)
          this.selectedType = latest || data[0] || null
        }
      } catch (err) {
        this.error = err.response?.data?.error || 'Failed to load content types'
      } finally {
        this.loading = false
      }
    },
    async createContentType(payload) {
      const request = { ...payload, datasetId: this.datasets.find((d) => d.name === this.selectedDataset)?.id }
      const { data } = await api.post('/content-types', request)
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
      search.set('dataset', this.selectedDataset)
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null && v !== '') search.set(k, String(v))
      })

      const { data } = await api.get(`/${apiId}?${search.toString()}`)
      this.entries = data.data
      this.entryMeta = data.meta
    },
    async createEntry(apiId, payload) {
      await api.post(`/${apiId}?dataset=${encodeURIComponent(this.selectedDataset)}`, payload)
      await this.fetchEntries(apiId)
    },
    async updateEntry(apiId, id, payload) {
      await api.put(`/${apiId}/${id}?dataset=${encodeURIComponent(this.selectedDataset)}`, payload)
      await this.fetchEntries(apiId)
    },
    async deleteEntry(apiId, id) {
      await api.delete(`/${apiId}/${id}?dataset=${encodeURIComponent(this.selectedDataset)}`)
      await this.fetchEntries(apiId)
    },
    async fetchTokens() {
      const { data } = await api.get('/datasets/tokens')
      this.deliveryTokens = data
    },
    async createToken(payload) {
      const { data } = await api.post('/datasets/tokens', payload)
      this.deliveryTokens.unshift(data)
      return data
    },
    async revokeToken(id) {
      await api.delete(`/datasets/tokens/${id}`)
      this.deliveryTokens = this.deliveryTokens.filter((t) => t.id !== id)
    },
  },
})
