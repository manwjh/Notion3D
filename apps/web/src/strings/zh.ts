/** User-facing copy — no MCP / env var names in primary UI. */

export type WebChatMode = "agent" | "setup_required";

export const MODE_LABEL: Record<WebChatMode, string> = {
  agent: "智能设计",
  setup_required: "待连接助手",
};

export const MODE_HINT: Record<WebChatMode, string> = {
  agent: "设计助手会理解需求并生成可打印模型",
  setup_required: "Web 对话需先连接设计助手，点击右上角「助手」查看配置",
};

export const ASSISTANT_LABEL: Record<string, string> = {
  cursor_sdk: "Cursor 设计助手",
  openclaw: "OpenClaw 助手",
  cursor_cloud: "Cursor 云端助手",
};

export function assistantDisplayName(
  activeId: string | null | undefined,
  fallbackLabel: string | null | undefined,
): string {
  if (fallbackLabel) return fallbackLabel;
  if (activeId && ASSISTANT_LABEL[activeId]) return ASSISTANT_LABEL[activeId];
  return "设计助手";
}

export const SAMPLE_PROMPTS = [
  "20mm 测试立方体",
  "40×30×20mm 收纳盒",
  "直径 30mm 的球体",
  "手机支架，屏幕倾角约 15°",
];

export const WELCOME_STEPS = [
  { title: "连接助手", desc: "配置 CURSOR_API_KEY 并运行 make dev" },
  { title: "描述需求", desc: "用自然语言说尺寸、用途和结构" },
  { title: "看初稿", desc: "左侧出现预览，确认造型方向" },
  { title: "导出打印", desc: "满意后下载 STL 送去打印" },
] as const;
