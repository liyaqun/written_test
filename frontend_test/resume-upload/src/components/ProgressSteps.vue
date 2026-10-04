<script setup>
import { computed } from 'vue'

const props = defineProps({
  current: {
    type: Number,
    default: 1,
  },
  total: {
    type: Number,
    default: 3,
  },
})

const activeWidth = computed(() => {
  if (props.total <= 1) return '100%'
  return `${((props.current - 1) / (props.total - 1)) * 100}%`
})
</script>

<template>
  <div
    class="progress"
    role="progressbar"
    :aria-valuenow="current"
    :aria-valuemin="1"
    :aria-valuemax="total"
    aria-label="Upload progress"
  >
    <div class="progress__track"></div>
    <div class="progress__active" :style="{ width: activeWidth }"></div>

    <div class="progress__dots">
      <div v-for="step in total" :key="step" class="progress__dot">
        <span class="progress__dot-inner">
          <svg
            v-if="step < current"
            class="progress__check"
            viewBox="0 0 10 8"
            fill="none"
            aria-hidden="true"
          >
            <path
              d="M1 4.1 3.6 6.7 9 1.3"
              stroke="#fff"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
          <span v-else class="progress__num">{{ step }}</span>
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.progress {
  position: relative;
  width: 343px;
  max-width: 100%;
  height: 32px;
  margin: auto auto 0;
}

.progress__track {
  position: absolute;
  left: 0;
  right: 0;
  top: 14px;
  height: 4px;
  background: var(--color-progress-track);
  border-radius: var(--radius-bar);
}

.progress__active {
  position: absolute;
  left: 0;
  top: 14px;
  height: 4px;
  background: var(--color-primary-light);
  border-radius: var(--radius-bar);
}

.progress__dots {
  position: relative;
  z-index: 1;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.progress__dot {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--color-primary-deep);
  box-shadow: var(--shadow-step);
  display: flex;
  align-items: center;
  justify-content: center;
}

.progress__dot-inner {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: var(--color-primary-light);
  display: flex;
  align-items: center;
  justify-content: center;
}

.progress__check {
  width: 10px;
  height: 8px;
}

.progress__num {
  color: var(--color-white);
  font-size: 11px;
  font-weight: 500;
  line-height: 13px;
}
</style>
