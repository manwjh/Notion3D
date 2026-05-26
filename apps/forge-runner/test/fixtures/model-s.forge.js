// Tesla Model S — layout silhouette (loft-hull derivative, B-class layout_only)
const carLength = param("Length", 200, { min: 150, max: 280, unit: "mm" });
const carWidth = param("Width", 79, { min: 60, max: 100, unit: "mm" });
const carHeight = param("Height", 52, { min: 40, max: 70, unit: "mm" });
const wheelRadius = param("Wheel Radius", 17, { min: 12, max: 22, unit: "mm" });
const wheelWidth = param("Wheel Width", 10, { min: 6, max: 14, unit: "mm" });

const mkSection = (wMul, hMul, taper) => {
  const hw = carWidth * 0.5 * wMul * taper;
  const ht = carHeight * hMul;
  const hb = carHeight * 0.22 * hMul;
  return spline2d(
    [
      [hw, ht * 0.12],
      [hw * 0.88, ht * 0.72],
      [hw * 0.15, ht],
      [-hw * 0.15, ht],
      [-hw * 0.88, ht * 0.72],
      [-hw, ht * 0.12],
      [-hw * 0.95, 0],
      [-hw * 0.72, -hb],
      [0, -hb * 1.08],
      [hw * 0.72, -hb],
      [hw * 0.95, 0],
    ],
    { closed: true, samplesPerSegment: 10, tension: 0.36 },
  );
};

const s0 = 0;
const s1 = carLength * 0.14;
const s2 = carLength * 0.32;
const s3 = carLength * 0.48;
const s4 = carLength * 0.66;
const s5 = carLength * 0.84;
const s6 = carLength;

const bodySolid = loft(
  [
    mkSection(0.52, 0.38, 0.72),
    mkSection(0.88, 0.58, 0.92),
    mkSection(1.0, 1.0, 1.0),
    mkSection(0.96, 0.92, 0.98),
    mkSection(0.72, 0.68, 0.88),
    mkSection(0.48, 0.42, 0.78),
    mkSection(0.35, 0.32, 0.65),
  ],
  [s0, s1, s2, s3, s4, s5, s6],
  { edgeLength: 1.1 },
)
  .rotate(0, 90, 0)
  .translate(-carLength / 2, 0, wheelRadius + carHeight * 0.08);

const bodyShell = bodySolid.color("#F0F0F0");

const glassLen = carLength * 0.38;
const glassW = carWidth * 0.48;
const glassSketch = (() => {
  const sk = constrainedSketch();
  const p0 = sk.point(-glassLen * 0.48, 0);
  const p1 = sk.point(glassLen * 0.42, 0);
  const p2 = sk.point(glassLen * 0.32, glassW);
  const p3 = sk.point(-glassLen * 0.38, glassW * 0.85);
  sk.line(p0, p1);
  sk.line(p1, p2);
  sk.line(p2, p3);
  sk.line(p3, p0);
  sk.addLoop([p0, p1, p2, p3]);
  sk.fix(p0);
  return sk.solve();
})();

const glassZ = wheelRadius + carHeight * 0.72;
const cabinGlass = glassSketch
  .extrude(2)
  .translate(carLength * 0.02, 0, glassZ)
  .color("#6EB5D9");

const trackHalf = carWidth * 0.42;
const frontAxle = -carLength * 0.22;
const rearAxle = carLength * 0.22;

const mkWheel = () =>
  cylinder(wheelWidth, wheelRadius, wheelRadius, 32, true)
    .rotate(90, 0, 0)
    .color("#1A1A1A");

const wheelFL = mkWheel().translate(frontAxle, -trackHalf, wheelRadius);
const wheelFR = mkWheel().translate(frontAxle, trackHalf, wheelRadius);
const wheelRL = mkWheel().translate(rearAxle, -trackHalf, wheelRadius);
const wheelRR = mkWheel().translate(rearAxle, trackHalf, wheelRadius);

return [
  { name: "BodyShell", shape: bodyShell },
  { name: "CabinGlass", shape: cabinGlass },
  { name: "WheelFrontLeft", shape: wheelFL },
  { name: "WheelFrontRight", shape: wheelFR },
  { name: "WheelRearLeft", shape: wheelRL },
  { name: "WheelRearRight", shape: wheelRR },
];
