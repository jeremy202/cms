<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import AdminLayout from '../layouts/AdminLayout.vue'
import DynamicEntryForm from '../components/DynamicEntryForm.vue'
import { useContentStore } from '../stores/content'
import { useAuthStore } from '../stores/auth'
import { api } from '../api/client'

const content = useContentStore()
const auth = useAuthStore()

const builder = reactive({
  name: '',
  apiId: '',
  description: '',
  schema: {
    fields: [
      { name: 'title', displayName: 'Title', type: 'TEXT', required: true, unique: false, options: {}, order: 0 },
    ],
  },
})

const entryForm = ref({})
const query = reactive({ page: 1, pageSize: 20, sort: '', filterField: '', filterValue: '' })
const uploadResult = ref(null)

const selectedType = computed(() => content.selectedType)
const canManageTypes = computed(() => auth.user?.role === 'ADMIN')

function addField() {
  builder.schema.fields.push({
    name: `field_${builder.schema.fields.length + 1}`,
    displayName: `Field ${builder.schema.fields.length + 1}`,
    type: 'TEXT',
    required: false,
    unique: false,
    options: {},
    order: builder.schema.fields.length,
  })
}

function removeField(index) {
  builder.schema.fields.splice(index, 1)
}

async function createType() {
  await content.createContentType(builder)
  builder.name = ''
  builder.apiId = ''
  builder.description = ''
  builder.schema.fields = [{ name: 'title', displayName: 'Title', type: 'TEXT', required: true, unique: false, options: {}, order: 0 }]
}

async function selectType(type) {
  content.selectedType = type
  await content.fetchEntries(type.apiId)
  entryForm.value = {}
}

async function applyQuery() {
  if (!selectedType.value) return
  const params = { page: query.page, pageSize: query.pageSize, sort: query.sort }
  if (query.filterField && query.filterValue) {
    params[`filters[${query.filterField}]`] = query.filterValue
  }
  await content.fetchEntries(selectedType.value.apiId, params)
}

async function createEntry() {
  if (!selectedType.value) return
  await content.createEntry(selectedType.value.apiId, { data: entryForm.value, published: false })
  entryForm.value = {}
}

async function deleteEntry(id) {
  if (!selectedType.value) return
  await content.deleteEntry(selectedType.value.apiId, id)
}

async function uploadFile(event) {
  const file = event.target.files?.[0]
  if (!file) return

  const body = new FormData()
  body.append('file', file)
  const { data } = await api.post('/media', body)
  uploadResult.value = data
}

onMounted(async () => {
  await content.fetchContentTypes()
  if (content.selectedType) {
    await content.fetchEntries(content.selectedType.apiId)
  }
})
</script>

<template>
  <AdminLayout>
    <div class="grid gap-4 lg:grid-cols-3">
      <section class="space-y-4 lg:col-span-1">
        <article class="rounded-lg border border-slate-200 bg-white p-4">
          <h2 class="text-lg font-semibold">Content Types</h2>
          <p class="mt-1 text-sm text-slate-500">Schemas are stored as JSON and versioned.</p>

          <div class="mt-3 space-y-2">
            <button
              v-for="type in content.contentTypes"
              :key="type.id"
              class="w-full rounded border px-3 py-2 text-left text-sm"
              :class="selectedType?.id === type.id ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-200 bg-white'"
              @click="selectType(type)"
            >
              <div class="font-medium">{{ type.name }}</div>
              <div class="text-xs opacity-80">/{{ type.apiId }} · v{{ type.version }}</div>
            </button>
          </div>
        </article>

        <article v-if="canManageTypes" class="rounded-lg border border-slate-200 bg-white p-4">
          <h2 class="text-lg font-semibold">Builder</h2>
          <form class="mt-3 space-y-2" @submit.prevent="createType">
            <input v-model="builder.name" class="w-full rounded border border-slate-300 px-3 py-2" placeholder="Content type name" required />
            <input v-model="builder.apiId" class="w-full rounded border border-slate-300 px-3 py-2" placeholder="api id (optional)" />
            <textarea v-model="builder.description" class="w-full rounded border border-slate-300 px-3 py-2" rows="2" placeholder="description" />

            <div class="space-y-2 rounded border border-slate-200 p-3">
              <div class="flex items-center justify-between">
                <h3 class="text-sm font-medium">Fields</h3>
                <button type="button" class="rounded bg-slate-100 px-2 py-1 text-xs" @click="addField">Add field</button>
              </div>
              <div v-for="(field, index) in builder.schema.fields" :key="index" class="grid grid-cols-12 gap-2">
                <input v-model="field.name" class="col-span-4 rounded border border-slate-300 px-2 py-1 text-sm" placeholder="name" required />
                <input v-model="field.displayName" class="col-span-4 rounded border border-slate-300 px-2 py-1 text-sm" placeholder="label" required />
                <select v-model="field.type" class="col-span-3 rounded border border-slate-300 px-2 py-1 text-sm">
                  <option>TEXT</option>
                  <option>NUMBER</option>
                  <option>BOOLEAN</option>
                  <option>MEDIA</option>
                  <option>RELATION</option>
                  <option>RICH_TEXT</option>
                </select>
                <button type="button" class="col-span-1 rounded bg-red-100 text-red-700" @click="removeField(index)">×</button>
                <label class="col-span-6 text-xs"><input v-model="field.required" type="checkbox" /> required</label>
                <label class="col-span-6 text-xs"><input v-model="field.unique" type="checkbox" /> unique</label>
              </div>
            </div>

            <button class="w-full rounded bg-slate-900 px-3 py-2 text-white">Create content type</button>
          </form>
        </article>
      </section>

      <section class="space-y-4 lg:col-span-2">
        <article class="rounded-lg border border-slate-200 bg-white p-4">
          <h2 class="text-lg font-semibold">Content Manager</h2>
          <p class="mt-1 text-sm text-slate-500">Dynamic form generated from selected schema.</p>

          <div v-if="selectedType" class="mt-3 space-y-3">
            <DynamicEntryForm v-model="entryForm" :fields="selectedType.schemaFields" />
            <button class="rounded bg-slate-900 px-3 py-2 text-white" @click="createEntry">Create entry</button>

            <div class="grid gap-2 rounded border border-slate-200 p-3 md:grid-cols-4">
              <input v-model="query.filterField" class="rounded border border-slate-300 px-2 py-1 text-sm" placeholder="filter field" />
              <input v-model="query.filterValue" class="rounded border border-slate-300 px-2 py-1 text-sm" placeholder="filter value" />
              <input v-model="query.sort" class="rounded border border-slate-300 px-2 py-1 text-sm" placeholder="sort e.g. title:asc" />
              <button class="rounded bg-slate-100 px-3 py-1 text-sm" @click="applyQuery">Apply query</button>
            </div>

            <div class="space-y-2">
              <article v-for="entry in content.entries" :key="entry.id" class="rounded border border-slate-200 bg-slate-50 p-3">
                <div class="flex items-center justify-between">
                  <span class="font-mono text-xs text-slate-500">{{ entry.id }}</span>
                  <button class="rounded bg-red-100 px-2 py-1 text-xs text-red-700" @click="deleteEntry(entry.id)">Delete</button>
                </div>
                <pre class="mt-2 overflow-auto rounded bg-white p-2 text-xs">{{ entry.data }}</pre>
              </article>
            </div>
          </div>

          <p v-else class="mt-3 text-sm text-slate-500">Select or create a content type to begin.</p>
        </article>

        <article class="rounded-lg border border-slate-200 bg-white p-4">
          <h2 class="text-lg font-semibold">Media Upload</h2>
          <p class="mt-1 text-sm text-slate-500">Upload files and link resulting URL in MEDIA fields.</p>
          <input class="mt-3" type="file" @change="uploadFile" />
          <div v-if="uploadResult" class="mt-3 rounded border border-slate-200 bg-slate-50 p-3 text-sm">
            <p><strong>File:</strong> {{ uploadResult.originalName }}</p>
            <p><strong>URL:</strong> <a class="text-blue-600" :href="uploadResult.url" target="_blank">{{ uploadResult.url }}</a></p>
          </div>
        </article>
      </section>
    </div>
  </AdminLayout>
</template>
