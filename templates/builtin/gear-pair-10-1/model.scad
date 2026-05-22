// 10:1 spur gear pair — involute profile, meshed layout
module_mm = 1.5;
teeth_1 = 10;
teeth_2 = 100;
thickness = 8;
bore_d = 5;
hub_d = 14;
hub_h = 5;
pressure_angle = 20;
backlash = 0.08;
$fn = 48;

center_distance = module_mm * (teeth_1 + teeth_2) / 2;

function involute_pt(r_base, t) = [
  r_base * (cos(t) + t * sin(t)),
  r_base * (sin(t) - t * cos(t))
];

module tooth_space_2d(z) {
  m = module_mm;
  pa = pressure_angle;
  r_pitch = m * z / 2;
  r_base = r_pitch * cos(pa);
  r_outer = r_pitch + m;
  r_root = max(m * 0.8, r_pitch - 1.25 * m - backlash / 2);
  t_outer = sqrt(pow(r_outer / r_base, 2) - 1);
  t_root = sqrt(pow(max(r_root, r_base + 0.01) / r_base, 2) - 1);
  n = 10;
  half_angle = 360 / z / 4;
  flank = [
    for (i = [0:n])
      let(t = t_root + (t_outer - t_root) * i / n)
      involute_pt(r_base, t)
  ];
  root_pt = [r_root * cos(-half_angle), r_root * sin(-half_angle)];
  poly = concat(
    [root_pt],
    flank,
    [for (p = flank) [p[0], -p[1]]],
    [[r_root * cos(half_angle), r_root * sin(half_angle)]]
  );
  polygon(points = poly);
}

module gear_blank_2d(z) {
  m = module_mm;
  pa = pressure_angle;
  r_pitch = m * z / 2;
  r_root = max(m * 0.8, r_pitch - 1.25 * m - backlash / 2);
  union() {
    circle(r = r_root, $fn = z * 6);
    for (i = [0:z - 1])
      rotate([0, 0, i * 360 / z])
        tooth_space_2d(z);
  }
}

module spur_gear(z) {
  difference() {
    union() {
      linear_extrude(height = thickness)
        gear_blank_2d(z);
      if (hub_d > bore_d)
        cylinder(d = hub_d, h = hub_h, $fn = 48);
    }
    translate([0, 0, -0.5])
      cylinder(d = bore_d, h = thickness + hub_h + 1, $fn = 48);
  }
}

spur_gear(teeth_1);

translate([center_distance, 0, 0])
  rotate([0, 0, 180 / teeth_2])
    spur_gear(teeth_2);
