import { nextTick, onMounted, onUnmounted, ref, watch, type ComputedRef, type Ref } from "vue";
import type ViewportHost from "../components/ViewportHost.vue";
import type ChatPanel from "../components/ChatPanel.vue";
import type { ModelPart } from "../types/parts";
import type { ModelPick } from "../types/pick";

export function useWorkbenchViewport(options: {
  selectedVersion: Ref<number | null>;
  narrowLayout: Ref<boolean>;
  mobilePanel: Ref<"structure" | "viewport" | "chat">;
}) {
  const { selectedVersion, mobilePanel } = options;

  const modelPick = ref<ModelPick | null>(null);
  const viewportParts = ref<ModelPart[]>([]);
  const partHidden = ref<Record<string, boolean>>({});
  const partOpacities = ref<Record<string, number>>({});
  const viewportRef = ref<InstanceType<typeof ViewportHost> | null>(null);
  const chatPanelRef = ref<InstanceType<typeof ChatPanel> | null>(null);

  watch(selectedVersion, () => {
    modelPick.value = null;
    viewportParts.value = [];
    partHidden.value = {};
    partOpacities.value = {};
  });

  function onPartsLoaded(parts: ModelPart[]) {
    viewportParts.value = parts;
    partHidden.value = {};
    partOpacities.value = {};
    for (const part of parts) {
      partOpacities.value[part.id] = part.opacity ?? 1;
    }
    viewportRef.value?.applyPartDefaults(parts);
    if (modelPick.value?.element) {
      viewportRef.value?.highlightPart(modelPick.value.element);
    }
  }

  function onModelPick(pick: ModelPick) {
    if (
      modelPick.value?.element &&
      pick.element &&
      modelPick.value.element === pick.element
    ) {
      onClearPartPick();
      return;
    }
    modelPick.value = pick;
    mobilePanel.value = "chat";
    viewportRef.value?.highlightPart(pick.element ?? null);
    void nextTick(() => {
      chatPanelRef.value?.prefillFromPick?.(pick);
      chatPanelRef.value?.focusInput();
    });
  }

  function onPartPick(part: ModelPart) {
    if (modelPick.value?.element === part.id) {
      onClearPartPick();
      return;
    }
    onModelPick({
      x: 0,
      y: 0,
      z: 0,
      nx: 0,
      ny: 1,
      nz: 0,
      element: part.id,
      label: part.label,
    });
  }

  function onClearPartPick() {
    modelPick.value = null;
    viewportRef.value?.highlightPart(null);
  }

  function onTogglePart(partId: string) {
    partHidden.value[partId] = !partHidden.value[partId];
    viewportRef.value?.setPartVisible(partId, !partHidden.value[partId]);
  }

  function onPartOpacity(partId: string, value: number) {
    partOpacities.value[partId] = value;
    viewportRef.value?.setPartOpacity(partId, value);
  }

  function onFocusPart(partId: string) {
    viewportRef.value?.fitPart(partId);
  }

  function onShowAllParts() {
    for (const part of viewportParts.value) {
      partHidden.value[part.id] = false;
      viewportRef.value?.setPartVisible(part.id, true);
    }
  }

  function onFitAllParts() {
    viewportRef.value?.fitAll();
  }

  function onShellMode() {
    for (const part of viewportParts.value) {
      const isShell = /shell|外壳|壳/i.test(part.label);
      const opacity = isShell ? 0.25 : 1;
      partOpacities.value[part.id] = opacity;
      viewportRef.value?.setPartOpacity(part.id, opacity);
      partHidden.value[part.id] = false;
      viewportRef.value?.setPartVisible(part.id, true);
    }
  }

  return {
    modelPick,
    viewportParts,
    partHidden,
    partOpacities,
    viewportRef,
    chatPanelRef,
    onPartsLoaded,
    onModelPick,
    onPartPick,
    onClearPartPick,
    onTogglePart,
    onPartOpacity,
    onFocusPart,
    onShowAllParts,
    onFitAllParts,
    onShellMode,
  };
}

export function useWorkbenchLayout(options: {
  hasModel: Ref<boolean>;
  stlReady: ComputedRef<boolean | undefined>;
  followLatestVersion: Ref<boolean>;
}) {
  const narrowLayout = ref(false);
  const mobilePanel = ref<"structure" | "viewport" | "chat">("chat");

  onMounted(() => {
    const mq = window.matchMedia("(max-width: 1024px)");
    const syncLayout = () => {
      narrowLayout.value = mq.matches;
    };
    syncLayout();
    mq.addEventListener("change", syncLayout);
    onUnmounted(() => mq.removeEventListener("change", syncLayout));
  });

  watch(options.hasModel, (value, previous) => {
    if (value && !previous && narrowLayout.value) {
      mobilePanel.value = "viewport";
    }
  });

  watch(
    () => options.stlReady.value,
    (ready, wasReady) => {
      if (ready && !wasReady && options.followLatestVersion.value && narrowLayout.value) {
        mobilePanel.value = "viewport";
      }
    },
  );

  function focusMobilePanel(panel: "structure" | "viewport" | "chat") {
    mobilePanel.value = panel;
  }

  return { narrowLayout, mobilePanel, focusMobilePanel };
}
