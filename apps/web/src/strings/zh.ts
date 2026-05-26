/** User-facing copy — agent backend is invisible; no MCP / env / provider names. */

export type WebChatMode = "agent" | "setup_required";

export const CHAT = {
  panelTitle: "对话",
  assistantName: "Notion3D",
  hintReady: "描述需求，生成并更新 3D 模型",
  hintUnavailable: "自然语言建模暂不可用，可使用左栏编辑模型",
  checking: "正在连接服务…",
  processing: "正在建模…",
  submitChecking: "正在连接服务，请稍候再试",
  submitUnavailable: "自然语言建模暂不可用，请使用左栏编辑",
  submitBusy: "上一条仍在处理，请稍候…",
  onboardingTitle: "用自然语言描述，生成 3D 模型",
  onboardingBody: "新建项目后在这里描述需求，中间视口会显示模型。",
  continueTitle: "继续改方案",
  startTitle: "说说你想做什么",
  continueHint: "直接描述想改什么。",
  placeholderNoProject: "先新建项目，然后描述想要的 3D 物件…",
  placeholderUnavailable: "自然语言建模暂不可用，可使用左栏编辑…",
  placeholderChecking: "正在连接服务…",
  placeholderBusy: "正在建模，完成后可继续发送…",
  placeholderPickElement: "说说想怎么改这个部件…",
  placeholderPick: "说说想怎么改这里…",
  placeholderHasModel: "继续描述想改什么…",
  placeholderDefault: "描述你想做的物件…",
  inputHint: "Enter 发送，Shift+Enter 换行；可粘贴图片",
  attachScreenshot: "附视口截图",
  attachImage: "添加图片",
  removeImage: "移除图片",
  screenshotAttached: "已附视口截图",
  screenshotFailed: "截屏失败：请确认中间视口已加载模型",
  screenshotNeedModel: "请先生成或选择带模型的方案",
  imageLimit: "最多 3 张图片",
  sendLabel: "发送",
  sendBusy: "发送中",
  pickElement: "选中部件",
  pickLocation: "点选位置",
  clearPick: "清除",
  prefillModify: (name: string) => `请修改「${name}」：`,
  submitFailed: "发送失败，请稍后重试",
  activityFallback: "处理中…",
  roleUser: "你",
  roleSystem: "系统",
  versionLabel: "方案",
} as const;

export const WORKBENCH = {
  viewportEmpty: "新建项目并描述需求，模型会显示在这里",
  structureEmpty: "创建项目并开始建模后，结构面板会显示在这里。",
  mobileChatTab: "对话",
} as const;

export const STATUS = {
  popoverTitle: "服务状态",
  serviceUnreachable: "无法连接 Notion3D 服务",
  forgeReady: "就绪",
  forgeMissing: "渲染引擎未就绪",
  workbenchReady: "工作台就绪",
  workbenchMissing: "服务未连接",
} as const;

export const STATUS_BAR = {
  noProject: "未选择项目",
  noModel: "暂无模型",
  pendingMesh: "待生成可打印模型",
  manualEditOnly: "仅手动编辑",
  partCount: (count: number) => `${count} 个部件`,
  selectedPart: (label: string) => `选中 ${label}`,
  validationCount: (count: number) => `${count} 条校验提示`,
  validationTitle: "装配 / 模型校验",
} as const;

export function assistantDisplayName(
  _activeId: string | null | undefined,
  _fallbackLabel: string | null | undefined,
): string {
  return CHAT.assistantName;
}

export const DESIGN_PHASE_LABEL: Record<string, string> = {
  intake: "建模中",
  plan: "建模中",
  author: "建模中",
  render: "渲染中",
  review: "核对中",
  done: "完成",
  blocked: "失败",
};

export const PLAN_STRATEGY_LABEL: Record<string, string> = {
  template_apply: "应用模板",
  template_edit: "改模板源码",
  from_scratch: "从零编写",
  chat_only: "仅对话",
};

export const REVIEW_STATUS_LABEL: Record<string, string> = {
  pass: "通过",
  retry: "需修改",
  accept_warnings: "接受警告",
};
