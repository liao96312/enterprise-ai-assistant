<template>
  <div class="panel">
    <div class="panel-head"><strong>LangChain Pipeline</strong></div>
    <div class="card-body pipeline">
      <div class="step" v-for="(step, index) in steps" :key="step">
        <span class="dot">{{ index + 1 }}</span>
        <span>{{ step }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  steps: { type: Array, required: true },
});
</script>
