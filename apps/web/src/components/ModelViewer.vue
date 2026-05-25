<script setup lang="ts">
import { nextTick, onMounted, onUnmounted, ref, watch } from "vue";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { STLLoader } from "three/examples/jsm/loaders/STLLoader.js";
import { describePick, type ModelPick } from "../types/pick";
import type { PartsManifest } from "../types/parts";

const props = withDefaults(
  defineProps<{
    stlUrl: string | null;
    partsUrl?: string | null;
    loading?: boolean;
    loadingLabel?: string | null;
    legacyIncomplete?: boolean;
    pickMode?: boolean;
    pick?: ModelPick | null;
  }>(),
  {
    loading: false,
    loadingLabel: null,
    legacyIncomplete: false,
    pickMode: false,
    pick: null,
    partsUrl: null,
  },
);

const emit = defineEmits<{ pick: [value: ModelPick]; "parts-loaded": [parts: PartsManifest["parts"]] }>();

const canvasHost = ref<HTMLElement | null>(null);
const error = ref<string | null>(null);
const meshLoading = ref(false);
const loadedParts = ref<PartsManifest["parts"]>([]);
const partMeshes = new Map<string, THREE.Mesh>();

let renderer: THREE.WebGLRenderer | null = null;
let scene: THREE.Scene | null = null;
let camera: THREE.PerspectiveCamera | null = null;
let controls: OrbitControls | null = null;
let mesh: THREE.Mesh | null = null;
let modelRoot: THREE.Group | null = null;
let pickGroup: THREE.Group | null = null;
let grid: THREE.GridHelper | null = null;
let animId = 0;
let raycaster = new THREE.Raycaster();
let pointer = new THREE.Vector2();

function alignGeometryOnBuildPlate(geometry: THREE.BufferGeometry) {
  geometry.rotateX(-Math.PI / 2);
  geometry.computeBoundingBox();
  const box = geometry.boundingBox;
  if (!box) return;
  const centerX = (box.min.x + box.max.x) / 2;
  const centerZ = (box.min.z + box.max.z) / 2;
  geometry.translate(-centerX, -box.min.y, -centerZ);
  geometry.computeVertexNormals();
  geometry.computeBoundingSphere();
}

function alignRootOnBuildPlate(root: THREE.Object3D) {
  root.rotation.x = -Math.PI / 2;
  root.updateMatrixWorld(true);
  const box = new THREE.Box3().setFromObject(root);
  const centerX = (box.min.x + box.max.x) / 2;
  const centerZ = (box.min.z + box.max.z) / 2;
  root.position.set(-centerX, -box.min.y, -centerZ);
  root.updateMatrixWorld(true);
}

function fitCameraToObject(object: THREE.Object3D) {
  if (!camera || !controls) return;
  const box = new THREE.Box3().setFromObject(object);
  const sphere = box.getBoundingSphere(new THREE.Sphere());
  if (!sphere || sphere.radius <= 0) return;
  const dist = (sphere.radius / Math.sin((camera.fov * Math.PI) / 360)) * 1.6;
  camera.position.set(
    sphere.center.x + dist,
    sphere.center.y + dist * 0.75,
    sphere.center.z + dist,
  );
  camera.near = Math.max(0.1, sphere.radius / 100);
  camera.far = dist * 20;
  camera.lookAt(sphere.center);
  camera.updateProjectionMatrix();
  controls.target.copy(sphere.center);
  controls.update();
}

function fitCamera(geometry: THREE.BufferGeometry) {
  if (!camera || !controls) return;
  geometry.computeBoundingSphere();
  const sphere = geometry.boundingSphere;
  if (!sphere) return;
  const dist = (sphere.radius / Math.sin((camera.fov * Math.PI) / 360)) * 1.6;
  camera.position.set(
    sphere.center.x + dist,
    sphere.center.y + dist * 0.75,
    sphere.center.z + dist,
  );
  camera.near = Math.max(0.1, sphere.radius / 100);
  camera.far = dist * 20;
  camera.lookAt(sphere.center);
  camera.updateProjectionMatrix();
  controls.target.copy(sphere.center);
  controls.update();
}

function clearPickMarker() {
  if (pickGroup && scene) {
    scene.remove(pickGroup);
    pickGroup.traverse((obj) => {
      if (obj instanceof THREE.Mesh) {
        obj.geometry.dispose();
        if (Array.isArray(obj.material)) obj.material.forEach((m) => m.dispose());
        else obj.material.dispose();
      }
    });
    pickGroup = null;
  }
}

function showPickMarker(pick: ModelPick) {
  if (!scene) return;
  clearPickMarker();
  pickGroup = new THREE.Group();
  pickGroup.position.set(pick.x, pick.y, pick.z);
  const normal = new THREE.Vector3(pick.nx, pick.ny, pick.nz).normalize();
  const quat = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 0, 1), normal);
  pickGroup.quaternion.copy(quat);

  const sphere = new THREE.Mesh(
    new THREE.SphereGeometry(1.2, 16, 16),
    new THREE.MeshBasicMaterial({ color: "#ffcc66", transparent: true, opacity: 0.95 }),
  );
  const ring = new THREE.Mesh(
    new THREE.RingGeometry(2.5, 3.2, 32),
    new THREE.MeshBasicMaterial({
      color: "#ffcc66",
      transparent: true,
      opacity: 0.55,
      side: THREE.DoubleSide,
    }),
  );
  ring.position.z = 0.5;
  pickGroup.add(sphere, ring);
  scene.add(pickGroup);
}

function disposeMesh() {
  if (mesh && scene) {
    scene.remove(mesh);
    mesh.geometry.dispose();
    if (Array.isArray(mesh.material)) mesh.material.forEach((m) => m.dispose());
    else mesh.material.dispose();
    mesh = null;
  }
  if (modelRoot && scene) {
    scene.remove(modelRoot);
    modelRoot.traverse((obj) => {
      if (obj instanceof THREE.Mesh) {
        obj.geometry.dispose();
        if (Array.isArray(obj.material)) obj.material.forEach((m) => m.dispose());
        else obj.material.dispose();
      }
    });
    modelRoot = null;
  }
  partMeshes.clear();
  loadedParts.value = [];
}

async function loadPartsManifest(url: string) {
  if (!scene) return;
  meshLoading.value = true;
  error.value = null;
  disposeMesh();
  try {
    const res = await fetch(url);
    if (!res.ok) {
      if (props.stlUrl) {
        meshLoading.value = false;
        await loadStl(props.stlUrl);
        return;
      }
      throw new Error("部件清单加载失败");
    }
    const manifest = (await res.json()) as PartsManifest;
    if (!manifest.parts?.length) throw new Error("部件清单为空");

    const loader = new STLLoader();
    const root = new THREE.Group();
    partMeshes.clear();
    for (const part of manifest.parts) {
      const geo = await loader.loadAsync(`${part.stl_url}?v=${encodeURIComponent(part.id)}`);
      geo.computeVertexNormals();
      const opacity = part.opacity ?? 1;
      const partMesh = new THREE.Mesh(
        geo,
        new THREE.MeshStandardMaterial({
          color: part.color,
          metalness: 0.12,
          roughness: 0.45,
          transparent: opacity < 1,
          opacity,
        }),
      );
      partMesh.castShadow = true;
      partMesh.receiveShadow = true;
      partMesh.userData.partId = part.id;
      partMesh.userData.partLabel = part.label;
      partMeshes.set(part.id, partMesh);
      root.add(partMesh);
    }
    loadedParts.value = manifest.parts;
    emit("parts-loaded", manifest.parts);
    alignRootOnBuildPlate(root);
    modelRoot = root;
    scene.add(root);
    fitCameraToObject(root);
  } catch (e) {
    error.value = e instanceof Error ? e.message : "模型加载失败";
  } finally {
    meshLoading.value = false;
  }
}

async function loadStl(url: string) {
  if (!scene) return;
  meshLoading.value = true;
  error.value = null;
  disposeMesh();
  try {
    const loader = new STLLoader();
    const geo = await loader.loadAsync(url);
    alignGeometryOnBuildPlate(geo);
    mesh = new THREE.Mesh(
      geo,
      new THREE.MeshStandardMaterial({
        color: props.pickMode ? "#8ec0ff" : "#6ea8fe",
        metalness: 0.12,
        roughness: 0.45,
      }),
    );
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    scene.add(mesh);
    fitCamera(geo);
  } catch (e) {
    error.value = e instanceof Error ? e.message : "模型加载失败";
  } finally {
    meshLoading.value = false;
  }
}

function onPointerClick(ev: MouseEvent) {
  if (!props.pickMode || !camera || !canvasHost.value) return;
  const target = modelRoot ?? mesh;
  if (!target) return;
  const rect = canvasHost.value.getBoundingClientRect();
  pointer.x = ((ev.clientX - rect.left) / rect.width) * 2 - 1;
  pointer.y = -((ev.clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(pointer, camera);
  const hits = modelRoot
    ? raycaster.intersectObjects(modelRoot.children, true)
    : raycaster.intersectObject(mesh as THREE.Mesh);
  if (hits.length === 0) return;
  const hit = hits[0];
  const p = hit.point;
  const n = hit.face?.normal?.clone() ?? new THREE.Vector3(0, 1, 0);
  const hitMesh = hit.object as THREE.Mesh;
  n.transformDirection(hitMesh.matrixWorld).normalize();
  const partId = hitMesh.userData.partId as string | undefined;
  const partLabel = hitMesh.userData.partLabel as string | undefined;
  emit("pick", {
    x: p.x,
    y: p.y,
    z: p.z,
    nx: n.x,
    ny: n.y,
    nz: n.z,
    element: partId ?? null,
    label: partId
      ? partLabel ?? partId
      : describePick(p.x, p.y, p.z, n.x, n.y, n.z),
  });
}

function onPointerMove() {
  if (props.pickMode) document.body.style.cursor = "crosshair";
}

function onPointerLeave() {
  document.body.style.cursor = "";
}

function animate() {
  animId = requestAnimationFrame(animate);
  controls?.update();
  if (renderer && scene && camera) renderer.render(scene, camera);
}

function resizeRenderer() {
  if (!canvasHost.value || !renderer || !camera) return;
  const w = canvasHost.value.clientWidth;
  const h = canvasHost.value.clientHeight;
  if (w <= 0 || h <= 0) return;
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  renderer.setSize(w, h, false);
}

function initThree() {
  if (!canvasHost.value || scene) return;
  scene = new THREE.Scene();
  scene.background = new THREE.Color("#141820");
  camera = new THREE.PerspectiveCamera(45, 1, 0.1, 10000);
  camera.position.set(120, 90, 120);
  renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" });
  renderer.shadowMap.enabled = true;
  renderer.domElement.style.width = "100%";
  renderer.domElement.style.height = "100%";
  renderer.domElement.style.display = "block";
  renderer.domElement.addEventListener("webglcontextlost", (e) => e.preventDefault());
  canvasHost.value.appendChild(renderer.domElement);

  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;

  scene.add(new THREE.AmbientLight(0xffffff, 0.65));
  const d1 = new THREE.DirectionalLight(0xffffff, 1.2);
  d1.position.set(80, 120, 60);
  d1.castShadow = true;
  scene.add(d1);
  const d2 = new THREE.DirectionalLight(0xffffff, 0.4);
  d2.position.set(-60, 40, -40);
  scene.add(d2);
  grid = new THREE.GridHelper(300, 30, 0x3a4254, 0x252b36);
  scene.add(grid);

  renderer.domElement.addEventListener("click", onPointerClick);
  renderer.domElement.addEventListener("pointermove", onPointerMove);
  renderer.domElement.addEventListener("pointerleave", onPointerLeave);

  const ro = new ResizeObserver(resizeRenderer);
  ro.observe(canvasHost.value);
  (canvasHost.value as HTMLElement & { _ro?: ResizeObserver })._ro = ro;

  animate();
  resizeRenderer();
  if (props.partsUrl) void loadPartsManifest(props.partsUrl);
  else if (props.stlUrl) void loadStl(props.stlUrl);
}

async function ensureViewerReady() {
  await nextTick();
  initThree();
  resizeRenderer();
  if (props.partsUrl && scene) await loadPartsManifest(props.partsUrl);
  else if (props.stlUrl && scene) await loadStl(props.stlUrl);
}

function destroyThree() {
  cancelAnimationFrame(animId);
  disposeMesh();
  clearPickMarker();
  if (canvasHost.value) {
    const el = canvasHost.value as HTMLElement & { _ro?: ResizeObserver };
    el._ro?.disconnect();
    if (renderer) {
      renderer.domElement.removeEventListener("click", onPointerClick);
      renderer.domElement.removeEventListener("pointermove", onPointerMove);
      renderer.domElement.removeEventListener("pointerleave", onPointerLeave);
      renderer.dispose();
      canvasHost.value.removeChild(renderer.domElement);
    }
  }
  grid?.geometry.dispose();
  if (grid?.material instanceof THREE.Material) grid.material.dispose();
  renderer = null;
  scene = null;
  camera = null;
  controls = null;
  grid = null;
}

watch(
  () => [props.stlUrl, props.partsUrl] as const,
  ([url, partsUrl]) => {
    error.value = null;
    void ensureViewerReady().then(() => {
      if (!url && !partsUrl) disposeMesh();
    });
  },
);

watch(
  () => props.loading,
  () => {
    if (props.stlUrl) void ensureViewerReady();
  },
);

watch(
  () => props.pickMode,
  (mode) => {
    if (controls) controls.enabled = !mode;
    const tint = mode ? "#8ec0ff" : null;
    if (mesh?.material instanceof THREE.MeshStandardMaterial && tint) {
      mesh.material.color.set(tint);
    } else if (mesh?.material instanceof THREE.MeshStandardMaterial) {
      mesh.material.color.set("#6ea8fe");
    }
    if (modelRoot) {
      modelRoot.traverse((obj) => {
        if (!(obj instanceof THREE.Mesh)) return;
        const mat = obj.material;
        if (!(mat instanceof THREE.MeshStandardMaterial)) return;
        if (mode) mat.emissive.set("#224466");
        else mat.emissive.set("#000000");
      });
    }
    if (!mode) document.body.style.cursor = "";
  },
);

watch(
  () => props.pick,
  (p) => {
    if (p) showPickMarker(p);
    else clearPickMarker();
  },
);

onMounted(() => {
  void ensureViewerReady();
});
onUnmounted(destroyThree);

function setPartVisible(partId: string, visible: boolean) {
  const mesh = partMeshes.get(partId);
  if (mesh) mesh.visible = visible;
}

function setPartOpacity(partId: string, opacity: number) {
  const mesh = partMeshes.get(partId);
  if (!mesh) return;
  const mat = mesh.material;
  if (!(mat instanceof THREE.MeshStandardMaterial)) return;
  mat.transparent = opacity < 1;
  mat.opacity = opacity;
  mat.needsUpdate = true;
}

function fitPart(partId: string) {
  const mesh = partMeshes.get(partId);
  if (mesh) fitCameraToObject(mesh);
}

function highlightPart(partId: string | null) {
  for (const [id, mesh] of partMeshes) {
    const mat = mesh.material;
    if (!(mat instanceof THREE.MeshStandardMaterial)) continue;
    if (partId && id === partId) {
      mat.emissive.set("#554400");
      mat.emissiveIntensity = 0.45;
    } else {
      mat.emissive.set("#000000");
      mat.emissiveIntensity = 1;
    }
    mat.needsUpdate = true;
  }
}

function fitAll() {
  if (modelRoot) fitCameraToObject(modelRoot);
  else if (mesh) fitCameraToObject(mesh);
}

defineExpose({ setPartVisible, setPartOpacity, fitPart, fitAll, highlightPart, loadedParts });
</script>

<template>
  <div class="viewer-shell">
    <div
      ref="canvasHost"
      class="viewer-root viewer-root--canvas"
      :class="{ 'viewer-root--pick': pickMode, 'viewer-root--hidden': !stlUrl }"
    >
      <div v-if="pickMode" class="viewer-pick-hint">
        点击模型部件（有分色标注时按元素选中），回对话区描述修改
      </div>
      <p v-if="error" class="viewer-error">{{ error }}</p>
      <span v-if="meshLoading" class="viewer-loading viewer-loading--overlay">加载模型…</span>
    </div>

    <div v-if="loading && !stlUrl" class="viewer-overlay viewer-root viewer-root--loading">
      <div class="viewer-loading-card">
        <span class="spinner" aria-hidden="true" />
        <p>{{ loadingLabel ?? "正在生成 3D 模型…" }}</p>
        <span class="viewer-loading-hint">完成后可在此旋转观察、点选修改</span>
      </div>
    </div>

    <div v-else-if="legacyIncomplete && !stlUrl" class="viewer-overlay viewer-root viewer-root--legacy">
      <div class="viewer-empty">
        <p>此版本缺少 3D 模型</p>
        <span>这是旧版未完成的数据。请用右上角 ⋯ →「生成可打印模型」补全。</span>
      </div>
    </div>

    <div v-else-if="!stlUrl" class="viewer-overlay viewer-root">
      <div class="viewer-empty">
        <div class="viewer-empty-icon" aria-hidden="true"><span /><span /><span /></div>
        <p>暂无图纸</p>
        <span>在对话区描述需求，3D 模型生成后会显示在这里</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.viewer-shell {
  position: relative;
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.viewer-overlay {
  position: absolute;
  inset: 0;
  z-index: 2;
}

.viewer-root--hidden {
  visibility: hidden;
  pointer-events: none;
}

.viewer-shell .viewer-root {
  flex: 1;
  min-height: 200px;
}

.viewer-root--canvas {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 200px;
}

.viewer-root--loading,
.viewer-root--legacy {
  display: flex;
  align-items: center;
  justify-content: center;
}

.viewer-loading-card {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.65rem;
  padding: 1.5rem;
}

.viewer-loading-card p {
  margin: 0;
  color: #c5cad6;
  font-size: 0.95rem;
}

.viewer-loading-hint {
  color: #6b7280;
  font-size: 0.82rem;
  max-width: 280px;
  line-height: 1.45;
}

.viewer-loading--overlay {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  z-index: 2;
}
</style>
