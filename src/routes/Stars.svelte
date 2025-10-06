<script lang="ts">
  import { onMount } from 'svelte';

  interface Star {
    size: number;
    top: number;
    left: number;
    duration: number;
    delay: number;
  }

  let stars: Star[] = [];

  onMount(() => {
    const numStars = 200;
    for (let i = 0; i < numStars; i++) {
      stars = [
        ...stars,
        {
          size: Math.random() * 2 + 1,
          top: Math.random() * 100,
          left: Math.random() * 100,
          duration: Math.random() * 3 + 2,
          delay: Math.random() * 3,
        }
      ];
    }
  });
</script>

<div class="stars-container">
  {#each stars as star}
    <div
      class="star"
      style="
        width: {star.size}px;
        height: {star.size}px;
        top: {star.top}%;
        left: {star.left}%;
        animation-duration: {star.duration}s;
        animation-delay: {star.delay}s;
      "
    ></div>
  {/each}
</div>

<style>
  .stars-container {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: -1;
    background: #0a0a0a;
    overflow: hidden;
  }
  .star {
    position: absolute;
    background: white;
    border-radius: 50%;
    animation: twinkle linear infinite;
  }
  @keyframes twinkle {
    0%, 100% { opacity: 0; }
    50% { opacity: 1; }
  }
</style>

