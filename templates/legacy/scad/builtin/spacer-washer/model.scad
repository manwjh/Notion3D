// Flat washer / spacer ring
outer_d = 20;
inner_d = 8;
thickness = 2;
$fn = 48;

difference() {
  cylinder(h = thickness, d = outer_d);
  translate([0, 0, -0.1])
    cylinder(h = thickness + 0.2, d = inner_d);
}
