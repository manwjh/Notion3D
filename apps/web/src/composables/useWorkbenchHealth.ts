import { onMounted, onUnmounted, ref } from "vue";
import { health, type Health } from "../api/client";

export function useWorkbenchHealth(pollMs = 30000) {
  const sysHealth = ref<Health | null>(null);

  async function refreshHealth() {
    try {
      sysHealth.value = await health();
    } catch {
      sysHealth.value = null;
    }
  }

  onMounted(() => {
    refreshHealth();
    const timer = setInterval(refreshHealth, pollMs);
    onUnmounted(() => clearInterval(timer));
  });

  return { sysHealth, refreshHealth };
}
