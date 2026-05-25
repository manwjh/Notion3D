/** 旧版流水线写入的系统话术，不应再展示为助手回复 */
const LEGACY_SYSTEM_REPLIES = [
  "设计助手正在理解需求并建模，左侧将陆续出现预览…",
  "设计助手正在理解需求并建模，右侧将陆续出现预览…",
] as const;

const LEGACY_SYSTEM_REPLY_RES = [
  /^初稿 v\d+ 好了，左侧可以预览/,
  /^初稿 v\d+ 好了，右侧可以预览/,
  /^已从 (SCAD|ForgeCAD) 渲染版本 v\d+/,
  /^Cursor SDK Agent 已完成/,
  /^Hermes Agent 已完成/,
];

export function isLegacySystemReply(content: string): boolean {
  if (LEGACY_SYSTEM_REPLIES.includes(content as (typeof LEGACY_SYSTEM_REPLIES)[number])) {
    return true;
  }
  return LEGACY_SYSTEM_REPLY_RES.some((re) => re.test(content));
}

export function filterChatMessages<T extends { role: string; content: string }>(messages: T[]): T[] {
  return messages.filter((m) => m.role !== "assistant" || !isLegacySystemReply(m.content));
}
