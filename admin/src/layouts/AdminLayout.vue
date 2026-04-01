<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <div class="min-h-screen bg-slate-100">
    <header class="border-b border-slate-200 bg-white">
      <div class="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
        <div>
          <h1 class="text-lg font-semibold">Headless CMS Admin</h1>
          <p class="text-sm text-slate-500">Custom Strapi-like platform</p>
        </div>
        <div class="flex items-center gap-3">
          <span class="rounded-full bg-slate-100 px-3 py-1 text-sm">{{ auth.user?.email }} ({{ auth.user?.role }})</span>
          <button class="rounded bg-slate-800 px-3 py-1.5 text-sm text-white" @click="logout">Logout</button>
        </div>
      </div>
    </header>

    <main class="mx-auto max-w-7xl p-4">
      <slot />
    </main>
  </div>
</template>
