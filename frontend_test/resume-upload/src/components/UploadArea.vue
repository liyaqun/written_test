<script setup>
import { ref } from 'vue'
import IconUpload from './IconUpload.vue'

defineProps({
  accept: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['selected', 'removed'])

const inputRef = ref(null)
const isDragover = ref(false)
const fileName = ref('')
const fileSize = ref(0)

function openFilePicker() {
  inputRef.value?.click()
}

function handleFiles(files) {
  const file = files && files[0]
  if (!file) return
  fileName.value = file.name
  fileSize.value = file.size
  emit('selected', { name: file.name, size: file.size, file })
}

function onInputChange(event) {
  handleFiles(event.target.files)
  // Allow re-selecting the same file afterwards.
  event.target.value = ''
}

function onDrop(event) {
  isDragover.value = false
  handleFiles(event.dataTransfer.files)
}

function clearFile() {
  fileName.value = ''
  fileSize.value = 0
  emit('removed')
}

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
</script>

<template>
  <div
    class="upload"
    :class="{ 'is-dragover': isDragover }"
    role="button"
    tabindex="0"
    :aria-label="fileName ? `Selected file: ${fileName}` : 'Upload resume file'"
    @click="openFilePicker"
    @keydown.enter="openFilePicker"
    @keydown.space.prevent="openFilePicker"
    @dragover.prevent="isDragover = true"
    @dragleave.prevent="isDragover = false"
    @drop.prevent="onDrop"
  >
    <input
      ref="inputRef"
      type="file"
      class="upload__input"
      :accept="accept"
      @change="onInputChange"
    />

    <template v-if="!fileName">
      <IconUpload class="upload__icon" />
      <p class="upload__hint">
        Drag your resume file to this area, or click on the area to select the
        appropriate file to upload
      </p>
    </template>

    <template v-else>
      <svg
        class="upload__file-icon"
        viewBox="0 0 24 24"
        fill="none"
        aria-hidden="true"
      >
        <path d="M7 3h7l4 4v14H7V3z" fill="#1849D6" opacity="0.15" />
        <path
          d="M14 3v4h4"
          stroke="#1849D6"
          stroke-width="1.6"
          stroke-linejoin="round"
        />
        <path
          d="M9 12h6M9 15h6"
          stroke="#1849D6"
          stroke-width="1.6"
          stroke-linecap="round"
        />
      </svg>
      <div class="upload__file-meta">
        <p class="upload__file-name" :title="fileName">{{ fileName }}</p>
        <p class="upload__file-size">{{ formatSize(fileSize) }}</p>
      </div>
      <button
        class="upload__remove"
        type="button"
        aria-label="Remove file"
        @click.stop="clearFile"
      >
        ×
      </button>
    </template>
  </div>
</template>

<style scoped>
.upload {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 28px;
  height: clamp(260px, 40vh, 420px);
  padding: 24px;
  background-color: var(--color-upload-bg);
  border: 1px dashed var(--color-upload-border);
  border-radius: var(--radius-upload);
  cursor: pointer;
  transition: border-color 0.2s ease, background-color 0.2s ease;
}

.upload:hover,
.upload.is-dragover {
  border-color: var(--color-primary);
  background-color: #e6f2ff;
}

.upload__input {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
  border: 0;
}

.upload__icon {
  flex-shrink: 0;
}

.upload__hint {
  max-width: 499px;
  font-size: 16px;
  line-height: 32px;
  text-align: center;
  color: var(--color-gray);
}

.upload__file-icon {
  width: 56px;
  height: 56px;
  flex-shrink: 0;
}

.upload__file-meta {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  min-width: 0;
}

.upload__file-name {
  max-width: 420px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 18px;
  font-weight: 500;
  color: var(--color-text-dark);
}

.upload__file-size {
  font-size: 14px;
  color: var(--color-gray);
}

.upload__remove {
  position: absolute;
  top: 16px;
  right: 20px;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 50%;
  background: rgba(5, 56, 187, 0.1);
  color: var(--color-upload-border);
  font-size: 22px;
  line-height: 1;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.upload__remove:hover {
  background: rgba(5, 56, 187, 0.2);
}

@media (max-width: 600px) {
  .upload {
    height: 300px;
  }
}
</style>
