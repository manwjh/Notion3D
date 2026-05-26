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
  placeholderBusy: "正在建模，可先写好下一条…",
  placeholderPickElement: "说说想怎么改这个部件…",
  placeholderPick: "说说想怎么改这里…",
  placeholderHasModel: "继续描述想改什么…",
  placeholderDefault: "描述你想做的物件…",
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
} as const;

export function assistantDisplayName(
  _activeId: string | null | undefined,
  _fallbackLabel: string | null | undefined,
): string {
  return CHAT.assistantName;
}

export const DESIGN_PHASE_LABEL: Record<string, string> = {
  intake: "理解需求",
  plan: "制定方案",
  author: "编写模型",
  render: "渲染网格",
  review: "验收检查",
  done: "已完成",
  blocked: "已阻塞",
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
