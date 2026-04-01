const JSON_HEADERS = { 'Content-Type': 'application/json' }

async function request(path, options = {}) {
  const response = await fetch(path, {
    credentials: 'include',
    headers: { ...JSON_HEADERS, ...(options.headers || {}) },
    ...options,
  })

  const contentType = response.headers.get('content-type') || ''
  const body = contentType.includes('application/json') ? await response.json() : await response.text()

  if (!response.ok) {
    const message = typeof body === 'string' ? body : body.error || 'Request failed'
    throw new Error(message)
  }

  return body
}

export const api = {
  me: () => request('/api/me'),
  register: (payload) => request('/auth/register', { method: 'POST', body: JSON.stringify(payload) }),
  login: (payload) => request('/auth/login', { method: 'POST', body: JSON.stringify(payload) }),
  logout: () => request('/auth/logout', { method: 'POST' }),

  listWebsites: (query = '') => request(`/api/websites${query ? `?${query}` : ''}`),
  createWebsite: (payload) => request('/api/websites', { method: 'POST', body: JSON.stringify(payload) }),
  updateWebsite: (id, payload) => request(`/api/websites/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  deleteWebsite: (id) => request(`/api/websites/${id}`, { method: 'DELETE' }),

  listPages: (websiteId) => request(`/api/websites/${websiteId}/pages`),
  createPage: (websiteId, payload) => request(`/api/websites/${websiteId}/pages`, { method: 'POST', body: JSON.stringify(payload) }),
  updatePage: (pageId, payload) => request(`/api/pages/${pageId}`, { method: 'PUT', body: JSON.stringify(payload) }),
  deletePage: (pageId) => request(`/api/pages/${pageId}`, { method: 'DELETE' }),

  listDeployments: (websiteId) => request(`/api/websites/${websiteId}/deployments`),
  createDeployment: (websiteId, payload) => request(`/api/websites/${websiteId}/deployments`, { method: 'POST', body: JSON.stringify(payload) }),
  updateDeployment: (deploymentId, payload) => request(`/api/deployments/${deploymentId}`, { method: 'PUT', body: JSON.stringify(payload) }),
  deleteDeployment: (deploymentId) => request(`/api/deployments/${deploymentId}`, { method: 'DELETE' }),
}
