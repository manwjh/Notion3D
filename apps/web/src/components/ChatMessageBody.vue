<script setup lang="ts">
import { computed } from "vue";
import type { ChatMessage } from "../api/client";
import { renderChatMarkdown } from "../utils/renderMarkdown";

const props = defineProps<{
  content: string;
  role: ChatMessage["role"];
}>();

const html = computed(() =>
  props.role === "assistant" ? renderChatMarkdown(props.content) : "",
);
</script>

<template>
  <div v-if="role === 'assistant'" class="chat-md" v-html="html" />
  <p v-else class="chat-plain">{{ content }}</p>
</template>
