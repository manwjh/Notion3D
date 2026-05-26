<script setup lang="ts">
import { computed } from "vue";
import type { ChatImage, ChatMessage } from "../api/client";
import { renderChatMarkdown } from "../utils/renderMarkdown";

const props = defineProps<{
  content: string;
  role: ChatMessage["role"];
  images?: ChatImage[];
}>();

const html = computed(() =>
  props.role === "assistant" ? renderChatMarkdown(props.content) : "",
);
</script>

<template>
  <div v-if="images?.length" class="chat-images">
    <a
      v-for="img in images"
      :key="img.id"
      class="chat-image-link"
      :href="img.url"
      target="_blank"
      rel="noopener noreferrer"
    >
      <img
        class="chat-image-thumb"
        :src="img.url"
        :alt="img.filename ?? '截图'"
        loading="lazy"
      />
    </a>
  </div>
  <div v-if="role === 'assistant'" class="chat-md" v-html="html" />
  <p v-else class="chat-plain">{{ content }}</p>
</template>
