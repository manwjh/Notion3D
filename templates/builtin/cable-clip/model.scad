// Snap cable clip — C-groove + adhesive base pad
cable_d = 5;
wall = 1.8;
length = 12;
slot_w = 2.4;
base_pad = 3;
base_h = 2;
$fn = 48;

r_outer = cable_d / 2 + wall;

difference() {
  union() {
    translate([0, 0, base_h])
      cylinder(h = length - base_h, r = r_outer);
    translate([-r_outer - base_pad, -r_outer - base_pad, 0])
      cube([2 * (r_outer + base_pad), 2 * (r_outer + base_pad), base_h]);
  }
  translate([0, 0, base_h - 0.1])
    cylinder(h = length - base_h + 0.2, r = cable_d / 2 + 0.15);
  translate([-r_outer - 0.1, -slot_w / 2, base_h - 0.1])
    cube([2 * r_outer + 0.2, slot_w, length - base_h + 0.2]);
}
