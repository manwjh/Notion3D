export type ModelPick = {
  x: number;
  y: number;
  z: number;
  nx: number;
  ny: number;
  nz: number;
  label?: string | null;
  element?: string | null;
};

export function formatPickShort(pick: ModelPick): string {
  if (pick.element) {
    return pick.label ? `${pick.label} (${pick.element})` : pick.element;
  }
  return pick.label ?? `(${pick.x.toFixed(1)}, ${pick.y.toFixed(1)}, ${pick.z.toFixed(1)})`;
}

export function describePick(
  x: number,
  y: number,
  z: number,
  nx: number,
  ny: number,
  nz: number
): string {
  const horiz = Math.abs(nx) > Math.abs(ny) && Math.abs(nx) > Math.abs(nz);
  const vert = Math.abs(ny) >= Math.abs(nx) && Math.abs(ny) >= Math.abs(nz);

  const sides: string[] = [];
  if (y > 0.5) sides.push("上侧");
  else if (y < -0.5) sides.push("下侧");
  if (z > 0.5) sides.push("前侧");
  else if (z < -0.5) sides.push("后侧");
  if (x > 0.5) sides.push("右侧");
  else if (x < -0.5) sides.push("左侧");

  const region = sides.length > 0 ? sides.join("、") : "中心附近";
  const face =
    vert && ny > 0.5
      ? "顶面"
      : vert && ny < -0.5
        ? "底面"
        : horiz
          ? nx > 0
            ? "右侧面"
            : "左侧面"
          : nz > 0
            ? "前侧面"
            : "后侧面";

  return `(${x.toFixed(1)}, ${y.toFixed(1)}, ${z.toFixed(1)}) mm · ${region} · ${face}`;
}
