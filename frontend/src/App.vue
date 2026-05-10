<template>
  <TopNav />
  <HeroSection @start="scrollToWorkspace" @sample="useSample" />

  <main ref="workspace" class="workspace">
    <div class="workspace-inner">
      <section class="section-title">
        <h2>AI 工作台</h2>
        <p>把模型配置、知识库入库和问答演示放在同一个界面里，适合本地演示，也能直接部署到企业服务器。</p>
      </section>

      <KnowledgeStatus :status="status" />

      <section class="main-grid">
        <ChatPanel
          v-model:draft="draft"
          v-model:session-id="sessionId"
          :busy="busy.chat"
          :messages="messages"
          @send="sendMessage"
          @clear="clearChat"
        />

        <aside class="side-stack">
          <ModelSettings
            :busy="busy.settings"
            :providers="providers"
            :api-key-hint="apiKeyHint"
            :settings-hint="settingsHint"
            v-model="modelForm"
            @save="saveSettings"
          />

          <KnowledgeTools
            v-model:admin-token="adminToken"
            :busy-upload="busy.upload"
            :busy-ingest="busy.ingest"
            @token-save="saveToken"
            @file-change="onFileChange"
            @upload="uploadFile"
            @ingest="ingest"
          />

          <PipelineCard :steps="pipeline" />
        </aside>
      </section>
    </div>
  </main>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref } from "vue";
import { authHeaders, getJson, postJson } from "./api";
import TopNav from "./components/TopNav.vue";
import HeroSection from "./components/HeroSection.vue";
import KnowledgeStatus from "./components/KnowledgeStatus.vue";
import ChatPanel from "./components/ChatPanel.vue";
import ModelSettings from "./components/ModelSettings.vue";
import KnowledgeTools from "./components/KnowledgeTools.vue";
import PipelineCard from "./components/PipelineCard.vue";

const workspace = ref(null);
const sessionId = ref("user_001");
const draft = ref("");
const selectedFile = ref(null);
const adminToken = ref(localStorage.getItem("enterprise_admin_token") || "");
const status = ref({ raw_documents: 0, vector_chunks: 0 });
const providers = ref([]);
const apiKeyHint = ref("正在读取配置...");
const settingsHint = ref("");
const modelForm = ref({
  model_provider: "deepseek",
  api_key: "",
  base_url: "",
  chat_model: "",
  embedding_provider: "auto",
  embedding_api_key: "",
  embedding_model: "",
});
const busy = reactive({ chat: false, upload: false, ingest: false, settings: false });
const messages = ref([
  {
    id: 1,
    role: "assistant",
    content: "你好，我会优先查企业知识库，并在回答里带上来源。右侧可以选择模型提供商并保存 API Key。",
    meta: "系统就绪",
  },
]);
const pipeline = [
  "Document Loader 读取资料",
  "Text Splitter 切分文档",
  "Embedding 生成向量",
  "Vector Store 相似检索",
  "LLM 组织答案并引用来源",
];

const token = computed(() => adminToken.value.trim());

function pushMessage(role, content, meta = "") {
  messages.value.push({ id: Date.now() + Math.random(), role, content, meta });
  nextTick(() => {
    const node = document.querySelector(".messages");
    if (node) node.scrollTop = node.scrollHeight;
  });
}

async function refreshAll() {
  await Promise.all([loadSettings(), refreshStatus()]);
}

async function loadSettings() {
  try {
    const data = await getJson("/settings", token.value);
    providers.value = data.providers || [];
    modelForm.value = {
      ...modelForm.value,
      model_provider: data.model_provider || "deepseek",
      base_url: data.base_url || "",
      chat_model: data.chat_model || "",
      embedding_provider: data.embedding_provider || "auto",
      embedding_model: data.embedding_model || "",
      api_key: "",
      embedding_api_key: "",
    };
    apiKeyHint.value = data.has_api_key ? `已保存：${data.api_key_masked}` : "尚未保存 API Key";
    settingsHint.value = `当前生效：${data.model_provider} / ${data.resolved_chat_model}`;
  } catch (error) {
    settingsHint.value = error.message;
  }
}

async function refreshStatus() {
  try {
    status.value = await getJson("/knowledge/status", token.value);
  } catch (error) {
    status.value = { raw_documents: 0, vector_chunks: 0, model_provider: "离线", chat_model: error.message };
  }
}

async function saveSettings() {
  busy.settings = true;
  const payload = {
    model_provider: modelForm.value.model_provider,
    base_url: modelForm.value.base_url.trim(),
    chat_model: modelForm.value.chat_model.trim(),
    embedding_provider: modelForm.value.embedding_provider,
    embedding_model: modelForm.value.embedding_model.trim(),
  };
  if (modelForm.value.api_key.trim()) payload.api_key = modelForm.value.api_key.trim();
  if (modelForm.value.embedding_api_key.trim()) payload.embedding_api_key = modelForm.value.embedding_api_key.trim();
  try {
    const data = await postJson("/settings", payload, token.value);
    modelForm.value.api_key = "";
    modelForm.value.embedding_api_key = "";
    apiKeyHint.value = data.has_api_key ? `已保存：${data.api_key_masked}` : "尚未保存 API Key";
    settingsHint.value = `已保存并生效：${data.model_provider} / ${data.resolved_chat_model}`;
    await refreshStatus();
  } catch (error) {
    settingsHint.value = error.message;
  } finally {
    busy.settings = false;
  }
}

function saveToken() {
  localStorage.setItem("enterprise_admin_token", token.value);
  pushMessage("assistant", "访问令牌已保存到当前浏览器。", "安全设置");
  refreshAll();
}

function onFileChange(file) {
  selectedFile.value = file;
}

async function uploadFile() {
  if (!selectedFile.value) {
    pushMessage("assistant", "请先选择一个 txt、md、pdf 或 docx 文件。");
    return;
  }
  busy.upload = true;
  const body = new FormData();
  body.append("file", selectedFile.value);
  try {
    const response = await fetch("/upload", { method: "POST", body, headers: authHeaders(token.value) });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "上传失败");
    pushMessage("assistant", `已上传：${data.filename}`, "资料上传");
    await refreshStatus();
  } catch (error) {
    pushMessage("assistant", error.message);
  } finally {
    busy.upload = false;
  }
}

async function ingest() {
  busy.ingest = true;
  try {
    const data = await postJson("/ingest", { path: "./data/raw", reset: true }, token.value);
    pushMessage("assistant", `入库完成：${data.documents} 个文档，${data.chunks} 个片段。${data.message}`, "向量库");
    await refreshStatus();
  } catch (error) {
    pushMessage("assistant", error.message);
  } finally {
    busy.ingest = false;
  }
}

async function sendMessage() {
  const text = draft.value.trim();
  if (!text) return;
  pushMessage("user", text);
  draft.value = "";
  busy.chat = true;
  try {
    const data = await postJson("/chat", { session_id: sessionId.value, message: text }, token.value);
    const meta = [
      data.tool_used ? `工具：${data.tool_used}` : "",
      data.sources?.length ? `来源：${data.sources.join("、")}` : "",
    ].filter(Boolean).join(" · ");
    pushMessage("assistant", data.answer, meta);
  } catch (error) {
    pushMessage("assistant", error.message);
  } finally {
    busy.chat = false;
  }
}

function clearChat() {
  messages.value = [];
  pushMessage("assistant", "对话已清空，可以继续提问。", "系统");
}

function useSample() {
  draft.value = "年假制度怎么规定？";
  scrollToWorkspace();
}

function scrollToWorkspace() {
  workspace.value?.scrollIntoView({ behavior: "smooth", block: "start" });
}

onMounted(refreshAll);
</script>
