// Phone stand — tilt + charging notch + cable groove + pad recesses
wall     = 2.0;
tilt_deg = 15;
slot_w   = 84;
slot_d   = 14;
lip_h    = 12;
back_h   = 95;
base_d   = 62;
base_w   = slot_w + 2 * wall;
brace_h  = 32;
port_w   = 28;
port_h   = 16;
cable_w  = 8;
cable_d  = 3;
pad_s    = 18;
pad_r    = 1.2;
$fn      = 48;

module inclined_trough() {
  union() {
    cube([base_w, wall, back_h]);
    cube([wall, slot_d + wall, back_h]);
    translate([base_w - wall, 0, 0])
      cube([wall, slot_d + wall, back_h]);
    translate([0, slot_d, 0])
      cube([base_w, wall, lip_h]);
  }
}

module side_brace(x) {
  run = brace_h * tan(tilt_deg);
  translate([x, base_d - wall - run, wall])
    linear_extrude(height = wall)
    polygon([[0, 0], [run, 0], [0, brace_h]]);
}

module charging_notch() {
  translate([base_w / 2 - port_w / 2, slot_d - 1, -0.5])
    cube([port_w, wall + 3, port_h + lip_h + 0.5]);
}

module finger_relief() {
  rw = 22;
  translate([base_w / 2 - rw / 2, slot_d + wall - 0.5, -0.5])
    cube([rw, 2.5, lip_h * 0.55]);
}

module cable_groove() {
  translate([base_w / 2 - cable_w / 2, base_d * 0.15, wall - cable_d + 0.01])
    cube([cable_w, base_d * 0.72, cable_d + 0.1]);
}

module pad_recess(x, y) {
  translate([x, y, -0.01])
    cube([pad_s, pad_s, pad_r + 0.02]);
}

difference() {
  union() {
    cube([base_w, base_d, wall]);
    translate([0, base_d - wall, wall])
      rotate([-tilt_deg, 0, 0])
      inclined_trough();
    side_brace(wall);
    side_brace(base_w - 2 * wall);
  }
  cable_groove();
  translate([0, base_d - wall, wall])
    rotate([-tilt_deg, 0, 0]) {
    charging_notch();
    finger_relief();
  }
  pad_recess(wall + 4, wall + 4);
  pad_recess(base_w - pad_s - wall - 4, wall + 4);
  pad_recess(wall + 4, base_d - pad_s - wall - 4);
  pad_recess(base_w - pad_s - wall - 4, base_d - pad_s - wall - 4);
}
