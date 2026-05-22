// SD card tray — shallow pocket + front finger notch
card_w = 32.4;
card_l = 24.4;
card_t = 2.3;
wall = 1.6;
clearance_top = 1;
finger_w = 14;
finger_depth = 8;
$fn = 32;

inner_w = card_w + 0.4;
inner_l = card_l + 0.4;
outer_w = inner_w + 2 * wall;
outer_l = inner_l + 2 * wall;
outer_h = card_t + wall + clearance_top;

difference() {
  cube([outer_w, outer_l, outer_h]);
  translate([wall, wall, wall])
    cube([inner_w, inner_l, card_t + 0.5]);
  translate([(outer_w - finger_w) / 2, -0.1, wall])
    cube([finger_w, finger_depth + wall, card_t + 0.5]);
}
