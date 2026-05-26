// Rectangular enclosure — sketch_extrude_shell recipe
const outerW = param("Outer Width", 90, { min: 50, max: 200, unit: "mm" });
const outerL = param("Outer Length", 60, { min: 40, max: 150, unit: "mm" });
const outerH = param("Outer Height", 40, { min: 20, max: 120, unit: "mm" });
const wall = param("Wall", 2.5, { min: 1.5, max: 6, unit: "mm" });
const filletR = param("Corner Fillet", 2, { min: 0, max: 6, unit: "mm" });

const outerSketch = (() => {
  const sk = constrainedSketch();
  const p0 = sk.point(0, 0);
  const p1 = sk.point(outerW, 0);
  const p2 = sk.point(outerW, outerL);
  const p3 = sk.point(0, outerL);
  const bottom = sk.line(p0, p1);
  const right = sk.line(p1, p2);
  sk.line(p2, p3);
  sk.line(p3, p0);
  sk.addLoop([p0, p1, p2, p3]);
  sk.fix(p0);
  sk.horizontal(bottom);
  sk.vertical(right);
  sk.length(bottom, outerW);
  sk.length(right, outerL);
  return sk.solve();
})();

const outerBody = outerSketch.extrude(outerH);
const inner = box(outerW - wall * 2, outerL - wall * 2, outerH - wall, true)
  .translate(wall, wall, wall);
let shellBody = outerBody.subtract(inner);
if (filletR > 0 && typeof shellBody.fillet === "function") {
  shellBody = shellBody.fillet(filletR);
}

return [{ name: "EnclosureShell", shape: shellBody.color("#6EA8FE") }];
