// Wall hook — back plate + L-shaped hook arm
hook_w = 18;
hook_d = 22;
wall = 2.0;
back_h = 35;
back_w = 28;
lip_h = 8;
$fn = 32;

module hook_arm() {
  union() {
    cube([hook_w, hook_d, wall]);
    translate([0, hook_d - wall, 0])
      cube([hook_w, wall, lip_h]);
  }
}

union() {
  cube([back_w, wall, back_h]);
  translate([(back_w - hook_w) / 2, wall, back_h - wall - lip_h])
    hook_arm();
}
