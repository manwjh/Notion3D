// L-bracket — union_bracket recipe: plate union + fillet
const w = param("Width", 80, { min: 40, max: 150, unit: "mm" });
const h = param("Height", 60, { min: 30, max: 100, unit: "mm" });
const d = param("Depth", 40, { min: 20, max: 80, unit: "mm" });
const t = param("Thickness", 5, { min: 2, max: 15, unit: "mm" });
const filletR = param("Fillet", 2, { min: 0.5, max: 8, unit: "mm" });

const base = box(w, d, t, true);
const wall = box(t, d, h, true).translate(0, 0, t);
let bracket = union(base, wall);
if (filletR > 0 && typeof bracket.fillet === "function") {
  bracket = bracket.fillet(filletR);
}

return [{ name: "Bracket", shape: bracket.color("#5B8DEF") }];
