<script setup>
defineProps({
  variant: {
    type: String,
    default: 'primary',
    validator: (v) => ['primary', 'secondary'].includes(v),
  },
  type: {
    type: String,
    default: 'button',
  },
})
</script>

<template>
  <button class="btn" :class="`btn--${variant}`" :type="type">
    <slot />
  </button>
</template>

<style scoped>
.btn {
  min-width: 272px;
  height: 67px;
  border: none;
  border-radius: var(--radius-btn);
  font-family: inherit;
  font-size: 24px;
  line-height: 35px;
  letter-spacing: 0.08em;
  color: var(--color-white);
  cursor: pointer;
  transition: background-color 0.2s ease, transform 0.1s ease;
}

.btn--primary {
  background-color: var(--color-primary);
}

.btn--primary:hover {
  background-color: #1547d9;
}

.btn--primary:active {
  background-color: #103cb8;
  transform: translateY(1px);
}

.btn--secondary {
  background-color: var(--color-secondary);
}

.btn--secondary:hover {
  background-color: #5f97e6;
}

.btn--secondary:active {
  background-color: #4d82d1;
  transform: translateY(1px);
}

.btn:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

@media (max-width: 600px) {
  .btn {
    min-width: 0;
    width: 100%;
    height: 56px;
    font-size: 20px;
  }
}
</style>
