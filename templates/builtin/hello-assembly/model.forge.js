// Hello assembly — Notion3D ForgeCAD starter template
const bodyW = param("Body Width", 36, { min: 24, max: 60, unit: "mm" });
const bodyH = param("Body Height", 90, { min: 60, max: 140, unit: "mm" });
const shellT = param("Shell Thickness", 1.8, { min: 1.2, max: 3, unit: "mm" });

const outer = cylinder(bodyH, bodyW / 2, bodyW / 2, 24, true).color("#BDC3C7");
const inner = cylinder(bodyH + 2, bodyW / 2 - shellT, bodyW / 2 - shellT, 24, true);
const shell = outer.subtract(inner).color("#95A5A6");

const motor = cylinder(28, 14, 14, 24, true)
  .translate(0, 0, -8)
  .color("#7F8C8D");

const battery = box(18, 18, 48, true)
  .translate(0, 0, -24)
  .color("#3498DB");

const pcb = box(10, 28, 2, true)
  .translate(bodyW / 2 - 6, 0, 10)
  .color("#27AE60");

const coil = cylinder(4, 22, 22, 24, true)
  .translate(0, 0, -bodyH / 2 + 6)
  .color("#E67E22");

return [
  { name: "Shell", shape: shell },
  { name: "Motor", shape: motor },
  { name: "Battery", shape: battery },
  { name: "PCB", shape: pcb },
  { name: "Charging Coil", shape: coil },
];
