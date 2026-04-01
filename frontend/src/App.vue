<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from './services/api'

const router = useRouter()
const me = ref(null)

async function refreshUser() {
  try {
    me.value = await api.me()
  } catch {
    me.value = null
  }
}

async function logout() {
  await api.logout()
  me.value = null
  await router.push('/login')
}

onMounted(refreshUser)
</script>

<template>
  <div class="min-h-screen bg-slate-50 text-slate-900">
    <header class="border-b border-slate-200 bg-white">
      <div class="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
        <h1 class="text-lg font-semibold">Vue CMS Admin</h1>
        <div class="flex items-center gap-2" v-if="me">
          <span class="rounded-full bg-slate-100 px-3 py-1 text-sm">{{ me.username }} ({{ me.role }})</span>
          <button class="rounded bg-slate-800 px-3 py-1.5 text-sm text-white" @click="logout">Logout</button>
        </div>
      </div>
    </header>
    <main class="mx-auto max-w-7xl p-4">
      <RouterView @auth-changed="refreshUser" />
    </main>
  </div>
</template>
