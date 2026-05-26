<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue";
import { highlightForgeCode, lineCount } from "../utils/forgeSyntax";

const props = defineProps<{
  modelValue: string;
  highlightLines?: { start: number; end: number } | null;
  disabled?: boolean;
  readonly?: boolean;
  placeholder?: string;
  minHeight?: string;
  maxHeight?: string;
  showLineNumbers?: boolean;
  compact?: boolean;
}>();

const emit = defineEmits<{ "update:modelValue": [value: string] }>();

const textareaRef = ref<HTMLTextAreaElement | null>(null);
const highlightRef = ref<HTMLPreElement | null>(null);
const gutterRef = ref<HTMLPreElement | null>(null);

const lineHeightPx = computed(() => (props.compact ? 16 : 18));
const fontSize = computed(() => (props.compact ? "0.68rem" : "0.78rem"));

const highlighted = computed(() => highlightForgeCode(props.modelValue || "", props.highlightLines));

const gutterText = computed(() => {
  const n = lineCount(props.modelValue || "");
  return Array.from({ length: n }, (_, i) => String(i + 1)).join("\n");
});

function syncScroll() {
  const ta = textareaRef.value;
  const hi = highlightRef.value;
  const gut = gutterRef.value;
  if (!ta) return;
  if (hi) hi.scrollTop = ta.scrollTop;
  if (gut) gut.scrollTop = ta.scrollTop;
}

function onInput(event: Event) {
  emit("update:modelValue", (event.target as HTMLTextAreaElement).value);
}

function scrollToHighlight() {
  const el = textareaRef.value;
  const hl = props.highlightLines;
  if (!el || !hl || !props.modelValue) return;

  const lines = props.modelValue.split("\n");
  let startPos = 0;
  for (let i = 0; i < hl.start - 1; i += 1) startPos += lines[i].length + 1;

  let endPos = startPos;
  for (let i = hl.start - 1; i < Math.min(hl.end, lines.length); i += 1) {
    endPos += lines[i].length + (i < lines.length - 1 ? 1 : 0);
  }

  el.focus({ preventScroll: true });
  el.setSelectionRange(startPos, Math.max(startPos, endPos));
  el.scrollTop = Math.max(0, (hl.start - 4) * lineHeightPx.value);
  syncScroll();
}

watch(
  () => [props.highlightLines, props.modelValue] as const,
  () => {
    if (!props.highlightLines) return;
    void nextTick(scrollToHighlight);
  },
  { flush: "post" },
);

defineExpose({ scrollToHighlight });
</script>

<template>
  <div
    class="forge-code-editor"
    :class="{
      'forge-code-editor--compact': compact,
      'forge-code-editor--highlighted': highlightLines,
      'forge-code-editor--readonly': readonly,
    }"
    :style="{ minHeight, maxHeight }"
  >
    <pre
      v-if="showLineNumbers !== false"
      ref="gutterRef"
      class="forge-code-gutter"
      aria-hidden="true"
      :style="{ fontSize, lineHeight: `${lineHeightPx}px` }"
    >{{ gutterText }}</pre>

    <div class="forge-code-stack">
      <pre
        ref="highlightRef"
        class="forge-code-highlight"
        aria-hidden="true"
        :style="{ fontSize, lineHeight: `${lineHeightPx}px` }"
        v-html="highlighted"
      />
      <textarea
        ref="textareaRef"
        class="forge-code-input forge-editor"
        :value="modelValue"
        :placeholder="placeholder"
        spellcheck="false"
        :disabled="disabled"
        :readonly="readonly"
        :style="{ fontSize, lineHeight: `${lineHeightPx}px` }"
        @input="onInput"
        @scroll="syncScroll"
      />
    </div>
  </div>
</template>

<style scoped>
.forge-code-editor {
  display: flex;
  min-height: 100px;
  max-height: 160px;
  border: 1px solid #2a3140;
  border-radius: 4px;
  background: #0a0c10;
  overflow: hidden;
}

.forge-code-editor--highlighted {
  box-shadow: inset 0 0 0 1px rgba(110, 168, 254, 0.35);
}

.forge-code-gutter {
  margin: 0;
  padding: 0.45rem 0.35rem 0.45rem 0.5rem;
  text-align: right;
  color: #4a5568;
  user-select: none;
  overflow: hidden;
  flex-shrink: 0;
  font-family: ui-monospace, Menlo, Monaco, Consolas, monospace;
  white-space: pre;
}

.forge-code-stack {
  position: relative;
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.forge-code-highlight,
.forge-code-input {
  position: absolute;
  inset: 0;
  margin: 0;
  padding: 0.45rem 0.5rem;
  border: none;
  font-family: ui-monospace, Menlo, Monaco, Consolas, monospace;
  white-space: pre;
  overflow: auto;
  tab-size: 2;
}

.forge-code-highlight {
  pointer-events: none;
  color: #d4dae6;
}

.forge-code-input {
  resize: none;
  background: transparent;
  color: transparent;
  caret-color: #d4dae6;
}

.forge-code-input:focus {
  outline: none;
}

.forge-code-input::placeholder {
  color: #5a6478;
}

.forge-code-editor--readonly .forge-code-input {
  caret-color: transparent;
}

:deep(.forge-tok-keyword) {
  color: #c792ea;
}

:deep(.forge-tok-builtin) {
  color: #82aaff;
}

:deep(.forge-tok-fn) {
  color: #7fdbca;
}

:deep(.forge-tok-string) {
  color: #ecc48d;
}

:deep(.forge-tok-number) {
  color: #f78c6c;
}

:deep(.forge-tok-comment) {
  color: #637777;
}

:deep(.forge-tok-ident) {
  color: #d4dae6;
}

:deep(.forge-line) {
  display: block;
}

:deep(.forge-line--focus) {
  background: rgba(110, 168, 254, 0.12);
}
</style>
