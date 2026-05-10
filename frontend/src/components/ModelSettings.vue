<template>
  <div class="panel">
    <div class="panel-head"><strong>模型配置</strong></div>
    <div class="card-body">
      <div class="field">
        <label>模型提供商</label>
        <select class="select-input" v-model="localValue.model_provider">
          <option v-for="provider in providers" :key="provider.name" :value="provider.name">{{ provider.name }}</option>
        </select>
      </div>
      <div class="field">
        <label>API Key</label>
        <input class="text-input" type="password" v-model="localValue.api_key" placeholder="留空则不覆盖已保存 Key" />
        <div class="hint">{{ apiKeyHint }}</div>
      </div>
      <div class="grid-2">
        <div class="field">
          <label>Base URL</label>
          <input class="text-input" v-model="localValue.base_url" :placeholder="activePreset.base_url || '自定义服务商需要填写'" />
        </div>
        <div class="field">
          <label>聊天模型</label>
          <input class="text-input" v-model="localValue.chat_model" :placeholder="activePreset.chat_model || '请输入模型名'" />
        </div>
      </div>
      <div class="grid-2">
        <div class="field">
          <label>Embedding</label>
          <select class="select-input" v-model="localValue.embedding_provider">
            <option value="auto">auto</option>
            <option value="api">api</option>
            <option value="local">local</option>
          </select>
        </div>
        <div class="field">
          <label>Embedding 模型</label>
          <input class="text-input" v-model="localValue.embedding_model" :placeholder="activePreset.embedding_model || '可留空使用本地 Embedding'" />
        </div>
      </div>
      <button class="primary" type="button" :disabled="busy" @click="$emit('save')">保存模型配置</button>
      <div class="hint">{{ settingsHint }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  modelValue: { type: Object, required: true },
  providers: { type: Array, required: true },
  apiKeyHint: { type: String, default: "" },
  settingsHint: { type: String, default: "" },
  busy: { type: Boolean, default: false },
});
const emit = defineEmits(["update:modelValue", "save"]);

const localValue = computed({
  get: () => props.modelValue,
  set: (value) => emit("update:modelValue", value),
});

const activePreset = computed(() => {
  return props.providers.find((item) => item.name === props.modelValue.model_provider) || {};
});
</script>
