<template>
  <section class="hero">
    <div class="hero-copy">
      <div class="eyebrow">Enterprise AI Assistant</div>
      <h1>企业知识，一问即答。</h1>
      <p>上传制度、手册和业务资料，使用 LangChain RAG 与国产大模型，构建企业自己的智能助手。</p>
      <div class="hero-actions">
        <button class="primary" type="button" @click="$emit('start')">开始配置</button>
        <button class="secondary" type="button" @click="$emit('sample')">试问制度</button>
      </div>
    </div>
    <div class="hero-visual">
      <img src="/assets/enterprise-ai-hero.png" alt="Enterprise AI visual" />
    </div>
  </section>
</template>
