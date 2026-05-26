// Streamlined hull — loft recipe (simplified)
const length = param("Length", 92, { min: 60, max: 150, unit: "mm" });
const beam = param("Beam", 42, { min: 24, max: 70, unit: "mm" });
const hullH = param("Hull Height", 34, { min: 18, max: 60, unit: "mm" });

const mkSection = (w, h) =>
  spline2d(
    [
      [w * 0.5, 0],
      [w * 0.35, h * 0.45],
      [0, h * 0.55],
      [-w * 0.35, h * 0.45],
      [-w * 0.5, 0],
      [-w * 0.35, -h * 0.25],
      [0, -h * 0.3],
      [w * 0.35, -h * 0.25],
    ],
    { closed: true, samplesPerSegment: 8, tension: 0.4 },
  );

const z1 = length * 0.25;
const z2 = length * 0.55;
const z3 = length * 0.85;

const hull = loft(
  [
    mkSection(beam * 0.45, hullH * 0.7),
    mkSection(beam, hullH),
    mkSection(beam * 0.35, hullH * 0.75),
    mkSection(beam * 0.12, hullH * 0.35),
  ],
  [0, z1, z2, z3],
  { edgeLength: 1.0 },
)
  .rotate(0, 90, 0)
  .color("#7F8C8D");

return [{ name: "HullBody", shape: hull }];
