// Open-top rectangular tray
outer_w = 60;
outer_l = 45;
outer_h = 25;
wall = 1.8;

difference() {
  cube([outer_w, outer_l, outer_h]);
  translate([wall, wall, wall])
    cube([outer_w - 2 * wall, outer_l - 2 * wall, outer_h - wall + 0.1]);
}
