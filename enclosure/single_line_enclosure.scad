// 忘却炉 筐体 — 立方体 / 一本線 / 底面アルミ露出 / 背面配線
// 設計判断は enclosure/筐体は一本線と底面アルミ露出で構成し配線は線の反対面から出す.md を参照。
//
// 寸法はすべて仮置きである。一辺は安全層基板95×72mmが入る最小に近い値から取った初期値で、
// 確定値ではない。side を変えれば線・勘合・ボスの位置がすべて追従する。
//
// レンダリング例:
//   openscad -o iso.png --imgsize=1600,1200 --projection=p --colorscheme=DeepOcean \
//            --autocenter --viewall --camera=0,0,0,62,0,28,0 -D 'view="assembled"' single_line_enclosure.scad
//   view = "assembled" | "exploded" | "bottom" | "back" | "lid" | "base"
//   STL書き出し:  openscad -o lid.stl -D 'view="lid"' single_line_enclosure.scad

view = "assembled";
$fn  = 72;

/* ---------- 外形（立方体・仮置き） ---------- */
side = 108;   // 一辺。内寸102mmに安全層基板95×72mmが収まる
wall = 3;     // 壁厚
r_f  = 8;     // 稜の丸め半径

ox = side; oy = side; oz = side;
inner_x = side - 2*wall;
inner_y = side - 2*wall;
inner_z = side - 2*wall;

/* ---------- 一本線 ---------- */
// 天面の途中(y=line_start_y)から始まり、前稜を越え、正面(-Y)を垂直に下り、底面で終わる。
// 線は x = line_x の1平面内に収まる。左右非対称に置くことで箱に向きを与える。
line_x       = -ox/2 + 34;
line_w       = 2.4;    // 溝幅
line_d       = 1.8;    // 溝深さ
line_recess  = 0.4;    // 拡散材を表面より沈める量
line_start_y = 8;      // 天面上の始点（+Yが背面側）
line_clr     = 0.15;   // 拡散材の幅方向クリアランス

/* ---------- 蓋と器 ---------- */
lid_h       = 36;   // 蓋の高さ（天面 + スカート）。分割線は z = oz - lid_h
part_clr    = 0.2;  // 勘合クリアランス
post_d      = 9;    // 蓋側ポスト外径
post_inset  = 12;   // 角からの寄せ
post_drop   = 15;   // 蓋側ポストが分割線より下へ伸びる長さ
screw_d     = 3.2;  // ねじ通し穴（底面から挿す）
screw_head  = 6.4;  // 座ぐり径
screw_cbore = 2.5;  // 座ぐり深さ
screw_pilot = 2.5;  // 蓋側の下穴

z_part = oz - lid_h;            // 分割線の高さ
z_meet = z_part - post_drop;    // 蓋ポストと器ボスが出会う高さ
boss_h = z_meet - wall;         // 器側ボス（柱）の高さ

/* ---------- アルミ接触板 ---------- */
plate_x  = 40;
plate_y  = 35;
plate_t  = 0.3;
plate_lip= 2.5;    // 板を受けるリップ幅（この分だけ窓が板より小さい）

/* ---------- 背面の開口（+Y面） ---------- */
dc_d = 8;   dc_x = -26;  dc_z = 20;
usb_w= 13;  usb_h = 7;   usb_x = 18;  usb_z = 20;

/* ---------- 色 ---------- */
c_body  = [0.085, 0.085, 0.095];
c_line  = [1.00, 0.55, 0.22];
c_alu   = [0.78, 0.79, 0.81];

/* =========================================================
   基本モジュール
   ========================================================= */

// 全稜が半径rで丸いボックス（底面がz=0）
module rbox(x, y, z, r) {
  translate([0, 0, z/2])
    hull() for (ix = [-1, 1], iy = [-1, 1], iz = [-1, 1])
      translate([ix*(x/2 - r), iy*(y/2 - r), iz*(z/2 - r)]) sphere(r);
}

module box2(x1, x2, y1, y2, z1, z2) {
  translate([x1, y1, z1]) cube([x2 - x1, y2 - y1, z2 - z1]);
}

// 一本線の帯。out = 表面から外へのはみ出し（負なら沈める）、dep = 表面からの深さ、w = 幅
module line_geom(out, dep, w) {
  yf  = -oy/2;        // 正面の外表面
  cy  = yf + r_f;     // 前稜の中心（Y）
  czt = oz - r_f;     // 上側前稜の中心（Z）
  czb = r_f;          // 下側前稜の中心（Z）

  // 天面区間
  box2(line_x - w/2, line_x + w/2, cy, line_start_y, oz - dep, oz + out);

  // 上側前稜（1/4円弧）
  intersection() {
    translate([line_x - w/2, cy, czt]) rotate([0, 90, 0])
      difference() {
        cylinder(h = w, r = r_f + out);
        translate([0, 0, -1]) cylinder(h = w + 2, r = r_f - dep);
      }
    box2(line_x - w, line_x + w, cy - r_f - 2, cy, czt, czt + r_f + 2);
  }

  // 正面の垂直区間
  box2(line_x - w/2, line_x + w/2, yf - out, yf + dep, czb, czt);

  // 下側前稜（1/4円弧）— ここで線は底面に抜けて終わる
  intersection() {
    translate([line_x - w/2, cy, czb]) rotate([0, 90, 0])
      difference() {
        cylinder(h = w, r = r_f + out);
        translate([0, 0, -1]) cylinder(h = w + 2, r = r_f - dep);
      }
    box2(line_x - w, line_x + w, cy - r_f - 2, cy, czb - r_f - 2, czb);
  }
}

module at_corners(inset) {
  for (ix = [-1, 1], iy = [-1, 1])
    translate([ix*(ox/2 - inset), iy*(oy/2 - inset), 0]) children();
}

/* =========================================================
   筐体本体（蓋と器に切り分ける前の一体形状）
   ========================================================= */

module shell() {
  difference() {
    rbox(ox, oy, oz, r_f);
    // 内部空洞
    translate([0, 0, wall]) rbox(inner_x, inner_y, inner_z, 3);
    // 一本線の溝
    line_geom(1, line_d, line_w);
    // 底面：アルミ板のポケット（外側から落とし込み、面一）と接触窓
    translate([0, 0, -0.01])
      rbox(plate_x + 0.4, plate_y + 0.4, plate_t + 0.11, 1);
    translate([0, 0, -1])
      rbox(plate_x - 2*plate_lip, plate_y - 2*plate_lip, wall + 2, 2);
    // 背面の開口
    translate([dc_x, oy/2 - wall - 1, dc_z]) rotate([-90, 0, 0])
      cylinder(h = wall + 2, d = dc_d);
    translate([usb_x - usb_w/2, oy/2 - wall - 1, usb_z])
      cube([usb_w, wall + 2, usb_h]);
  }
}

module lid() {
  color(c_body)
  difference() {
    union() {
      intersection() {
        shell();
        box2(-ox, ox, -oy, oy, z_part + part_clr/2, oz + 1);
      }
      // 位置決めポスト（分割線を跨いで器側の柱まで届く）
      at_corners(post_inset)
        translate([0, 0, z_meet]) cylinder(h = oz - wall - z_meet, d = post_d);
    }
    // ねじの下穴
    at_corners(post_inset)
      translate([0, 0, z_meet - 1]) cylinder(h = 16, d = screw_pilot);
  }
}

module base() {
  color(c_body)
  difference() {
    union() {
      intersection() {
        shell();
        box2(-ox, ox, -oy, oy, -1, z_part - part_clr/2);
      }
      // 器側の柱（蓋ポストの受け。基板の支柱も兼ねる）
      at_corners(post_inset)
        translate([0, 0, wall]) cylinder(h = boss_h, d = post_d + 3);
    }
    // ポストの受け穴
    at_corners(post_inset)
      translate([0, 0, z_meet - 6]) cylinder(h = 6.1, d = post_d + 0.3);
    // ねじは底面から挿し、頭は座ぐりに沈める（外周4面と天面には穴がない）
    at_corners(post_inset) {
      translate([0, 0, -1]) cylinder(h = z_meet + 1, d = screw_d);
      translate([0, 0, -0.01]) cylinder(h = screw_cbore, d = screw_head);
    }
  }
}

// 拡散材（一本線そのもの）
module light_line() {
  color(c_line) line_geom(-line_recess, line_d, line_w - 2*line_clr);
}

// アルミ接触板
module plate() {
  color(c_alu) rbox(plate_x, plate_y, plate_t, 1);
}

/* =========================================================
   ビュー
   ========================================================= */

module assembled() { base(); lid(); light_line(); plate(); }

module exploded() {
  ex = 62;
  base(); plate();
  translate([0, 0, ex]) lid();
  intersection() { light_line(); box2(-ox, ox, -oy, oy, -1, z_part); }
  translate([0, 0, ex])
    intersection() { light_line(); box2(-ox, ox, -oy, oy, z_part, oz + 1); }
}

if      (view == "assembled") assembled();
else if (view == "exploded")  exploded();
else if (view == "bottom")    assembled();
else if (view == "back")      assembled();
else if (view == "lid")       lid();
else if (view == "base")      base();
else                          assembled();
