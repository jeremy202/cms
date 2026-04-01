<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '../services/api'

const loading = ref(true)
const error = ref('')
const websites = ref([])
const expandedWebsite = ref(null)
const pagesByWebsite = reactive({})
const deploymentsByWebsite = reactive({})

const filters = reactive({ q: '', status: 'all', tag: 'all', sort: 'newest' })

const websiteForm = reactive({ name: '', domain: '', tech_stack: '', status: 'active', tags: '' })

const pageDraft = reactive({ title: '', slug: '', seo_description: '', content_markdown: '', published: true })
const deploymentDraft = reactive({ provider: 'vercel', project_name: '', production_url: '', preview_url: '', branch: 'main', status: 'active' })

const availableTags = computed(() => {
  const tags = new Set()
  websites.value.forEach((site) => (site.tags || []).forEach((tag) => tags.add(tag)))
  return [...tags].sort()
})

function queryString() {
  const p = new URLSearchParams()
  if (filters.q) p.set('q', filters.q)
  if (filters.status !== 'all') p.set('status', filters.status)
  if (filters.tag !== 'all') p.set('tag', filters.tag)
  if (filters.sort) p.set('sort', filters.sort)
  return p.toString()
}

async function loadWebsites() {
  loading.value = true
  error.value = ''
  try {
    websites.value = await api.listWebsites(queryString())
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function createWebsite() {
  try {
    await api.createWebsite({ ...websiteForm })
    websiteForm.name = ''
    websiteForm.domain = ''
    websiteForm.tech_stack = ''
    websiteForm.status = 'active'
    websiteForm.tags = ''
    await loadWebsites()
  } catch (err) {
    error.value = err.message
  }
}

async function removeWebsite(id) {
  if (!confirm('Delete this website and all related data?')) return
  try {
    await api.deleteWebsite(id)
    if (expandedWebsite.value === id) {
      expandedWebsite.value = null
    }
    await loadWebsites()
  } catch (err) {
    error.value = err.message
  }
}

async function toggleWebsite(site) {
  if (expandedWebsite.value === site.id) {
    expandedWebsite.value = null
    return
  }

  expandedWebsite.value = site.id
  pagesByWebsite[site.id] = await api.listPages(site.id)
  deploymentsByWebsite[site.id] = await api.listDeployments(site.id)
}

async function createPage(siteId) {
  try {
    await api.createPage(siteId, { ...pageDraft, published: pageDraft.published ? 1 : 0 })
    pageDraft.title = ''
    pageDraft.slug = ''
    pageDraft.seo_description = ''
    pageDraft.content_markdown = ''
    pageDraft.published = true
    pagesByWebsite[siteId] = await api.listPages(siteId)
    await loadWebsites()
  } catch (err) {
    error.value = err.message
  }
}

async function removePage(pageId, siteId) {
  try {
    await api.deletePage(pageId)
    pagesByWebsite[siteId] = await api.listPages(siteId)
    await loadWebsites()
  } catch (err) {
    error.value = err.message
  }
}

async function createDeployment(siteId) {
  try {
    await api.createDeployment(siteId, { ...deploymentDraft })
    deploymentDraft.provider = 'vercel'
    deploymentDraft.project_name = ''
    deploymentDraft.production_url = ''
    deploymentDraft.preview_url = ''
    deploymentDraft.branch = 'main'
    deploymentDraft.status = 'active'
    deploymentsByWebsite[siteId] = await api.listDeployments(siteId)
    await loadWebsites()
  } catch (err) {
    error.value = err.message
  }
}

async function removeDeployment(deploymentId, siteId) {
  try {
    await api.deleteDeployment(deploymentId)
    deploymentsByWebsite[siteId] = await api.listDeployments(siteId)
    await loadWebsites()
  } catch (err) {
    error.value = err.message
  }
}

onMounted(loadWebsites)
</script>

<template>
  <div class="space-y-4">
    <section class="rounded-lg border border-slate-200 bg-white p-4">
      <h2 class="text-lg font-semibold">Create website</h2>
      <form class="mt-3 grid gap-2 md:grid-cols-5" @submit.prevent="createWebsite">
        <input v-model="websiteForm.name" class="rounded border border-slate-300 px-3 py-2" placeholder="Name" required />
        <input v-model="websiteForm.domain" class="rounded border border-slate-300 px-3 py-2" placeholder="Domain" required />
        <input v-model="websiteForm.tech_stack" class="rounded border border-slate-300 px-3 py-2" placeholder="Tech stack" />
        <input v-model="websiteForm.tags" class="rounded border border-slate-300 px-3 py-2" placeholder="tags, comma-separated" />
        <div class="flex gap-2">
          <select v-model="websiteForm.status" class="w-full rounded border border-slate-300 px-3 py-2">
            <option value="active">active</option>
            <option value="maintenance">maintenance</option>
            <option value="archived">archived</option>
          </select>
          <button class="rounded bg-slate-900 px-3 py-2 text-white">Add</button>
        </div>
      </form>
    </section>

    <section class="rounded-lg border border-slate-200 bg-white p-4">
      <h2 class="text-lg font-semibold">Search / filter / sort</h2>
      <form class="mt-3 grid gap-2 md:grid-cols-5" @submit.prevent="loadWebsites">
        <input v-model="filters.q" class="rounded border border-slate-300 px-3 py-2" placeholder="Search by name/domain/stack" />
        <select v-model="filters.status" class="rounded border border-slate-300 px-3 py-2">
          <option value="all">all statuses</option>
          <option value="active">active</option>
          <option value="maintenance">maintenance</option>
          <option value="archived">archived</option>
        </select>
        <select v-model="filters.tag" class="rounded border border-slate-300 px-3 py-2">
          <option value="all">all tags</option>
          <option v-for="tag in availableTags" :key="tag" :value="tag">{{ tag }}</option>
        </select>
        <select v-model="filters.sort" class="rounded border border-slate-300 px-3 py-2">
          <option value="newest">newest</option>
          <option value="oldest">oldest</option>
          <option value="name_asc">name a-z</option>
          <option value="name_desc">name z-a</option>
          <option value="pages_desc">most pages</option>
        </select>
        <button class="rounded bg-slate-900 px-3 py-2 text-white">Apply</button>
      </form>
    </section>

    <p v-if="error" class="rounded bg-red-50 px-3 py-2 text-sm text-red-700">{{ error }}</p>

    <section class="rounded-lg border border-slate-200 bg-white p-4">
      <h2 class="text-lg font-semibold">Websites</h2>
      <p v-if="loading" class="mt-3 text-sm text-slate-500">Loading...</p>

      <div v-else class="mt-3 space-y-3">
        <article v-for="site in websites" :key="site.id" class="rounded border border-slate-200 bg-slate-50 p-3">
          <div class="flex flex-wrap items-center justify-between gap-2">
            <div>
              <h3 class="font-semibold">{{ site.name }} <span class="text-sm font-normal text-slate-500">({{ site.domain }})</span></h3>
              <p class="text-sm text-slate-600">
                status: {{ site.status }} · pages: {{ site.page_count }} · deployments: {{ site.deployment_count }}
              </p>
              <div class="mt-1 flex flex-wrap gap-1" v-if="site.tags?.length">
                <span v-for="tag in site.tags" :key="tag" class="rounded-full bg-slate-200 px-2 py-0.5 text-xs">{{ tag }}</span>
              </div>
            </div>
            <div class="flex gap-2">
              <button class="rounded bg-slate-700 px-3 py-1.5 text-sm text-white" @click="toggleWebsite(site)">
                {{ expandedWebsite === site.id ? 'Hide' : 'Manage' }}
              </button>
              <button class="rounded bg-red-600 px-3 py-1.5 text-sm text-white" @click="removeWebsite(site.id)">Delete</button>
            </div>
          </div>

          <div v-if="expandedWebsite === site.id" class="mt-4 grid gap-4 lg:grid-cols-2">
            <section class="rounded border border-slate-200 bg-white p-3">
              <h4 class="font-semibold">Pages</h4>
              <form class="mt-2 space-y-2" @submit.prevent="createPage(site.id)">
                <input v-model="pageDraft.title" class="w-full rounded border border-slate-300 px-3 py-2" placeholder="Title" required />
                <input v-model="pageDraft.slug" class="w-full rounded border border-slate-300 px-3 py-2" placeholder="Slug" required />
                <input v-model="pageDraft.seo_description" class="w-full rounded border border-slate-300 px-3 py-2" placeholder="SEO description" />
                <textarea v-model="pageDraft.content_markdown" class="w-full rounded border border-slate-300 px-3 py-2" rows="5" placeholder="Markdown content"></textarea>
                <label class="flex items-center gap-2 text-sm"><input v-model="pageDraft.published" type="checkbox" /> Published</label>
                <button class="rounded bg-slate-900 px-3 py-2 text-sm text-white">Create page</button>
              </form>

              <ul class="mt-3 space-y-2 text-sm">
                <li v-for="page in pagesByWebsite[site.id] || []" :key="page.id" class="flex items-center justify-between rounded border border-slate-200 px-2 py-1">
                  <span>{{ page.title }} <span class="text-slate-500">/{{ page.slug }}</span></span>
                  <button class="rounded bg-red-100 px-2 py-1 text-xs text-red-700" @click="removePage(page.id, site.id)">Delete</button>
                </li>
              </ul>
            </section>

            <section class="rounded border border-slate-200 bg-white p-3">
              <h4 class="font-semibold">Deployments</h4>
              <form class="mt-2 grid gap-2" @submit.prevent="createDeployment(site.id)">
                <select v-model="deploymentDraft.provider" class="rounded border border-slate-300 px-3 py-2">
                  <option value="vercel">vercel</option>
                  <option value="netlify">netlify</option>
                </select>
                <input v-model="deploymentDraft.project_name" class="rounded border border-slate-300 px-3 py-2" placeholder="Project name" required />
                <input v-model="deploymentDraft.production_url" class="rounded border border-slate-300 px-3 py-2" placeholder="Production URL" />
                <input v-model="deploymentDraft.preview_url" class="rounded border border-slate-300 px-3 py-2" placeholder="Preview URL" />
                <input v-model="deploymentDraft.branch" class="rounded border border-slate-300 px-3 py-2" placeholder="Branch" />
                <select v-model="deploymentDraft.status" class="rounded border border-slate-300 px-3 py-2">
                  <option value="active">active</option>
                  <option value="paused">paused</option>
                  <option value="error">error</option>
                </select>
                <button class="rounded bg-slate-900 px-3 py-2 text-sm text-white">Create deployment</button>
              </form>

              <ul class="mt-3 space-y-2 text-sm">
                <li v-for="deployment in deploymentsByWebsite[site.id] || []" :key="deployment.id" class="flex items-center justify-between rounded border border-slate-200 px-2 py-1">
                  <span>{{ deployment.provider }} · {{ deployment.project_name }}</span>
                  <button class="rounded bg-red-100 px-2 py-1 text-xs text-red-700" @click="removeDeployment(deployment.id, site.id)">Delete</button>
                </li>
              </ul>
            </section>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>
