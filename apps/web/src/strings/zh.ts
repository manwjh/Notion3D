/** User-facing copy — no MCP / env var names in primary UI. */

export type WebChatMode = "agent" | "setup_required";

export const MODE_LABEL: Record<WebChatMode, string> = {
  agent: "已连接",
  setup_required: "未连接",
};

export const MODE_HINT: Record<WebChatMode, string> = {
  agent: "直接描述需求，助手会生成并更新 3D 模型",
  setup_required: "需先连接设计助手，点击右上角「助手」",
};

export const ASSISTANT_LABEL: Record<string, string> = {
  cursor_sdk: "Cursor 设计助手",
  hermes: "Hermes 设计助手",
};

export function assistantDisplayName(
  activeId: string | null | undefined,
  fallbackLabel: string | null | undefined,
): string {
  if (fallbackLabel) return fallbackLabel;
  if (activeId && ASSISTANT_LABEL[activeId]) return ASSISTANT_LABEL[activeId];
  return "设计助手";
}
