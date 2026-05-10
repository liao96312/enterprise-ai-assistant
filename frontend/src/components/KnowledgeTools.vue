<template>
  <div class="panel">
    <div class="panel-head"><strong>资料与权限</strong></div>
    <div class="card-body">
      <input class="file-input" type="file" accept=".txt,.md,.pdf,.docx" @change="$emit('fileChange', $event.target.files[0] || null)" />
      <div class="grid-2">
        <button class="secondary" type="button" :disabled="busyUpload" @click="$emit('upload')">上传资料</button>
        <button class="primary" type="button" :disabled="busyIngest" @click="$emit('ingest')">重建向量库</button>
      </div>
      <div class="field">
        <label>访问令牌</label>
        <input class="text-input" type="password" :value="adminToken" @input="$emit('update:adminToken', $event.target.value)" placeholder="启用鉴权时填写 Admin Token" />
        <button class="plain" type="button" @click="$emit('tokenSave')">保存到本机浏览器</button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  adminToken: { type: String, default: "" },
  busyUpload: { type: Boolean, default: false },
  busyIngest: { type: Boolean, default: false },
});

defineEmits(["update:adminToken", "fileChange", "upload", "ingest", "tokenSave"]);
</script>
