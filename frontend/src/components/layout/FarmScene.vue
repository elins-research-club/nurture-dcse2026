<script setup lang="ts">
import { computed } from 'vue'
import { useDark } from '@vueuse/core'

const isDark = useDark({ storageKey: 'theme', valueDark: 'dark', valueLight: 'light' })

/* Deterministic swaying grass - two depth layers */
function makeBlades(count: number, seed: number, minH: number, maxH: number) {
  const out = []
  for (let i = 0; i < count; i++) {
    const x = ((i * 1450) / count + (i * seed) % 11) % 1460
    const h = minH + ((i * (37 + seed)) % (maxH - minH))
    const lean = (((i * (53 + seed)) % 30) - 15)
    const dur = 3.4 + (((i * 17) % 26) / 10)
    const delay = -(((i * 29) % 45) / 10)
    const w = 2.2 + (((i * 13) % 16) / 10)
    out.push({ i, x, h, lean, dur, delay, w })
  }
  return out
}

const backBlades = computed(() => makeBlades(78, 3, 34, 64))
const frontBlades = computed(() => makeBlades(58, 7, 58, 104))

const particles = computed(() =>
  [
    { l: 6, b: 22, s: 3.5, d: 0, dur: 13, x: 26, y: -54 },
    { l: 14, b: 34, s: 2.5, d: 2.6, dur: 17, x: -20, y: -42 },
    { l: 21, b: 18, s: 4, d: 1.1, dur: 15, x: 34, y: -68 },
    { l: 28, b: 28, s: 2.8, d: 4.2, dur: 19, x: -28, y: -36 },
    { l: 35, b: 40, s: 3.2, d: 0.7, dur: 14, x: 22, y: -60 },
    { l: 42, b: 20, s: 2.4, d: 5.3, dur: 21, x: -16, y: -48 },
    { l: 49, b: 31, s: 4.2, d: 2.1, dur: 16, x: 30, y: -72 },
    { l: 56, b: 24, s: 2.6, d: 6.4, dur: 18, x: -24, y: -40 },
    { l: 63, b: 36, s: 3.4, d: 1.8, dur: 15, x: 18, y: -56 },
    { l: 70, b: 19, s: 2.9, d: 3.7, dur: 20, x: -30, y: -64 },
    { l: 77, b: 29, s: 3.8, d: 0.4, dur: 17, x: 24, y: -44 },
    { l: 84, b: 23, s: 2.5, d: 4.9, dur: 22, x: -18, y: -58 },
    { l: 91, b: 35, s: 3.6, d: 2.9, dur: 14, x: 28, y: -50 },
    { l: 96, b: 26, s: 2.7, d: 6.1, dur: 19, x: -22, y: -66 },
    { l: 10, b: 45, s: 3, d: 7.2, dur: 23, x: 32, y: -38 },
    { l: 46, b: 48, s: 2.6, d: 5.8, dur: 20, x: -26, y: -52 },
    { l: 68, b: 46, s: 3.3, d: 3.1, dur: 18, x: 20, y: -62 },
    { l: 88, b: 42, s: 2.8, d: 1.4, dur: 24, x: -32, y: -46 },
  ].map((p, i) => ({ ...p, key: i }))
)

const stars = computed(() =>
  [
    { l: 8, t: 12, s: 1.6, d: 0 }, { l: 17, t: 26, s: 1.2, d: 1.4 },
    { l: 24, t: 8, s: 2, d: 2.7 }, { l: 33, t: 19, s: 1.4, d: 0.8 },
    { l: 41, t: 6, s: 1.8, d: 3.3 }, { l: 52, t: 22, s: 1.2, d: 1.9 },
    { l: 59, t: 11, s: 1.7, d: 2.2 }, { l: 67, t: 27, s: 1.3, d: 0.5 },
    { l: 74, t: 9, s: 2.1, d: 3.8 }, { l: 82, t: 18, s: 1.5, d: 1.1 },
    { l: 90, t: 7, s: 1.8, d: 2.5 }, { l: 95, t: 24, s: 1.3, d: 4.1 },
    { l: 13, t: 33, s: 1.4, d: 3.0 }, { l: 47, t: 31, s: 1.1, d: 1.7 },
    { l: 78, t: 35, s: 1.5, d: 2.9 },
  ].map((p, i) => ({ ...p, key: i }))
)
</script>

<template>
  <div class="farm-scene absolute inset-0 overflow-hidden pointer-events-none select-none" aria-hidden="true">

    <div class="absolute inset-0 sky"></div>

    <template v-if="isDark">
      <span
        v-for="s in stars"
        :key="'star-' + s.key"
        class="star"
        :style="{ left: s.l + '%', top: s.t + '%', width: s.s + 'px', height: s.s + 'px', animationDelay: s.d + 's' }"
      ></span>
    </template>

    <template v-else>
      <svg class="cloud cloud-1" viewBox="0 0 120 50" fill="currentColor">
        <ellipse cx="35" cy="32" rx="30" ry="16" /><ellipse cx="60" cy="24" rx="26" ry="19" /><ellipse cx="86" cy="33" rx="24" ry="14" />
      </svg>
      <svg class="cloud cloud-2" viewBox="0 0 120 50" fill="currentColor">
        <ellipse cx="34" cy="30" rx="26" ry="14" /><ellipse cx="62" cy="23" rx="24" ry="17" /><ellipse cx="88" cy="31" rx="21" ry="13" />
      </svg>
      <svg class="cloud cloud-3" viewBox="0 0 120 50" fill="currentColor">
        <ellipse cx="38" cy="31" rx="22" ry="13" /><ellipse cx="62" cy="25" rx="21" ry="15" /><ellipse cx="84" cy="32" rx="18" ry="11" />
      </svg>
    </template>

    <div class="celestial"></div>

    <svg class="hills" viewBox="0 0 1440 420" preserveAspectRatio="none">
      <path class="hill hill-3" d="M0 250 C 180 200 320 268 520 240 C 720 212 900 272 1120 236 C 1280 210 1380 244 1440 232 L1440 420 L0 420 Z" />
      <path class="hill hill-2" d="M0 300 C 200 258 380 322 600 292 C 820 262 980 320 1200 288 C 1320 270 1400 296 1440 288 L1440 420 L0 420 Z" />
      <path class="hill hill-1" d="M0 350 C 240 316 420 372 660 344 C 900 316 1080 366 1300 340 C 1380 331 1420 344 1440 340 L1440 420 L0 420 Z" />
    </svg>

    <!-- ═══ SWAYING GRASS — back layer ═══ -->
    <svg class="grass grass-back" viewBox="0 0 1440 120" preserveAspectRatio="none">
      <path
        v-for="b in backBlades"
        :key="'gb' + b.i"
        class="blade"
        :d="`M${b.x} 120 Q${b.x + b.lean * 0.35} ${120 - b.h * 0.55} ${b.x + b.lean} ${120 - b.h}`"
        :stroke-width="b.w"
        :style="{ animationDuration: b.dur + 's', animationDelay: b.delay + 's' }"
      />
    </svg>

    <!-- ═══ SWAYING GRASS — front layer ═══ -->
    <svg class="grass grass-front" viewBox="0 0 1440 120" preserveAspectRatio="none">
      <path
        v-for="b in frontBlades"
        :key="'gf' + b.i"
        class="blade"
        :d="`M${b.x} 120 Q${b.x + b.lean * 0.4} ${120 - b.h * 0.55} ${b.x + b.lean} ${120 - b.h}`"
        :stroke-width="b.w"
        :style="{ animationDuration: b.dur + 's', animationDelay: b.delay + 's' }"
      />
    </svg>

    <span
      v-for="p in particles"
      :key="'p-' + p.key"
      class="mote"
      :style="{
        left: p.l + '%', bottom: p.b + '%', width: p.s + 'px', height: p.s + 'px',
        animationDelay: p.d + 's', animationDuration: p.dur + 's',
        '--dx': p.x + 'px', '--dy': p.y + 'px'
      }"
    ></span>
  </div>
</template>

<style scoped>
/* ── Sky ─────────────────────────────────────────────── */
.sky { background: linear-gradient(to bottom, #cfe8f7 0%, #e8f2ea 55%, #f2f4e9 100%); }
:global(.dark) .sky { background: linear-gradient(to bottom, #060b16 0%, #0b1524 48%, #0d1a18 100%); }

/* ── Celestial ───────────────────────────────────────── */
.celestial {
  position: absolute; top: 9%; right: 13%;
  width: 74px; height: 74px; border-radius: 9999px;
  background: #ffd66b; box-shadow: 0 0 48px 18px rgba(255, 214, 107, 0.42);
}
:global(.dark) .celestial { background: #e8eef7; box-shadow: 0 0 42px 12px rgba(232, 238, 247, 0.22); }

/* ── Stars ───────────────────────────────────────────── */
.star { position: absolute; border-radius: 9999px; background: #e9eef8; opacity: 0.5; animation: twinkle 4.5s ease-in-out infinite; }
@keyframes twinkle { 0%, 100% { opacity: 0.22; } 50% { opacity: 0.85; } }

/* ── Clouds ──────────────────────────────────────────── */
.cloud { position: absolute; color: rgba(255, 255, 255, 0.9); will-change: transform; }
.cloud-1 { top: 12%; width: 190px; animation: drift 66s linear infinite; }
.cloud-2 { top: 24%; width: 140px; opacity: 0.8; animation: drift 88s linear infinite -22s; }
.cloud-3 { top: 6%;  width: 110px; opacity: 0.7; animation: drift 74s linear infinite -48s; }
@keyframes drift { from { transform: translateX(-24vw); } to { transform: translateX(112vw); } }

/* ── Hills ───────────────────────────────────────────── */
.hills { position: absolute; bottom: 0; left: 0; width: 100%; height: 46%; }
.hill-3 { fill: #b9d6b0; }
.hill-2 { fill: #93c08b; }
.hill-1 { fill: #6ea86b; }
:global(.dark) .hill-3 { fill: #0f2019; }
:global(.dark) .hill-2 { fill: #0b1912; }
:global(.dark) .hill-1 { fill: #07110c; }

/* ── Grass ───────────────────────────────────────────── */
.grass {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  overflow: visible;
}
.grass-back  { height: 13%; }
.grass-front { height: 18%; }

.blade {
  fill: none;
  stroke-linecap: round;
  transform-box: fill-box;
  transform-origin: 50% 100%;
  will-change: transform;
  animation-name: sway;
  animation-timing-function: ease-in-out;
  animation-iteration-count: infinite;
  animation-direction: alternate;
}
.grass-back .blade  { stroke: #5d9a55; }
.grass-front .blade { stroke: #3d7a3a; }
:global(.dark) .grass-back .blade  { stroke: #16321f; }
:global(.dark) .grass-front .blade { stroke: #0f2416; }

@keyframes sway {
  from { transform: rotate(-4.5deg) skewX(-2deg); }
  to   { transform: rotate(4.5deg) skewX(2deg); }
}

/* ── Fireflies / pollen ──────────────────────────────── */
.mote {
  position: absolute; border-radius: 9999px;
  background: #fff3a8; box-shadow: 0 0 7px 2px rgba(255, 232, 120, 0.75);
  opacity: 0; will-change: transform, opacity;
  animation-name: float-glow; animation-timing-function: ease-in-out; animation-iteration-count: infinite;
}
:global(.dark) .mote { background: #d9ff87; box-shadow: 0 0 10px 3px rgba(190, 255, 120, 0.85); }
:global(html:not(.dark)) .mote { background: #ffffff; box-shadow: 0 0 6px 2px rgba(255, 255, 255, 0.8); }

@keyframes float-glow {
  0%   { transform: translate(0, 0) scale(0.6); opacity: 0; }
  12%  { opacity: 0.95; }
  50%  { transform: translate(var(--dx), var(--dy)) scale(1); opacity: 0.65; }
  78%  { opacity: 0.9; }
  100% { transform: translate(calc(var(--dx) * 1.7), calc(var(--dy) * 1.8)) scale(0.55); opacity: 0; }
}

@media (prefers-reduced-motion: reduce) {
  .mote, .star, .cloud, .blade { animation: none; }
  .mote { opacity: 0.6; }
}
</style>
