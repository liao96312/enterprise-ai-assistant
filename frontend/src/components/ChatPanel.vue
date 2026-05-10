<template>
  <div class="panel chat-panel">
    <div class="panel-head">
      <strong>对话</strong>
      <span class="mode">knowledge_search / policy_explain / calculator / current_time</span>
    </div>
    <div class="messages">
      <div class="message" :class="message.role" v-for="message in messages" :key="message.id">
        <div class="bubble">{{ message.content }}</div>
        <div class="meta" v-if="message.meta">{{ message.meta }}</div>
      </div>
    </div>
    <form class="composer" @submit.prevent="$emit('send')">
      <input class="text-input" :value="sessionId" @input="$emit('update:sessionId', $event.target.value)" aria-label="Session ID" />
      <input class="text-input" :value="draft" @input="$emit('update:draft', $event.target.value)" placeholder="输入问题，例如：年假制度怎么规定？" />
      <div class="grid-2">
        <button class="plain" type="button" @click="$emit('clear')">清屏</button>
        <button class="primary" type="submit" :disabled="busy">发送</button>
      </div>
    </form>
  </div>
</template>

<script setup>
defineProps({
  messages: { type: Array, required: true },
  draft: { type: String, required: true },
  sessionId: { type: String, required: true },
  busy: { type: Boolean, default: false },
});

defineEmits(["send", "clear", "update:draft", "update:sessionId"]);
</script>
