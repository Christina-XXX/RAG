<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 64 64"
    xmlns="http://www.w3.org/2000/svg"
  >
    <!-- 齐肩长发（后面） -->
    <path
      d="M11,33 C11,14 21,5 32,5 C43,5 53,14 53,33 L53,49 C53,57 43,58 35,55 C33,54 31,52 31,52 C31,52 29,54 27,55 C19,58 11,57 11,49 Z"
      :fill="hair"
    />
    <!-- 脸 -->
    <ellipse cx="32" cy="35" rx="13.5" ry="14.5" :fill="skin" />
    <!-- 齐刘海 -->
    <path
      d="M17,27 L17,22 C17,16 24,14.5 32,14.5 C40,14.5 47,16 47,22 L47,27 Z"
      :fill="hair"
    />
    <!-- 眼睛 -->
    <circle cx="27" cy="38" r="2.1" fill="#3a3a3a" />
    <circle cx="37" cy="38" r="2.1" fill="#3a3a3a" />
    <circle cx="27.7" cy="37.3" r="0.6" fill="#ffffff" />
    <circle cx="37.7" cy="37.3" r="0.6" fill="#ffffff" />
    <!-- 腮红 -->
    <circle cx="23.5" cy="43" r="2.4" fill="#ffb3b3" opacity="0.6" />
    <circle cx="40.5" cy="43" r="2.4" fill="#ffb3b3" opacity="0.6" />
    <!-- 嘴 -->
    <path
      d="M29.5,44.5 Q32,47 34.5,44.5"
      stroke="#3a3a3a"
      stroke-width="1.4"
      fill="none"
      stroke-linecap="round"
    />
    <!-- 红色蝴蝶结 -->
    <g v-if="bow">
      <path
        d="M32,7 L22,1.5 L22,12.5 Z"
        fill="#e74c3c"
        stroke="#c0392b"
        stroke-width="0.7"
        stroke-linejoin="round"
      />
      <path
        d="M32,7 L42,1.5 L42,12.5 Z"
        fill="#e74c3c"
        stroke="#c0392b"
        stroke-width="0.7"
        stroke-linejoin="round"
      />
      <circle cx="32" cy="7" r="3.2" fill="#e74c3c" stroke="#c0392b" stroke-width="0.7" />
    </g>
  </svg>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    hair?: string
    skin?: string
    bow?: boolean
    size?: number
  }>(),
  {
    hair: '#262626',
    skin: '#ffe3d1',
    bow: false,
    size: 40,
  }
)
</script>
