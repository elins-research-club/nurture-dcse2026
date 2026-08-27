<script setup lang="ts">
const logos = [
  { src: '/Logo-UGM.png', alt: 'Universitas Gadjah Mada', class: 'h-[45px] max-w-[53px]' },
  { src: '/Logo-DIKE.png', alt: 'Departemen Ilmu Komputer dan Elektronika UGM', class: 'h-9 max-w-[75px]' },
  { src: '/logo-icon.webp', alt: 'Laboratorium ELINS', class: 'h-9 max-w-[40px]' },
  { src: '/logo-webdev.webp', alt: 'Webdev ERC', class: 'h-9 max-w-[40px] dark:invert' },
]
</script>

<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-[99999] w-screen h-screen flex flex-col items-center justify-center bg-background select-none transition-colors duration-300">
      <div class="flex flex-col items-center gap-5 sm:gap-6">
        <!-- Top Title: COMMUNITY SERVICE PROGRAM -->
        <p class="text-xs sm:text-[13px] font-bold uppercase tracking-[0.2em] text-muted-foreground/80">
          Community Service Program
        </p>

        <!-- Row of Wavy Animated Logos -->
        <div class="flex items-center justify-center gap-6 sm:gap-8 my-1">
          <div
            v-for="(logo, index) in logos"
            :key="logo.src"
            class="logo-wavy flex items-center justify-center"
            :style="{ animationDelay: `${index * 0.18}s` }"
          >
            <img
              :src="logo.src"
              :alt="logo.alt"
              :class="[logo.class, 'object-contain pointer-events-none drop-shadow-sm']"
            />
          </div>
        </div>

        <!-- Sentence with sequential looping three dots -->
        <div class="flex items-center text-xs sm:text-sm font-medium text-muted-foreground tracking-wide">
          <span>Mohon tunggu</span>
          <span class="inline-flex items-center ml-1 gap-0.5">
            <span class="dot dot-1 font-bold text-foreground">.</span>
            <span class="dot dot-2 font-bold text-foreground">.</span>
            <span class="dot dot-3 font-bold text-foreground">.</span>
          </span>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
/* Wavy bounce animation for logos */
.logo-wavy {
  animation: logoWave 1.4s ease-in-out infinite;
}

@keyframes logoWave {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-8px);
  }
}

/* Sequential three dots fading in one by one and looping */
.dot {
  opacity: 0;
  animation: dotBlink 1.4s infinite;
}

.dot-1 {
  animation-delay: 0s;
}

.dot-2 {
  animation-delay: 0.25s;
}

.dot-3 {
  animation-delay: 0.5s;
}

@keyframes dotBlink {
  0% {
    opacity: 0;
    transform: translateY(0);
  }
  30% {
    opacity: 1;
    transform: translateY(-1px);
  }
  70% {
    opacity: 1;
    transform: translateY(0);
  }
  100% {
    opacity: 0;
  }
}
</style>
