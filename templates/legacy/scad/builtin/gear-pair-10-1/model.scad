// 10:1 involute spur gear pair — Leemon Baird public domain gear (Thingiverse 5505 / pd-gears)
module_mm = 1.5;
teeth_1 = 10;
teeth_2 = 100;
thickness = 8;
hole_diameter = 5;
pressure_angle = 20;
backlash = 0.08;
clearance = 0.08;
$fn = 48;

mm_per_tooth = module_mm * PI;

module gear (
	mm_per_tooth    = 3,
	number_of_teeth = 11,
	thickness       = 6,
	hole_diameter   = 3,
	twist           = 0,
	teeth_to_hide   = 0,
	pressure_angle  = 28,
	clearance       = 0.0,
	backlash        = 0.0,
    center = false,
    $fn = 20
) {
	p  = mm_per_tooth * number_of_teeth / PI / 2;
	c  = p + mm_per_tooth / PI - clearance;
	b  = p*cos(pressure_angle);
	r  = p-(c-p)-clearance;
	t  = mm_per_tooth/2-backlash/2;
	k  = -iang(b, p) - t/2/p/PI*180;
    difference() {
        linear_extrude(height = thickness, center = center, convexity = 10, twist = twist)
            for (i = [0:(number_of_teeth-teeth_to_hide-1 > 0 ? 1 : -1):number_of_teeth-teeth_to_hide-1] )
                rotate([0,0,i*360/number_of_teeth])
                    polygon(
                        points=[
                            [0, -hole_diameter/10],
                            polar(r, -181/number_of_teeth),
                            polar(r, r<b ? k : -180/number_of_teeth),
                            q7(0/5,r,b,c,k, 1),q7(1/5,r,b,c,k, 1),q7(2/5,r,b,c,k, 1),q7(3/5,r,b,c,k, 1),q7(4/5,r,b,c,k, 1),q7(5/5,r,b,c,k, 1),
                            q7(5/5,r,b,c,k,-1),q7(4/5,r,b,c,k,-1),q7(3/5,r,b,c,k,-1),q7(2/5,r,b,c,k,-1),q7(1/5,r,b,c,k,-1),q7(0/5,r,b,c,k,-1),
                            polar(r, r<b ? -k : 180/number_of_teeth),
                            polar(r, 181/number_of_teeth)
                        ],
                        paths=[[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16]]
                    );
        translate([0,0, (center ? 0 : -0.1)])
            cylinder(h=thickness+0.2, r=hole_diameter/2, center=center, $fn=$fn);
    }
};

function polar(r,theta)   = r*[sin(theta), cos(theta)];
function iang(r1,r2)      = sqrt((r2/r1)*(r2/r1) - 1)/PI*180 - acos(r1/r2);
function q7(f,r,b,r2,t,s) = q6(b,s,t,(1-f)*max(b,r)+f*r2);
function q6(b,s,t,d)      = polar(d,s*(iang(b,d)+t));
function pitch_radius(mm_per_tooth=3,number_of_teeth=11) = mm_per_tooth * number_of_teeth / PI / 2;

center_distance = pitch_radius(mm_per_tooth, teeth_1) + pitch_radius(mm_per_tooth, teeth_2);

gear(
  mm_per_tooth,
  teeth_1,
  thickness,
  hole_diameter,
  0,
  0,
  pressure_angle,
  clearance,
  backlash,
  false,
  $fn
);

translate([center_distance, 0, 0])
  rotate([0, 0, (-teeth_2 / 4 + teeth_1 / 4 + 1 / 2) * 360 / teeth_2])
    gear(
      mm_per_tooth,
      teeth_2,
      thickness,
      hole_diameter,
      0,
      0,
      pressure_angle,
      clearance,
      backlash,
      false,
      $fn
    );
