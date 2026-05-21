// Eiffel Tower — FDM-friendly, mm units, no external imports

$fn = 48;
wall = 1.6;

// Overall scale (mm)
h_total = 120;
base_w = 42;

function leg_pos(z, w) = [
    w/2 * (1 - z/h_total * 0.15),
    w/2 * (1 - z/h_total * 0.15)
];

module leg_segment(z0, z1, w0, w1) {
    p0 = leg_pos(z0, w0);
    p1 = leg_pos(z1, w1);
    for (m = [[1,1],[-1,1],[1,-1],[-1,-1]]) {
        hull() {
            translate([p0[0]*m[0], p0[1]*m[1], z0])
                cylinder(h = 0.01, r = wall/2 + 0.4, $fn = 24);
            translate([p1[0]*m[0], p1[1]*m[1], z1])
                cylinder(h = 0.01, r = wall/2 + 0.2, $fn = 24);
        }
    }
}

module cross_brace(z, w, span) {
    r = wall/2 + 0.15;
    for (a = [0, 90]) rotate([0, 0, a])
        hull() {
            translate([span/2, 0, z]) cylinder(h = 0.01, r = r, $fn = 16);
            translate([-span/2, 0, z]) cylinder(h = 0.01, r = r, $fn = 16);
        }
    for (m = [[1,1],[-1,1],[1,-1],[-1,-1]])
        hull() {
            translate([span/2*m[0], span/2*m[1], z])
                cylinder(h = 0.01, r = r, $fn = 16);
            translate([span/2*m[0]*0.55, span/2*m[1]*0.55, z + span*0.35])
                cylinder(h = 0.01, r = r, $fn = 16);
        }
}

module platform(w, t = 2.4) {
    s = w * 0.92;
    difference() {
        linear_extrude(height = t)
            square([s, s], center = true);
        linear_extrude(height = t + 0.2)
            square([s - wall*2.2, s - wall*2.2], center = true);
    }
    linear_extrude(height = t)
        square([s * 0.35, s * 0.35], center = true);
}

module arch(z, w, h_arch) {
    span = w * 0.55;
    difference() {
        hull() {
            for (m = [[1,0],[-1,0]])
                translate([span/2*m[0], 0, z])
                    cylinder(h = h_arch, r = wall + 0.5, $fn = 32);
        }
        translate([0, -span, z - 0.1])
            cube([span*2.2, span*2, h_arch + wall*3]);
    }
}

module middle_taper(z0, z1, w0, w1) {
    steps = 6;
    for (i = [0:steps-1]) {
        z_a = z0 + (z1 - z0) * i / steps;
        z_b = z0 + (z1 - z0) * (i + 1) / steps;
        w_a = w0 + (w1 - w0) * i / steps;
        w_b = w0 + (w1 - w0) * (i + 1) / steps;
        leg_segment(z_a, z_b, w_a, w_b);
        if (i % 2 == 0)
            cross_brace(z_a + (z_b-z_a)*0.5, w_a, w_a * 0.78);
    }
}

module upper_lattice(z0, z1, w) {
    n = 5;
    for (i = [0:n-1]) {
        za = z0 + (z1-z0)*i/n;
        zb = z0 + (z1-z0)*(i+1)/n;
        leg_segment(za, zb, w, w * (1 - 0.12*(i+1)/n));
        cross_brace(za + (zb-za)/2, w, w * 0.55);
    }
}

module spire(z0, h) {
    cylinder(h = h, r1 = wall + 0.6, r2 = 0.4, $fn = 32);
    translate([0, 0, h - 0.01])
        sphere(r = 0.9, $fn = 24);
}

module eiffel_tower() {
    z_base = 3;
    z_leg1 = 22;
    z_plat1 = 28;
    z_leg2 = 48;
    z_plat2 = 54;
    z_leg3 = 78;
    z_plat3 = 84;
    z_top = h_total - 8;

    // Base
    platform(base_w, 3);
    translate([0, 0, z_base])
        platform(base_w * 1.02, 2);

    // Lower legs + arches
    leg_segment(z_base, z_leg1, base_w, base_w * 0.88);
    translate([0, 0, z_base + 2])
        arch(z_base + 4, base_w, 14);
    for (z = [z_base + 8, z_base + 14, z_leg1 - 4])
        cross_brace(z, base_w, base_w * 0.82);

    // First level
    translate([0, 0, z_leg1])
        platform(base_w * 0.72, 2.6);
    middle_taper(z_plat1, z_leg2, base_w * 0.72, base_w * 0.48);

    // Second level
    translate([0, 0, z_leg2])
        platform(base_w * 0.48, 2.2);
    middle_taper(z_plat2, z_leg3, base_w * 0.48, base_w * 0.28);

    // Third level + upper
    translate([0, 0, z_leg3])
        platform(base_w * 0.28, 2);
    upper_lattice(z_plat3, z_top, base_w * 0.22);

    // Observation deck ring
    translate([0, 0, z_top - 2])
        difference() {
            cylinder(h = 2.5, r = base_w * 0.12, $fn = 48);
            translate([0, 0, -0.1])
                cylinder(h = 3, r = base_w * 0.12 - wall, $fn = 48);
        }

    // Spire
    translate([0, 0, z_top])
        spire(0, h_total - z_top);
}

eiffel_tower();
