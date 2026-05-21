import { createRouter, createWebHistory } from "vue-router";
import WorkbenchPage from "../pages/WorkbenchPage.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "home", component: WorkbenchPage },
    { path: "/p/:projectId", name: "project", component: WorkbenchPage },
    { path: "/workbench/:pathMatch(.*)*", redirect: "/" },
    { path: "/:pathMatch(.*)*", redirect: "/" },
  ],
});

export default router;
