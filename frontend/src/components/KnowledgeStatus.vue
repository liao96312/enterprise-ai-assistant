<template>
  <section class="status-strip">
    <div class="stat">
      <span>原始文档</span>
      <strong>{{ status.raw_documents || 0 }}</strong>
    </div>
    <div class="stat">
      <span>向量片段</span>
      <strong>{{ status.vector_chunks || 0 }}</strong>
    </div>
    <div class="stat wide">
      <span>当前模型</span>
      <strong>{{ status.model_provider || '-' }} / {{ status.chat_model || '-' }}<br />{{ status.vector_store || '-' }} · {{ status.embedding_provider || '-' }}</strong>
    </div>
  </section>
</template>

<script setup>
defineProps({
  status: { type: Object, required: true },
});
</script>
