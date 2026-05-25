// Open enclosure — parametric box with front cutout
const outerW = param("Outer Width", 80, { min: 40, max: 200, unit: "mm" });
const outerL = param("Outer Length", 60, { min: 40, max: 200, unit: "mm" });
const outerH = param("Outer Height", 40, { min: 20, max: 120, unit: "mm" });
const wall = param("Wall", 1.8, { min: 1.2, max: 4, unit: "mm" });

const outer = box(outerW, outerL, outerH, true).color("#6EA8FE");
const inner = box(outerW - wall * 2, outerL - wall * 2, outerH - wall, true)
  .translate(0, 0, wall / 2);
const body = outer.subtract(inner);

const frontCut = box(outerW * 0.55, wall + 2, outerH * 0.55, true)
  .translate(0, outerL / 2 - wall, 0);

const enclosure = body.subtract(frontCut).color("#5B8DEF");

return [
  { name: "Enclosure", shape: enclosure },
];
