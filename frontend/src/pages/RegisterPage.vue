<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../services/api'

const emit = defineEmits(['auth-changed'])
const router = useRouter()

const username = ref('')
const password = ref('')
const role = ref('editor')
const error = ref('')
const submitting = ref(false)

async function submit() {
  error.value = ''
  submitting.value = true
  try {
    await api.register({ username: username.value, password: password.value, role: role.value })
    emit('auth-changed')
    await router.push('/')
  } catch (err) {
    error.value = err.message
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="mx-auto mt-10 max-w-md rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
    <h2 class="mb-4 text-xl font-semibold">Create account</h2>
    <p v-if="error" class="mb-3 rounded bg-red-50 px-3 py-2 text-sm text-red-700">{{ error }}</p>
    <form class="space-y-3" @submit.prevent="submit">
      <label class="block text-sm font-medium">Username
        <input v-model="username" minlength="3" class="mt-1 w-full rounded border border-slate-300 px-3 py-2" required />
      </label>
      <label class="block text-sm font-medium">Password
        <input v-model="password" type="password" minlength="8" class="mt-1 w-full rounded border border-slate-300 px-3 py-2" required />
      </label>
      <label class="block text-sm font-medium">Role
        <select v-model="role" class="mt-1 w-full rounded border border-slate-300 px-3 py-2">
          <option value="editor">editor</option>
          <option value="admin">admin</option>
        </select>
      </label>
      <button :disabled="submitting" class="w-full rounded bg-slate-900 px-3 py-2 text-white disabled:opacity-50">{{ submitting ? 'Creating...' : 'Register' }}</button>
    </form>
    <p class="mt-4 text-sm text-slate-600">Already have an account? <RouterLink to="/login" class="text-blue-600">Login</RouterLink></p>
  </div>
</template>
