<script setup>
import { reactive, watch } from 'vue'

const props = defineProps({
  fields: { type: Array, required: true },
  modelValue: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['update:modelValue'])
const form = reactive({ ...props.modelValue })

watch(
  () => props.modelValue,
  (value) => {
    Object.assign(form, value || {})
  },
  { deep: true }
)

watch(
  form,
  (value) => {
    emit('update:modelValue', { ...value })
  },
  { deep: true }
)
</script>

<template>
  <div class="grid gap-3 md:grid-cols-2">
    <div v-for="field in fields" :key="field.id" class="space-y-1">
      <label class="block text-sm font-medium text-slate-700">{{ field.displayName }}</label>

      <input
        v-if="field.type === 'TEXT' || field.type === 'RICH_TEXT' || field.type === 'MEDIA' || field.type === 'RELATION'"
        v-model="form[field.name]"
        type="text"
        class="w-full rounded border border-slate-300 px-3 py-2"
        :placeholder="field.name"
      />

      <input
        v-else-if="field.type === 'NUMBER'"
        v-model.number="form[field.name]"
        type="number"
        class="w-full rounded border border-slate-300 px-3 py-2"
      />

      <label v-else-if="field.type === 'BOOLEAN'" class="flex items-center gap-2 text-sm">
        <input v-model="form[field.name]" type="checkbox" />
        Enabled
      </label>

      <p class="text-xs text-slate-500">type: {{ field.type }}</p>
    </div>
  </div>
</template>
