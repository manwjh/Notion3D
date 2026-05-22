// Open-top box with centered through-hole in the floor
outer_w = 50;
outer_l = 40;
outer_h = 30;
wall = 1.8;
hole_d = 12;
$fn = 48;

difference() {
  cube([outer_w, outer_l, outer_h]);
  translate([wall, wall, wall])
    cube([outer_w - 2 * wall, outer_l - 2 * wall, outer_h - wall + 0.1]);
  translate([outer_w / 2, outer_l / 2, -0.1])
    cylinder(d = hole_d, h = wall + 0.2);
}
