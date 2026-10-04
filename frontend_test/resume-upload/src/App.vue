<script setup>
import UploadArea from './components/UploadArea.vue'
import BaseButton from './components/BaseButton.vue'
import ProgressSteps from './components/ProgressSteps.vue'
import illustrationUrl from './assets/illustration-7bffb9.png'
</script>

<template>
  <main class="page">
    <section class="left">
      <header class="hero">
        <h1 class="hero__title">finish!<br />Upload your resume</h1>
        <p class="hero__subtitle">
          Upload your resume, the platform will help you parse and optimize, you
          can also skip this step
        </p>
      </header>
      <img class="hero__illustration" :src="illustrationUrl" alt="" />
    </section>

    <section class="card" aria-label="Upload resume form">
      <h2 class="card__title">Upload file</h2>

      <UploadArea accept=".pdf,.doc,.docx" />

      <div class="card__actions">
        <BaseButton variant="secondary">Last step</BaseButton>
        <BaseButton variant="primary">finish</BaseButton>
      </div>

      <ProgressSteps :current="3" :total="3" />
    </section>
  </main>
</template>

<style scoped>
.page {
  height: 100vh;
  max-width: 1920px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: clamp(24px, 4vw, 56px);
  padding: 32px clamp(24px, 5vw, 102px);
  overflow: hidden;
}

.left {
  flex: 7 7 0; /* 左栏 : 右栏 = 7 : 9，按比例缩放，不写死 px */
  min-width: 0;
  align-self: stretch;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 24px 0;
}

.hero__title {
  font-size: 40px;
  font-weight: 400;
  line-height: 55px;
  color: var(--color-black);
}

.hero__subtitle {
  margin-top: 20px;
  max-width: 696px;
  font-size: 20px;
  line-height: 35px;
  color: var(--color-gray);
}

.hero__illustration {
  width: auto;
  max-width: 100%; /* 填满左栏，永不溢出、不被裁剪 */
  max-height: 56vh;
  height: auto;
  align-self: flex-start;
}

.card {
  flex: 9 9 0; /* 左栏 : 右栏 = 7 : 9 */
  min-width: 760px; /* 保证按钮/上传框不被挤爆 */
  max-width: 943px;
  height: min(922px, calc(100vh - 64px));
  background: var(--color-white);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-card);
  padding: 32px clamp(40px, 6vw, 129px) 32px;
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.card__title {
  font-size: 36px;
  font-weight: 500;
  line-height: 35px;
  letter-spacing: 0.08em;
  color: var(--color-text-dark);
}

.card__actions {
  display: flex;
  justify-content: center;
  gap: 29px;
}

/* 中等宽度：收窄留白，插画随比例缩小（不再隐藏） */
@media (max-width: 1500px) and (min-width: 1101px) {
  .page {
    gap: 40px;
    padding: 32px 48px;
  }
}

/* 小屏幕 / 移动端：左右结构切换为上下结构 */
@media (max-width: 1100px) {
  .page {
    height: auto;
    min-height: 100vh;
    overflow: visible;
    flex-direction: column;
    align-items: center;
    gap: 40px;
    padding: 40px 24px;
  }

  .left {
    flex: none;
    width: 100%;
    max-width: 720px;
    align-items: center;
    text-align: center;
    padding: 0;
  }

  .hero__subtitle {
    margin-left: auto;
    margin-right: auto;
  }

  .hero__illustration {
    align-self: center;
    width: auto;
    max-width: 100%;
    max-height: 40vh;
    height: auto;
  }

  .card {
    flex: none;
    width: 100%;
    min-width: 0;
    max-width: 720px;
    height: auto;
    padding: 32px 24px 40px;
  }
}

@media (max-width: 600px) {
  .card__actions {
    flex-direction: column;
    gap: 12px;
  }
}
</style>
