<script setup>
import { reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const form = reactive({ email: '', password: '', role: 'EDITOR' })

async function submit() {
  try {
    await auth.register(form)
    router.push('/')
  } catch {
    // handled in store
  }
}
</script>

<template>
  <div class="mx-auto mt-16 max-w-md rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
    <h2 class="text-2xl font-semibold">Create account</h2>
    <p class="mt-1 text-sm text-slate-500">Bootstrap your CMS team</p>

    <p v-if="auth.error" class="mt-3 rounded bg-red-50 px-3 py-2 text-sm text-red-700">{{ auth.error }}</p>

    <form class="mt-4 space-y-3" @submit.prevent="submit">
      <input v-model="form.email" type="email" class="w-full rounded border border-slate-300 px-3 py-2" placeholder="Email" required />
      <input v-model="form.password" type="password" class="w-full rounded border border-slate-300 px-3 py-2" placeholder="Password" required minlength="8" />
      <select v-model="form.role" class="w-full rounded border border-slate-300 px-3 py-2">
        <option value="EDITOR">EDITOR</option>
        <option value="ADMIN">ADMIN</option>
      </select>
      <button :disabled="auth.loading" class="w-full rounded bg-slate-900 px-3 py-2 text-white disabled:opacity-50">{{ auth.loading ? 'Loading...' : 'Register' }}</button>
    </form>

    <p class="mt-4 text-sm text-slate-600">Already registered? <RouterLink to="/login" class="text-blue-600">Login</RouterLink></p>
  </div>
</template>
