`timescale 1ns/1ps
// 自动生成数据 + 成对改造，请勿手改。
//   LUT 常量来源：build/generated/pl_synth_offload/cpu_breakdown/gen_exp_vectors.py
//   （按 PL-EXP-20261022 任务约定该脚本保持只读，未改动；成对改造见
//    report/pl_expunit_fix_20261022.json 的 rom_postprocess 字段）
// 复数 exp 单元 ROM：
//   EXP  256x36 成对存储 {e_{i+1}, e_i}（Q2.16, e^(i*ln2/256)），一次地址读出 lo/hi；
//        e_256 = 2*e_0 = 131072（与定点模型 IDX==255 时的 HI 一致）
//   COS/SIN 1024x36 打包 {sin, cos}（Q1.17，cos(0)=131071 已钳位）
module minphase_rom_1024 (
    input  wire        clk,
    input  wire [8:0]  exp_addr,   // 只用 [7:0]，成对表按 idx 寻址
    output reg  [17:0] exp_lo,     // e_idx
    output reg  [17:0] exp_hi,     // e_{idx+1}
    input  wire [9:0]  ang_addr,
    output wire signed [17:0] cos_q,
    output wire signed [17:0] sin_q
);
    (* rom_style = "block" *) reg [35:0] exp_pair [0:255];
    (* rom_style = "block" *) reg [35:0] ang_rom [0:1023];
    initial begin
        exp_pair[  0] = 36'h402c90000;  // {e_1, e_0} = {65714, 65536}
        exp_pair[  1] = 36'h4059100b2;  // {e_2, e_1} = {65892, 65714}
        exp_pair[  2] = 36'h4085d0164;  // {e_3, e_2} = {66071, 65892}
        exp_pair[  3] = 36'h40b290217;  // {e_4, e_3} = {66250, 66071}
        exp_pair[  4] = 36'h40df502ca;  // {e_5, e_4} = {66429, 66250}
        exp_pair[  5] = 36'h410c5037d;  // {e_6, e_5} = {66609, 66429}
        exp_pair[  6] = 36'h413990431;  // {e_7, e_6} = {66790, 66609}
        exp_pair[  7] = 36'h4166d04e6;  // {e_8, e_7} = {66971, 66790}
        exp_pair[  8] = 36'h41945059b;  // {e_9, e_8} = {67153, 66971}
        exp_pair[  9] = 36'h41c1d0651;  // {e_10, e_9} = {67335, 67153}
        exp_pair[ 10] = 36'h41ef50707;  // {e_11, e_10} = {67517, 67335}
        exp_pair[ 11] = 36'h421d107bd;  // {e_12, e_11} = {67700, 67517}
        exp_pair[ 12] = 36'h424b10874;  // {e_13, e_12} = {67884, 67700}
        exp_pair[ 13] = 36'h42791092c;  // {e_14, e_13} = {68068, 67884}
        exp_pair[ 14] = 36'h42a7109e4;  // {e_15, e_14} = {68252, 68068}
        exp_pair[ 15] = 36'h42d590a9c;  // {e_16, e_15} = {68438, 68252}
        exp_pair[ 16] = 36'h4303d0b56;  // {e_17, e_16} = {68623, 68438}
        exp_pair[ 17] = 36'h433250c0f;  // {e_18, e_17} = {68809, 68623}
        exp_pair[ 18] = 36'h436110cc9;  // {e_19, e_18} = {68996, 68809}
        exp_pair[ 19] = 36'h438fd0d84;  // {e_20, e_19} = {69183, 68996}
        exp_pair[ 20] = 36'h43be90e3f;  // {e_21, e_20} = {69370, 69183}
        exp_pair[ 21] = 36'h43ed90efa;  // {e_22, e_21} = {69558, 69370}
        exp_pair[ 22] = 36'h441cd0fb6;  // {e_23, e_22} = {69747, 69558}
        exp_pair[ 23] = 36'h444c11073;  // {e_24, e_23} = {69936, 69747}
        exp_pair[ 24] = 36'h447b91130;  // {e_25, e_24} = {70126, 69936}
        exp_pair[ 25] = 36'h44ab111ee;  // {e_26, e_25} = {70316, 70126}
        exp_pair[ 26] = 36'h44dad12ac;  // {e_27, e_26} = {70507, 70316}
        exp_pair[ 27] = 36'h450a9136b;  // {e_28, e_27} = {70698, 70507}
        exp_pair[ 28] = 36'h453a5142a;  // {e_29, e_28} = {70889, 70698}
        exp_pair[ 29] = 36'h456a914e9;  // {e_30, e_29} = {71082, 70889}
        exp_pair[ 30] = 36'h459a915aa;  // {e_31, e_30} = {71274, 71082}
        exp_pair[ 31] = 36'h45cb1166a;  // {e_32, e_31} = {71468, 71274}
        exp_pair[ 32] = 36'h45fb5172c;  // {e_33, e_32} = {71661, 71468}
        exp_pair[ 33] = 36'h462c117ed;  // {e_34, e_33} = {71856, 71661}
        exp_pair[ 34] = 36'h465c918b0;  // {e_35, e_34} = {72050, 71856}
        exp_pair[ 35] = 36'h468d91972;  // {e_36, e_35} = {72246, 72050}
        exp_pair[ 36] = 36'h46be91a36;  // {e_37, e_36} = {72442, 72246}
        exp_pair[ 37] = 36'h46ef91afa;  // {e_38, e_37} = {72638, 72442}
        exp_pair[ 38] = 36'h4720d1bbe;  // {e_39, e_38} = {72835, 72638}
        exp_pair[ 39] = 36'h475211c83;  // {e_40, e_39} = {73032, 72835}
        exp_pair[ 40] = 36'h478391d48;  // {e_41, e_40} = {73230, 73032}
        exp_pair[ 41] = 36'h47b551e0e;  // {e_42, e_41} = {73429, 73230}
        exp_pair[ 42] = 36'h47e711ed5;  // {e_43, e_42} = {73628, 73429}
        exp_pair[ 43] = 36'h481911f9c;  // {e_44, e_43} = {73828, 73628}
        exp_pair[ 44] = 36'h484b12064;  // {e_45, e_44} = {74028, 73828}
        exp_pair[ 45] = 36'h487d5212c;  // {e_46, e_45} = {74229, 74028}
        exp_pair[ 46] = 36'h48af921f5;  // {e_47, e_46} = {74430, 74229}
        exp_pair[ 47] = 36'h48e2122be;  // {e_48, e_47} = {74632, 74430}
        exp_pair[ 48] = 36'h491492388;  // {e_49, e_48} = {74834, 74632}
        exp_pair[ 49] = 36'h494752452;  // {e_50, e_49} = {75037, 74834}
        exp_pair[ 50] = 36'h497a1251d;  // {e_51, e_50} = {75240, 75037}
        exp_pair[ 51] = 36'h49ad125e8;  // {e_52, e_51} = {75444, 75240}
        exp_pair[ 52] = 36'h49e0526b4;  // {e_53, e_52} = {75649, 75444}
        exp_pair[ 53] = 36'h4a1392781;  // {e_54, e_53} = {75854, 75649}
        exp_pair[ 54] = 36'h4a471284e;  // {e_55, e_54} = {76060, 75854}
        exp_pair[ 55] = 36'h4a7a9291c;  // {e_56, e_55} = {76266, 76060}
        exp_pair[ 56] = 36'h4aae529ea;  // {e_57, e_56} = {76473, 76266}
        exp_pair[ 57] = 36'h4ae212ab9;  // {e_58, e_57} = {76680, 76473}
        exp_pair[ 58] = 36'h4b1612b88;  // {e_59, e_58} = {76888, 76680}
        exp_pair[ 59] = 36'h4b4a12c58;  // {e_60, e_59} = {77096, 76888}
        exp_pair[ 60] = 36'h4b7e52d28;  // {e_61, e_60} = {77305, 77096}
        exp_pair[ 61] = 36'h4bb2d2df9;  // {e_62, e_61} = {77515, 77305}
        exp_pair[ 62] = 36'h4be752ecb;  // {e_63, e_62} = {77725, 77515}
        exp_pair[ 63] = 36'h4c1c12f9d;  // {e_64, e_63} = {77936, 77725}
        exp_pair[ 64] = 36'h4c50d3070;  // {e_65, e_64} = {78147, 77936}
        exp_pair[ 65] = 36'h4c85d3143;  // {e_66, e_65} = {78359, 78147}
        exp_pair[ 66] = 36'h4cbb13217;  // {e_67, e_66} = {78572, 78359}
        exp_pair[ 67] = 36'h4cf0532ec;  // {e_68, e_67} = {78785, 78572}
        exp_pair[ 68] = 36'h4d25933c1;  // {e_69, e_68} = {78998, 78785}
        exp_pair[ 69] = 36'h4d5b13496;  // {e_70, e_69} = {79212, 78998}
        exp_pair[ 70] = 36'h4d90d356c;  // {e_71, e_70} = {79427, 79212}
        exp_pair[ 71] = 36'h4dc693643;  // {e_72, e_71} = {79642, 79427}
        exp_pair[ 72] = 36'h4dfc9371a;  // {e_73, e_72} = {79858, 79642}
        exp_pair[ 73] = 36'h4e32d37f2;  // {e_74, e_73} = {80075, 79858}
        exp_pair[ 74] = 36'h4e69138cb;  // {e_75, e_74} = {80292, 80075}
        exp_pair[ 75] = 36'h4e9f939a4;  // {e_76, e_75} = {80510, 80292}
        exp_pair[ 76] = 36'h4ed613a7e;  // {e_77, e_76} = {80728, 80510}
        exp_pair[ 77] = 36'h4f0cd3b58;  // {e_78, e_77} = {80947, 80728}
        exp_pair[ 78] = 36'h4f4393c33;  // {e_79, e_78} = {81166, 80947}
        exp_pair[ 79] = 36'h4f7a93d0e;  // {e_80, e_79} = {81386, 81166}
        exp_pair[ 80] = 36'h4fb1d3dea;  // {e_81, e_80} = {81607, 81386}
        exp_pair[ 81] = 36'h4fe913ec7;  // {e_82, e_81} = {81828, 81607}
        exp_pair[ 82] = 36'h502093fa4;  // {e_83, e_82} = {82050, 81828}
        exp_pair[ 83] = 36'h505854082;  // {e_84, e_83} = {82273, 82050}
        exp_pair[ 84] = 36'h509014161;  // {e_85, e_84} = {82496, 82273}
        exp_pair[ 85] = 36'h50c7d4240;  // {e_86, e_85} = {82719, 82496}
        exp_pair[ 86] = 36'h51001431f;  // {e_87, e_86} = {82944, 82719}
        exp_pair[ 87] = 36'h513854400;  // {e_88, e_87} = {83169, 82944}
        exp_pair[ 88] = 36'h5170944e1;  // {e_89, e_88} = {83394, 83169}
        exp_pair[ 89] = 36'h51a9145c2;  // {e_90, e_89} = {83620, 83394}
        exp_pair[ 90] = 36'h51e1d46a4;  // {e_91, e_90} = {83847, 83620}
        exp_pair[ 91] = 36'h521a94787;  // {e_92, e_91} = {84074, 83847}
        exp_pair[ 92] = 36'h52539486a;  // {e_93, e_92} = {84302, 84074}
        exp_pair[ 93] = 36'h528cd494e;  // {e_94, e_93} = {84531, 84302}
        exp_pair[ 94] = 36'h52c614a33;  // {e_95, e_94} = {84760, 84531}
        exp_pair[ 95] = 36'h52ff94b18;  // {e_96, e_95} = {84990, 84760}
        exp_pair[ 96] = 36'h533914bfe;  // {e_97, e_96} = {85220, 84990}
        exp_pair[ 97] = 36'h5372d4ce4;  // {e_98, e_97} = {85451, 85220}
        exp_pair[ 98] = 36'h53acd4dcb;  // {e_99, e_98} = {85683, 85451}
        exp_pair[ 99] = 36'h53e6d4eb3;  // {e_100, e_99} = {85915, 85683}
        exp_pair[100] = 36'h542114f9b;  // {e_101, e_100} = {86148, 85915}
        exp_pair[101] = 36'h545b95084;  // {e_102, e_101} = {86382, 86148}
        exp_pair[102] = 36'h54961516e;  // {e_103, e_102} = {86616, 86382}
        exp_pair[103] = 36'h54d0d5258;  // {e_104, e_103} = {86851, 86616}
        exp_pair[104] = 36'h550b95343;  // {e_105, e_104} = {87086, 86851}
        exp_pair[105] = 36'h55469542e;  // {e_106, e_105} = {87322, 87086}
        exp_pair[106] = 36'h5581d551a;  // {e_107, e_106} = {87559, 87322}
        exp_pair[107] = 36'h55bd15607;  // {e_108, e_107} = {87796, 87559}
        exp_pair[108] = 36'h55f8956f4;  // {e_109, e_108} = {88034, 87796}
        exp_pair[109] = 36'h5634557e2;  // {e_110, e_109} = {88273, 88034}
        exp_pair[110] = 36'h5670558d1;  // {e_111, e_110} = {88513, 88273}
        exp_pair[111] = 36'h56ac159c1;  // {e_112, e_111} = {88752, 88513}
        exp_pair[112] = 36'h56e855ab0;  // {e_113, e_112} = {88993, 88752}
        exp_pair[113] = 36'h572495ba1;  // {e_114, e_113} = {89234, 88993}
        exp_pair[114] = 36'h576115c92;  // {e_115, e_114} = {89476, 89234}
        exp_pair[115] = 36'h579dd5d84;  // {e_116, e_115} = {89719, 89476}
        exp_pair[116] = 36'h57da95e77;  // {e_117, e_116} = {89962, 89719}
        exp_pair[117] = 36'h581795f6a;  // {e_118, e_117} = {90206, 89962}
        exp_pair[118] = 36'h5854d605e;  // {e_119, e_118} = {90451, 90206}
        exp_pair[119] = 36'h589216153;  // {e_120, e_119} = {90696, 90451}
        exp_pair[120] = 36'h58cf96248;  // {e_121, e_120} = {90942, 90696}
        exp_pair[121] = 36'h590d1633e;  // {e_122, e_121} = {91188, 90942}
        exp_pair[122] = 36'h594b16434;  // {e_123, e_122} = {91436, 91188}
        exp_pair[123] = 36'h59891652c;  // {e_124, e_123} = {91684, 91436}
        exp_pair[124] = 36'h59c716624;  // {e_125, e_124} = {91932, 91684}
        exp_pair[125] = 36'h5a055671c;  // {e_126, e_125} = {92181, 91932}
        exp_pair[126] = 36'h5a43d6815;  // {e_127, e_126} = {92431, 92181}
        exp_pair[127] = 36'h5a829690f;  // {e_128, e_127} = {92682, 92431}
        exp_pair[128] = 36'h5ac156a0a;  // {e_129, e_128} = {92933, 92682}
        exp_pair[129] = 36'h5b0056b05;  // {e_130, e_129} = {93185, 92933}
        exp_pair[130] = 36'h5b3f96c01;  // {e_131, e_130} = {93438, 93185}
        exp_pair[131] = 36'h5b7ed6cfe;  // {e_132, e_131} = {93691, 93438}
        exp_pair[132] = 36'h5bbe56dfb;  // {e_133, e_132} = {93945, 93691}
        exp_pair[133] = 36'h5bfe16ef9;  // {e_134, e_133} = {94200, 93945}
        exp_pair[134] = 36'h5c3dd6ff8;  // {e_135, e_134} = {94455, 94200}
        exp_pair[135] = 36'h5c7dd70f7;  // {e_136, e_135} = {94711, 94455}
        exp_pair[136] = 36'h5cbe171f7;  // {e_137, e_136} = {94968, 94711}
        exp_pair[137] = 36'h5cfe972f8;  // {e_138, e_137} = {95226, 94968}
        exp_pair[138] = 36'h5d3f173fa;  // {e_139, e_138} = {95484, 95226}
        exp_pair[139] = 36'h5d7fd74fc;  // {e_140, e_139} = {95743, 95484}
        exp_pair[140] = 36'h5dc0975ff;  // {e_141, e_140} = {96002, 95743}
        exp_pair[141] = 36'h5e01d7702;  // {e_142, e_141} = {96263, 96002}
        exp_pair[142] = 36'h5e4317807;  // {e_143, e_142} = {96524, 96263}
        exp_pair[143] = 36'h5e845790c;  // {e_144, e_143} = {96785, 96524}
        exp_pair[144] = 36'h5ec617a11;  // {e_145, e_144} = {97048, 96785}
        exp_pair[145] = 36'h5f07d7b18;  // {e_146, e_145} = {97311, 97048}
        exp_pair[146] = 36'h5f49d7c1f;  // {e_147, e_146} = {97575, 97311}
        exp_pair[147] = 36'h5f8bd7d27;  // {e_148, e_147} = {97839, 97575}
        exp_pair[148] = 36'h5fce17e2f;  // {e_149, e_148} = {98104, 97839}
        exp_pair[149] = 36'h601097f38;  // {e_150, e_149} = {98370, 98104}
        exp_pair[150] = 36'h605358042;  // {e_151, e_150} = {98637, 98370}
        exp_pair[151] = 36'h60965814d;  // {e_152, e_151} = {98905, 98637}
        exp_pair[152] = 36'h60d958259;  // {e_153, e_152} = {99173, 98905}
        exp_pair[153] = 36'h611c98365;  // {e_154, e_153} = {99442, 99173}
        exp_pair[154] = 36'h615fd8472;  // {e_155, e_154} = {99711, 99442}
        exp_pair[155] = 36'h61a39857f;  // {e_156, e_155} = {99982, 99711}
        exp_pair[156] = 36'h61e75868e;  // {e_157, e_156} = {100253, 99982}
        exp_pair[157] = 36'h622b1879d;  // {e_158, e_157} = {100524, 100253}
        exp_pair[158] = 36'h626f588ac;  // {e_159, e_158} = {100797, 100524}
        exp_pair[159] = 36'h62b3989bd;  // {e_160, e_159} = {101070, 100797}
        exp_pair[160] = 36'h62f818ace;  // {e_161, e_160} = {101344, 101070}
        exp_pair[161] = 36'h633cd8be0;  // {e_162, e_161} = {101619, 101344}
        exp_pair[162] = 36'h6381d8cf3;  // {e_163, e_162} = {101895, 101619}
        exp_pair[163] = 36'h63c6d8e07;  // {e_164, e_163} = {102171, 101895}
        exp_pair[164] = 36'h640c18f1b;  // {e_165, e_164} = {102448, 102171}
        exp_pair[165] = 36'h645199030;  // {e_166, e_165} = {102726, 102448}
        exp_pair[166] = 36'h649719146;  // {e_167, e_166} = {103004, 102726}
        exp_pair[167] = 36'h64dcd925c;  // {e_168, e_167} = {103283, 103004}
        exp_pair[168] = 36'h652319373;  // {e_169, e_168} = {103564, 103283}
        exp_pair[169] = 36'h65691948c;  // {e_170, e_169} = {103844, 103564}
        exp_pair[170] = 36'h65af995a4;  // {e_171, e_170} = {104126, 103844}
        exp_pair[171] = 36'h65f6196be;  // {e_172, e_171} = {104408, 104126}
        exp_pair[172] = 36'h663cd97d8;  // {e_173, e_172} = {104691, 104408}
        exp_pair[173] = 36'h6683d98f3;  // {e_174, e_173} = {104975, 104691}
        exp_pair[174] = 36'h66cb19a0f;  // {e_175, e_174} = {105260, 104975}
        exp_pair[175] = 36'h671259b2c;  // {e_176, e_175} = {105545, 105260}
        exp_pair[176] = 36'h6759d9c49;  // {e_177, e_176} = {105831, 105545}
        exp_pair[177] = 36'h67a199d67;  // {e_178, e_177} = {106118, 105831}
        exp_pair[178] = 36'h67e999e86;  // {e_179, e_178} = {106406, 106118}
        exp_pair[179] = 36'h683199fa6;  // {e_180, e_179} = {106694, 106406}
        exp_pair[180] = 36'h687a1a0c6;  // {e_181, e_180} = {106984, 106694}
        exp_pair[181] = 36'h68c29a1e8;  // {e_182, e_181} = {107274, 106984}
        exp_pair[182] = 36'h690b5a30a;  // {e_183, e_182} = {107565, 107274}
        exp_pair[183] = 36'h69541a42d;  // {e_184, e_183} = {107856, 107565}
        exp_pair[184] = 36'h699d5a550;  // {e_185, e_184} = {108149, 107856}
        exp_pair[185] = 36'h69e69a675;  // {e_186, e_185} = {108442, 108149}
        exp_pair[186] = 36'h6a301a79a;  // {e_187, e_186} = {108736, 108442}
        exp_pair[187] = 36'h6a79da8c0;  // {e_188, e_187} = {109031, 108736}
        exp_pair[188] = 36'h6ac39a9e7;  // {e_189, e_188} = {109326, 109031}
        exp_pair[189] = 36'h6b0ddab0e;  // {e_190, e_189} = {109623, 109326}
        exp_pair[190] = 36'h6b581ac37;  // {e_191, e_190} = {109920, 109623}
        exp_pair[191] = 36'h6ba29ad60;  // {e_192, e_191} = {110218, 109920}
        exp_pair[192] = 36'h6bed5ae8a;  // {e_193, e_192} = {110517, 110218}
        exp_pair[193] = 36'h6c381afb5;  // {e_194, e_193} = {110816, 110517}
        exp_pair[194] = 36'h6c835b0e0;  // {e_195, e_194} = {111117, 110816}
        exp_pair[195] = 36'h6cce9b20d;  // {e_196, e_195} = {111418, 111117}
        exp_pair[196] = 36'h6d1a1b33a;  // {e_197, e_196} = {111720, 111418}
        exp_pair[197] = 36'h6d65db468;  // {e_198, e_197} = {112023, 111720}
        exp_pair[198] = 36'h6db1db597;  // {e_199, e_198} = {112327, 112023}
        exp_pair[199] = 36'h6dfddb6c7;  // {e_200, e_199} = {112631, 112327}
        exp_pair[200] = 36'h6e4a5b7f7;  // {e_201, e_200} = {112937, 112631}
        exp_pair[201] = 36'h6e96db929;  // {e_202, e_201} = {113243, 112937}
        exp_pair[202] = 36'h6ee39ba5b;  // {e_203, e_202} = {113550, 113243}
        exp_pair[203] = 36'h6f309bb8e;  // {e_204, e_203} = {113858, 113550}
        exp_pair[204] = 36'h6f7ddbcc2;  // {e_205, e_204} = {114167, 113858}
        exp_pair[205] = 36'h6fcb1bdf7;  // {e_206, e_205} = {114476, 114167}
        exp_pair[206] = 36'h7018dbf2c;  // {e_207, e_206} = {114787, 114476}
        exp_pair[207] = 36'h70669c063;  // {e_208, e_207} = {115098, 114787}
        exp_pair[208] = 36'h70b49c19a;  // {e_209, e_208} = {115410, 115098}
        exp_pair[209] = 36'h7102dc2d2;  // {e_210, e_209} = {115723, 115410}
        exp_pair[210] = 36'h71511c40b;  // {e_211, e_210} = {116036, 115723}
        exp_pair[211] = 36'h719fdc544;  // {e_212, e_211} = {116351, 116036}
        exp_pair[212] = 36'h71eedc67f;  // {e_213, e_212} = {116667, 116351}
        exp_pair[213] = 36'h723ddc7bb;  // {e_214, e_213} = {116983, 116667}
        exp_pair[214] = 36'h728d1c8f7;  // {e_215, e_214} = {117300, 116983}
        exp_pair[215] = 36'h72dc9ca34;  // {e_216, e_215} = {117618, 117300}
        exp_pair[216] = 36'h732c5cb72;  // {e_217, e_216} = {117937, 117618}
        exp_pair[217] = 36'h737c5ccb1;  // {e_218, e_217} = {118257, 117937}
        exp_pair[218] = 36'h73cc5cdf1;  // {e_219, e_218} = {118577, 118257}
        exp_pair[219] = 36'h741cdcf31;  // {e_220, e_219} = {118899, 118577}
        exp_pair[220] = 36'h746d5d073;  // {e_221, e_220} = {119221, 118899}
        exp_pair[221] = 36'h74be1d1b5;  // {e_222, e_221} = {119544, 119221}
        exp_pair[222] = 36'h750f5d2f8;  // {e_223, e_222} = {119869, 119544}
        exp_pair[223] = 36'h75609d43d;  // {e_224, e_223} = {120194, 119869}
        exp_pair[224] = 36'h75b1dd582;  // {e_225, e_224} = {120519, 120194}
        exp_pair[225] = 36'h76039d6c7;  // {e_226, e_225} = {120846, 120519}
        exp_pair[226] = 36'h76559d80e;  // {e_227, e_226} = {121174, 120846}
        exp_pair[227] = 36'h76a79d956;  // {e_228, e_227} = {121502, 121174}
        exp_pair[228] = 36'h76fa1da9e;  // {e_229, e_228} = {121832, 121502}
        exp_pair[229] = 36'h774c9dbe8;  // {e_230, e_229} = {122162, 121832}
        exp_pair[230] = 36'h779f5dd32;  // {e_231, e_230} = {122493, 122162}
        exp_pair[231] = 36'h77f25de7d;  // {e_232, e_231} = {122825, 122493}
        exp_pair[232] = 36'h78459dfc9;  // {e_233, e_232} = {123158, 122825}
        exp_pair[233] = 36'h78991e116;  // {e_234, e_233} = {123492, 123158}
        exp_pair[234] = 36'h78ecde264;  // {e_235, e_234} = {123827, 123492}
        exp_pair[235] = 36'h7940de3b3;  // {e_236, e_235} = {124163, 123827}
        exp_pair[236] = 36'h79951e503;  // {e_237, e_236} = {124500, 124163}
        exp_pair[237] = 36'h79e95e654;  // {e_238, e_237} = {124837, 124500}
        exp_pair[238] = 36'h7a3e1e7a5;  // {e_239, e_238} = {125176, 124837}
        exp_pair[239] = 36'h7a92de8f8;  // {e_240, e_239} = {125515, 125176}
        exp_pair[240] = 36'h7ae7dea4b;  // {e_241, e_240} = {125855, 125515}
        exp_pair[241] = 36'h7b3d5eb9f;  // {e_242, e_241} = {126197, 125855}
        exp_pair[242] = 36'h7b92decf5;  // {e_243, e_242} = {126539, 126197}
        exp_pair[243] = 36'h7be89ee4b;  // {e_244, e_243} = {126882, 126539}
        exp_pair[244] = 36'h7c3e9efa2;  // {e_245, e_244} = {127226, 126882}
        exp_pair[245] = 36'h7c94df0fa;  // {e_246, e_245} = {127571, 127226}
        exp_pair[246] = 36'h7ceb5f253;  // {e_247, e_246} = {127917, 127571}
        exp_pair[247] = 36'h7d41df3ad;  // {e_248, e_247} = {128263, 127917}
        exp_pair[248] = 36'h7d98df507;  // {e_249, e_248} = {128611, 128263}
        exp_pair[249] = 36'h7df01f663;  // {e_250, e_249} = {128960, 128611}
        exp_pair[250] = 36'h7e479f7c0;  // {e_251, e_250} = {129310, 128960}
        exp_pair[251] = 36'h7e9f1f91e;  // {e_252, e_251} = {129660, 129310}
        exp_pair[252] = 36'h7ef71fa7c;  // {e_253, e_252} = {130012, 129660}
        exp_pair[253] = 36'h7f4f1fbdc;  // {e_254, e_253} = {130364, 130012}
        exp_pair[254] = 36'h7fa79fd3c;  // {e_255, e_254} = {130718, 130364}
        exp_pair[255] = 36'h80001fe9e;  // {e_256, e_255} = {131072, 130718}
        ang_rom[   0] = 36'h00001ffff;
        ang_rom[   1] = 36'h00c91fffe;
        ang_rom[   2] = 36'h01921fff6;
        ang_rom[   3] = 36'h025b5ffea;
        ang_rom[   4] = 36'h03245ffd9;
        ang_rom[   5] = 36'h03ed5ffc2;
        ang_rom[   6] = 36'h04b61ffa7;
        ang_rom[   7] = 36'h057f1ff87;
        ang_rom[   8] = 36'h0647dff62;
        ang_rom[   9] = 36'h0710dff38;
        ang_rom[  10] = 36'h07d95ff09;
        ang_rom[  11] = 36'h08a21fed6;
        ang_rom[  12] = 36'h096a9fe9d;
        ang_rom[  13] = 36'h0a331fe5f;
        ang_rom[  14] = 36'h0afb9fe1d;
        ang_rom[  15] = 36'h0bc3dfdd5;
        ang_rom[  16] = 36'h0c8bdfd89;
        ang_rom[  17] = 36'h0d53dfd38;
        ang_rom[  18] = 36'h0e1bdfce1;
        ang_rom[  19] = 36'h0ee39fc86;
        ang_rom[  20] = 36'h0fab5fc26;
        ang_rom[  21] = 36'h1072dfbc1;
        ang_rom[  22] = 36'h113a1fb58;
        ang_rom[  23] = 36'h12011fae9;
        ang_rom[  24] = 36'h12c81fa75;
        ang_rom[  25] = 36'h138edf9fd;
        ang_rom[  26] = 36'h14559f980;
        ang_rom[  27] = 36'h151bdf8fd;
        ang_rom[  28] = 36'h15e21f876;
        ang_rom[  29] = 36'h16a81f7ea;
        ang_rom[  30] = 36'h176ddf75a;
        ang_rom[  31] = 36'h18339f6c4;
        ang_rom[  32] = 36'h18f8df629;
        ang_rom[  33] = 36'h19bddf58a;
        ang_rom[  34] = 36'h1a82df4e6;
        ang_rom[  35] = 36'h1b475f43d;
        ang_rom[  36] = 36'h1c0b9f38f;
        ang_rom[  37] = 36'h1ccf9f2dd;
        ang_rom[  38] = 36'h1d935f225;
        ang_rom[  39] = 36'h1e56df169;
        ang_rom[  40] = 36'h1f1a1f0a8;
        ang_rom[  41] = 36'h1fdcdefe2;
        ang_rom[  42] = 36'h209f9ef18;
        ang_rom[  43] = 36'h2161dee48;
        ang_rom[  44] = 36'h2223ded74;
        ang_rom[  45] = 36'h22e55ec9b;
        ang_rom[  46] = 36'h23a69ebbe;
        ang_rom[  47] = 36'h24679eadb;
        ang_rom[  48] = 36'h25281e9f4;
        ang_rom[  49] = 36'h25e85e908;
        ang_rom[  50] = 36'h26a85e818;
        ang_rom[  51] = 36'h27679e722;
        ang_rom[  52] = 36'h2826de629;
        ang_rom[  53] = 36'h28e59e52a;
        ang_rom[  54] = 36'h29a3de427;
        ang_rom[  55] = 36'h2a61de31f;
        ang_rom[  56] = 36'h2b1f5e212;
        ang_rom[  57] = 36'h2bdc5e101;
        ang_rom[  58] = 36'h2c991dfeb;
        ang_rom[  59] = 36'h2d555ded0;
        ang_rom[  60] = 36'h2e111ddb1;
        ang_rom[  61] = 36'h2ecc9dc8d;
        ang_rom[  62] = 36'h2f875db65;
        ang_rom[  63] = 36'h3041dda38;
        ang_rom[  64] = 36'h30fbdd907;
        ang_rom[  65] = 36'h31b55d7d1;
        ang_rom[  66] = 36'h326e5d696;
        ang_rom[  67] = 36'h33271d557;
        ang_rom[  68] = 36'h33df1d413;
        ang_rom[  69] = 36'h34969d2cb;
        ang_rom[  70] = 36'h354d9d17e;
        ang_rom[  71] = 36'h36041d02d;
        ang_rom[  72] = 36'h36ba5ced8;
        ang_rom[  73] = 36'h376f9cd7e;
        ang_rom[  74] = 36'h38249cc1f;
        ang_rom[  75] = 36'h38d91cabc;
        ang_rom[  76] = 36'h398cdc955;
        ang_rom[  77] = 36'h3a405c7e9;
        ang_rom[  78] = 36'h3af31c679;
        ang_rom[  79] = 36'h3ba51c504;
        ang_rom[  80] = 36'h3c56dc38b;
        ang_rom[  81] = 36'h3d07dc20e;
        ang_rom[  82] = 36'h3db85c08c;
        ang_rom[  83] = 36'h3e681bf06;
        ang_rom[  84] = 36'h3f175bd7c;
        ang_rom[  85] = 36'h3fc61bbed;
        ang_rom[  86] = 36'h40741ba5b;
        ang_rom[  87] = 36'h41215b8c4;
        ang_rom[  88] = 36'h41ce1b728;
        ang_rom[  89] = 36'h427a5b589;
        ang_rom[  90] = 36'h4325db3e5;
        ang_rom[  91] = 36'h43d09b23d;
        ang_rom[  92] = 36'h447adb091;
        ang_rom[  93] = 36'h45245aee0;
        ang_rom[  94] = 36'h45cd5ad2c;
        ang_rom[  95] = 36'h46759ab73;
        ang_rom[  96] = 36'h471d1a9b6;
        ang_rom[  97] = 36'h47c3da7f6;
        ang_rom[  98] = 36'h486a1a631;
        ang_rom[  99] = 36'h490f5a468;
        ang_rom[ 100] = 36'h49b41a29a;
        ang_rom[ 101] = 36'h4a581a0c9;
        ang_rom[ 102] = 36'h4afb99ef4;
        ang_rom[ 103] = 36'h4b9e19d1b;
        ang_rom[ 104] = 36'h4c3fd9b3e;
        ang_rom[ 105] = 36'h4ce11995d;
        ang_rom[ 106] = 36'h4d8199778;
        ang_rom[ 107] = 36'h4e211958f;
        ang_rom[ 108] = 36'h4ec0193a2;
        ang_rom[ 109] = 36'h4f5e191b1;
        ang_rom[ 110] = 36'h4ffb98fbd;
        ang_rom[ 111] = 36'h509818dc4;
        ang_rom[ 112] = 36'h5133d8bc8;
        ang_rom[ 113] = 36'h51ced89c8;
        ang_rom[ 114] = 36'h5269187c4;
        ang_rom[ 115] = 36'h5302985bc;
        ang_rom[ 116] = 36'h539b583b1;
        ang_rom[ 117] = 36'h5433181a2;
        ang_rom[ 118] = 36'h54ca17f8f;
        ang_rom[ 119] = 36'h556057d78;
        ang_rom[ 120] = 36'h55f5d7b5e;
        ang_rom[ 121] = 36'h568a57940;
        ang_rom[ 122] = 36'h571e1771e;
        ang_rom[ 123] = 36'h57b0d74f9;
        ang_rom[ 124] = 36'h5842d72d1;
        ang_rom[ 125] = 36'h58d4170a4;
        ang_rom[ 126] = 36'h596496e74;
        ang_rom[ 127] = 36'h59f3d6c41;
        ang_rom[ 128] = 36'h5a8296a0a;
        ang_rom[ 129] = 36'h5b10567cf;
        ang_rom[ 130] = 36'h5b9d16592;
        ang_rom[ 131] = 36'h5c2916350;
        ang_rom[ 132] = 36'h5cb45610b;
        ang_rom[ 133] = 36'h5d3e55ec3;
        ang_rom[ 134] = 36'h5dc795c78;
        ang_rom[ 135] = 36'h5e5015a29;
        ang_rom[ 136] = 36'h5ed7957d7;
        ang_rom[ 137] = 36'h5f5e15581;
        ang_rom[ 138] = 36'h5fe3d5328;
        ang_rom[ 139] = 36'h6068950cc;
        ang_rom[ 140] = 36'h60ec54e6d;
        ang_rom[ 141] = 36'h616f14c0a;
        ang_rom[ 142] = 36'h61f1149a4;
        ang_rom[ 143] = 36'h62721473b;
        ang_rom[ 144] = 36'h62f2144cf;
        ang_rom[ 145] = 36'h637114260;
        ang_rom[ 146] = 36'h63ef53fee;
        ang_rom[ 147] = 36'h646c53d78;
        ang_rom[ 148] = 36'h64e893b00;
        ang_rom[ 149] = 36'h6563d3884;
        ang_rom[ 150] = 36'h65de13606;
        ang_rom[ 151] = 36'h665753384;
        ang_rom[ 152] = 36'h66cf930ff;
        ang_rom[ 153] = 36'h6746d2e78;
        ang_rom[ 154] = 36'h67bd12bee;
        ang_rom[ 155] = 36'h683252960;
        ang_rom[ 156] = 36'h68a6926d0;
        ang_rom[ 157] = 36'h691a1243d;
        ang_rom[ 158] = 36'h698c521a8;
        ang_rom[ 159] = 36'h69fd91f0f;
        ang_rom[ 160] = 36'h6a6d91c74;
        ang_rom[ 161] = 36'h6adcd19d6;
        ang_rom[ 162] = 36'h6b4b11735;
        ang_rom[ 163] = 36'h6bb811491;
        ang_rom[ 164] = 36'h6c24511eb;
        ang_rom[ 165] = 36'h6c8f50f42;
        ang_rom[ 166] = 36'h6cf950c97;
        ang_rom[ 167] = 36'h6d62509e9;
        ang_rom[ 168] = 36'h6dca10738;
        ang_rom[ 169] = 36'h6e3110485;
        ang_rom[ 170] = 36'h6e96d01d0;
        ang_rom[ 171] = 36'h6efb4ff18;
        ang_rom[ 172] = 36'h6f5f0fc5d;
        ang_rom[ 173] = 36'h6fc18f9a0;
        ang_rom[ 174] = 36'h70230f6e1;
        ang_rom[ 175] = 36'h70838f41f;
        ang_rom[ 176] = 36'h70e2cf15b;
        ang_rom[ 177] = 36'h71410ee94;
        ang_rom[ 178] = 36'h719e4ebcc;
        ang_rom[ 179] = 36'h71fa4e901;
        ang_rom[ 180] = 36'h72554e633;
        ang_rom[ 181] = 36'h72af0e364;
        ang_rom[ 182] = 36'h7307ce092;
        ang_rom[ 183] = 36'h735f8ddbe;
        ang_rom[ 184] = 36'h73b60dae9;
        ang_rom[ 185] = 36'h740b4d810;
        ang_rom[ 186] = 36'h745f8d536;
        ang_rom[ 187] = 36'h74b2cd25a;
        ang_rom[ 188] = 36'h7504ccf7c;
        ang_rom[ 189] = 36'h7555ccc9c;
        ang_rom[ 190] = 36'h75a58c9b9;
        ang_rom[ 191] = 36'h75f44c6d5;
        ang_rom[ 192] = 36'h7641cc3ef;
        ang_rom[ 193] = 36'h768e0c107;
        ang_rom[ 194] = 36'h76d94be1d;
        ang_rom[ 195] = 36'h77234bb32;
        ang_rom[ 196] = 36'h776c4b844;
        ang_rom[ 197] = 36'h77b40b555;
        ang_rom[ 198] = 36'h77facb264;
        ang_rom[ 199] = 36'h78404af71;
        ang_rom[ 200] = 36'h78848ac7d;
        ang_rom[ 201] = 36'h78c7ca987;
        ang_rom[ 202] = 36'h7909ca68f;
        ang_rom[ 203] = 36'h794a8a396;
        ang_rom[ 204] = 36'h798a4a09b;
        ang_rom[ 205] = 36'h79c889d9e;
        ang_rom[ 206] = 36'h7a0609aa1;
        ang_rom[ 207] = 36'h7a42097a1;
        ang_rom[ 208] = 36'h7a7d094a0;
        ang_rom[ 209] = 36'h7ab6c919e;
        ang_rom[ 210] = 36'h7aef88e9a;
        ang_rom[ 211] = 36'h7b26c8b95;
        ang_rom[ 212] = 36'h7b5d0888f;
        ang_rom[ 213] = 36'h7b9208587;
        ang_rom[ 214] = 36'h7bc60827e;
        ang_rom[ 215] = 36'h7bf887f73;
        ang_rom[ 216] = 36'h7c2a07c68;
        ang_rom[ 217] = 36'h7c5a4795b;
        ang_rom[ 218] = 36'h7c894764d;
        ang_rom[ 219] = 36'h7cb74733e;
        ang_rom[ 220] = 36'h7ce3c702e;
        ang_rom[ 221] = 36'h7d0f46d1d;
        ang_rom[ 222] = 36'h7d3986a0b;
        ang_rom[ 223] = 36'h7d62866f7;
        ang_rom[ 224] = 36'h7d8a463e3;
        ang_rom[ 225] = 36'h7db1060ce;
        ang_rom[ 226] = 36'h7dd685db7;
        ang_rom[ 227] = 36'h7dfa85aa0;
        ang_rom[ 228] = 36'h7e1d85788;
        ang_rom[ 229] = 36'h7e3f4546f;
        ang_rom[ 230] = 36'h7e6005156;
        ang_rom[ 231] = 36'h7e7f44e3b;
        ang_rom[ 232] = 36'h7e9d44b20;
        ang_rom[ 233] = 36'h7eba44804;
        ang_rom[ 234] = 36'h7ed6044e8;
        ang_rom[ 235] = 36'h7ef0441cb;
        ang_rom[ 236] = 36'h7f0983ead;
        ang_rom[ 237] = 36'h7f2183b8e;
        ang_rom[ 238] = 36'h7f384386f;
        ang_rom[ 239] = 36'h7f4e0354f;
        ang_rom[ 240] = 36'h7f624322f;
        ang_rom[ 241] = 36'h7f7542f0f;
        ang_rom[ 242] = 36'h7f8742bee;
        ang_rom[ 243] = 36'h7f97c28cc;
        ang_rom[ 244] = 36'h7fa7425aa;
        ang_rom[ 245] = 36'h7fb582288;
        ang_rom[ 246] = 36'h7fc241f65;
        ang_rom[ 247] = 36'h7fce01c43;
        ang_rom[ 248] = 36'h7fd88191f;
        ang_rom[ 249] = 36'h7fe1c15fc;
        ang_rom[ 250] = 36'h7fe9c12d8;
        ang_rom[ 251] = 36'h7ff080fb5;
        ang_rom[ 252] = 36'h7ff640c91;
        ang_rom[ 253] = 36'h7ffa8096d;
        ang_rom[ 254] = 36'h7ffd80648;
        ang_rom[ 255] = 36'h7fff80324;
        ang_rom[ 256] = 36'h7fffc0000;
        ang_rom[ 257] = 36'h7fffbfcdc;
        ang_rom[ 258] = 36'h7ffdbf9b8;
        ang_rom[ 259] = 36'h7ffabf693;
        ang_rom[ 260] = 36'h7ff67f36f;
        ang_rom[ 261] = 36'h7ff0bf04b;
        ang_rom[ 262] = 36'h7fe9fed28;
        ang_rom[ 263] = 36'h7fe1fea04;
        ang_rom[ 264] = 36'h7fd8be6e1;
        ang_rom[ 265] = 36'h7fce3e3bd;
        ang_rom[ 266] = 36'h7fc27e09b;
        ang_rom[ 267] = 36'h7fb5bdd78;
        ang_rom[ 268] = 36'h7fa77da56;
        ang_rom[ 269] = 36'h7f97fd734;
        ang_rom[ 270] = 36'h7f877d412;
        ang_rom[ 271] = 36'h7f757d0f1;
        ang_rom[ 272] = 36'h7f627cdd1;
        ang_rom[ 273] = 36'h7f4e3cab1;
        ang_rom[ 274] = 36'h7f387c791;
        ang_rom[ 275] = 36'h7f21bc472;
        ang_rom[ 276] = 36'h7f09bc153;
        ang_rom[ 277] = 36'h7ef07be35;
        ang_rom[ 278] = 36'h7ed63bb18;
        ang_rom[ 279] = 36'h7eba7b7fc;
        ang_rom[ 280] = 36'h7e9d7b4e0;
        ang_rom[ 281] = 36'h7e7f7b1c5;
        ang_rom[ 282] = 36'h7e603aeaa;
        ang_rom[ 283] = 36'h7e3f7ab91;
        ang_rom[ 284] = 36'h7e1dba878;
        ang_rom[ 285] = 36'h7dfaba560;
        ang_rom[ 286] = 36'h7dd6ba249;
        ang_rom[ 287] = 36'h7db139f32;
        ang_rom[ 288] = 36'h7d8a79c1d;
        ang_rom[ 289] = 36'h7d62b9909;
        ang_rom[ 290] = 36'h7d39b95f5;
        ang_rom[ 291] = 36'h7d0f792e3;
        ang_rom[ 292] = 36'h7ce3f8fd2;
        ang_rom[ 293] = 36'h7cb778cc2;
        ang_rom[ 294] = 36'h7c89789b3;
        ang_rom[ 295] = 36'h7c5a786a5;
        ang_rom[ 296] = 36'h7c2a38398;
        ang_rom[ 297] = 36'h7bf8b808d;
        ang_rom[ 298] = 36'h7bc637d82;
        ang_rom[ 299] = 36'h7b9237a79;
        ang_rom[ 300] = 36'h7b5d37771;
        ang_rom[ 301] = 36'h7b26f746b;
        ang_rom[ 302] = 36'h7aefb7166;
        ang_rom[ 303] = 36'h7ab6f6e62;
        ang_rom[ 304] = 36'h7a7d36b60;
        ang_rom[ 305] = 36'h7a423685f;
        ang_rom[ 306] = 36'h7a063655f;
        ang_rom[ 307] = 36'h79c8b6262;
        ang_rom[ 308] = 36'h798a75f65;
        ang_rom[ 309] = 36'h794ab5c6a;
        ang_rom[ 310] = 36'h7909f5971;
        ang_rom[ 311] = 36'h78c7f5679;
        ang_rom[ 312] = 36'h7884b5383;
        ang_rom[ 313] = 36'h78407508f;
        ang_rom[ 314] = 36'h77faf4d9c;
        ang_rom[ 315] = 36'h77b434aab;
        ang_rom[ 316] = 36'h776c747bc;
        ang_rom[ 317] = 36'h7723744ce;
        ang_rom[ 318] = 36'h76d9741e3;
        ang_rom[ 319] = 36'h768e33ef9;
        ang_rom[ 320] = 36'h7641f3c11;
        ang_rom[ 321] = 36'h75f47392b;
        ang_rom[ 322] = 36'h75a5b3647;
        ang_rom[ 323] = 36'h7555f3364;
        ang_rom[ 324] = 36'h7504f3084;
        ang_rom[ 325] = 36'h74b2f2da6;
        ang_rom[ 326] = 36'h745fb2aca;
        ang_rom[ 327] = 36'h740b727f0;
        ang_rom[ 328] = 36'h73b632517;
        ang_rom[ 329] = 36'h735fb2242;
        ang_rom[ 330] = 36'h7307f1f6e;
        ang_rom[ 331] = 36'h72af31c9c;
        ang_rom[ 332] = 36'h7255719cd;
        ang_rom[ 333] = 36'h71fa716ff;
        ang_rom[ 334] = 36'h719e71434;
        ang_rom[ 335] = 36'h71413116c;
        ang_rom[ 336] = 36'h70e2f0ea5;
        ang_rom[ 337] = 36'h7083b0be1;
        ang_rom[ 338] = 36'h70233091f;
        ang_rom[ 339] = 36'h6fc1b0660;
        ang_rom[ 340] = 36'h6f5f303a3;
        ang_rom[ 341] = 36'h6efb700e8;
        ang_rom[ 342] = 36'h6e96efe30;
        ang_rom[ 343] = 36'h6e312fb7b;
        ang_rom[ 344] = 36'h6dca2f8c8;
        ang_rom[ 345] = 36'h6d626f617;
        ang_rom[ 346] = 36'h6cf96f369;
        ang_rom[ 347] = 36'h6c8f6f0be;
        ang_rom[ 348] = 36'h6c246ee15;
        ang_rom[ 349] = 36'h6bb82eb6f;
        ang_rom[ 350] = 36'h6b4b2e8cb;
        ang_rom[ 351] = 36'h6adcee62a;
        ang_rom[ 352] = 36'h6a6dae38c;
        ang_rom[ 353] = 36'h69fdae0f1;
        ang_rom[ 354] = 36'h698c6de58;
        ang_rom[ 355] = 36'h691a2dbc3;
        ang_rom[ 356] = 36'h68a6ad930;
        ang_rom[ 357] = 36'h68326d6a0;
        ang_rom[ 358] = 36'h67bd2d412;
        ang_rom[ 359] = 36'h6746ed188;
        ang_rom[ 360] = 36'h66cfacf01;
        ang_rom[ 361] = 36'h66576cc7c;
        ang_rom[ 362] = 36'h65de2c9fa;
        ang_rom[ 363] = 36'h6563ec77c;
        ang_rom[ 364] = 36'h64e8ac500;
        ang_rom[ 365] = 36'h646c6c288;
        ang_rom[ 366] = 36'h63ef6c012;
        ang_rom[ 367] = 36'h63712bda0;
        ang_rom[ 368] = 36'h62f22bb31;
        ang_rom[ 369] = 36'h62722b8c5;
        ang_rom[ 370] = 36'h61f12b65c;
        ang_rom[ 371] = 36'h616f2b3f6;
        ang_rom[ 372] = 36'h60ec6b193;
        ang_rom[ 373] = 36'h6068aaf34;
        ang_rom[ 374] = 36'h5fe3eacd8;
        ang_rom[ 375] = 36'h5f5e2aa7f;
        ang_rom[ 376] = 36'h5ed7aa829;
        ang_rom[ 377] = 36'h5e502a5d7;
        ang_rom[ 378] = 36'h5dc7aa388;
        ang_rom[ 379] = 36'h5d3e6a13d;
        ang_rom[ 380] = 36'h5cb469ef5;
        ang_rom[ 381] = 36'h5c2929cb0;
        ang_rom[ 382] = 36'h5b9d29a6e;
        ang_rom[ 383] = 36'h5b1069831;
        ang_rom[ 384] = 36'h5a82a95f6;
        ang_rom[ 385] = 36'h59f3e93bf;
        ang_rom[ 386] = 36'h5964a918c;
        ang_rom[ 387] = 36'h58d428f5c;
        ang_rom[ 388] = 36'h5842e8d2f;
        ang_rom[ 389] = 36'h57b0e8b07;
        ang_rom[ 390] = 36'h571e288e2;
        ang_rom[ 391] = 36'h568a686c0;
        ang_rom[ 392] = 36'h55f5e84a2;
        ang_rom[ 393] = 36'h556068288;
        ang_rom[ 394] = 36'h54ca28071;
        ang_rom[ 395] = 36'h543327e5e;
        ang_rom[ 396] = 36'h539b67c4f;
        ang_rom[ 397] = 36'h5302a7a44;
        ang_rom[ 398] = 36'h52692783c;
        ang_rom[ 399] = 36'h51cee7638;
        ang_rom[ 400] = 36'h5133e7438;
        ang_rom[ 401] = 36'h50982723c;
        ang_rom[ 402] = 36'h4ffba7043;
        ang_rom[ 403] = 36'h4f5e26e4f;
        ang_rom[ 404] = 36'h4ec026c5e;
        ang_rom[ 405] = 36'h4e2126a71;
        ang_rom[ 406] = 36'h4d81a6888;
        ang_rom[ 407] = 36'h4ce1266a3;
        ang_rom[ 408] = 36'h4c3fe64c2;
        ang_rom[ 409] = 36'h4b9e262e5;
        ang_rom[ 410] = 36'h4afba610c;
        ang_rom[ 411] = 36'h4a5825f37;
        ang_rom[ 412] = 36'h49b425d66;
        ang_rom[ 413] = 36'h490f65b98;
        ang_rom[ 414] = 36'h486a259cf;
        ang_rom[ 415] = 36'h47c3e580a;
        ang_rom[ 416] = 36'h471d2564a;
        ang_rom[ 417] = 36'h4675a548d;
        ang_rom[ 418] = 36'h45cd652d4;
        ang_rom[ 419] = 36'h452465120;
        ang_rom[ 420] = 36'h447ae4f6f;
        ang_rom[ 421] = 36'h43d0a4dc3;
        ang_rom[ 422] = 36'h4325e4c1b;
        ang_rom[ 423] = 36'h427a64a77;
        ang_rom[ 424] = 36'h41ce248d8;
        ang_rom[ 425] = 36'h41216473c;
        ang_rom[ 426] = 36'h4074245a5;
        ang_rom[ 427] = 36'h3fc624413;
        ang_rom[ 428] = 36'h3f1764284;
        ang_rom[ 429] = 36'h3e68240fa;
        ang_rom[ 430] = 36'h3db863f74;
        ang_rom[ 431] = 36'h3d07e3df2;
        ang_rom[ 432] = 36'h3c56e3c75;
        ang_rom[ 433] = 36'h3ba523afc;
        ang_rom[ 434] = 36'h3af323987;
        ang_rom[ 435] = 36'h3a4063817;
        ang_rom[ 436] = 36'h398ce36ab;
        ang_rom[ 437] = 36'h38d923544;
        ang_rom[ 438] = 36'h3824a33e1;
        ang_rom[ 439] = 36'h376fa3282;
        ang_rom[ 440] = 36'h36ba63128;
        ang_rom[ 441] = 36'h360422fd3;
        ang_rom[ 442] = 36'h354da2e82;
        ang_rom[ 443] = 36'h3496a2d35;
        ang_rom[ 444] = 36'h33df22bed;
        ang_rom[ 445] = 36'h332722aa9;
        ang_rom[ 446] = 36'h326e6296a;
        ang_rom[ 447] = 36'h31b56282f;
        ang_rom[ 448] = 36'h30fbe26f9;
        ang_rom[ 449] = 36'h3041e25c8;
        ang_rom[ 450] = 36'h2f876249b;
        ang_rom[ 451] = 36'h2ecca2373;
        ang_rom[ 452] = 36'h2e112224f;
        ang_rom[ 453] = 36'h2d5562130;
        ang_rom[ 454] = 36'h2c9922015;
        ang_rom[ 455] = 36'h2bdc61eff;
        ang_rom[ 456] = 36'h2b1f61dee;
        ang_rom[ 457] = 36'h2a61e1ce1;
        ang_rom[ 458] = 36'h29a3e1bd9;
        ang_rom[ 459] = 36'h28e5a1ad6;
        ang_rom[ 460] = 36'h2826e19d7;
        ang_rom[ 461] = 36'h2767a18de;
        ang_rom[ 462] = 36'h26a8617e8;
        ang_rom[ 463] = 36'h25e8616f8;
        ang_rom[ 464] = 36'h25282160c;
        ang_rom[ 465] = 36'h2467a1525;
        ang_rom[ 466] = 36'h23a6a1442;
        ang_rom[ 467] = 36'h22e561365;
        ang_rom[ 468] = 36'h2223e128c;
        ang_rom[ 469] = 36'h2161e11b8;
        ang_rom[ 470] = 36'h209fa10e8;
        ang_rom[ 471] = 36'h1fdce101e;
        ang_rom[ 472] = 36'h1f1a20f58;
        ang_rom[ 473] = 36'h1e56e0e97;
        ang_rom[ 474] = 36'h1d9360ddb;
        ang_rom[ 475] = 36'h1ccfa0d23;
        ang_rom[ 476] = 36'h1c0ba0c71;
        ang_rom[ 477] = 36'h1b4760bc3;
        ang_rom[ 478] = 36'h1a82e0b1a;
        ang_rom[ 479] = 36'h19bde0a76;
        ang_rom[ 480] = 36'h18f8e09d7;
        ang_rom[ 481] = 36'h1833a093c;
        ang_rom[ 482] = 36'h176de08a6;
        ang_rom[ 483] = 36'h16a820816;
        ang_rom[ 484] = 36'h15e22078a;
        ang_rom[ 485] = 36'h151be0703;
        ang_rom[ 486] = 36'h1455a0680;
        ang_rom[ 487] = 36'h138ee0603;
        ang_rom[ 488] = 36'h12c82058b;
        ang_rom[ 489] = 36'h120120517;
        ang_rom[ 490] = 36'h113a204a8;
        ang_rom[ 491] = 36'h1072e043f;
        ang_rom[ 492] = 36'h0fab603da;
        ang_rom[ 493] = 36'h0ee3a037a;
        ang_rom[ 494] = 36'h0e1be031f;
        ang_rom[ 495] = 36'h0d53e02c8;
        ang_rom[ 496] = 36'h0c8be0277;
        ang_rom[ 497] = 36'h0bc3e022b;
        ang_rom[ 498] = 36'h0afba01e3;
        ang_rom[ 499] = 36'h0a33201a1;
        ang_rom[ 500] = 36'h096aa0163;
        ang_rom[ 501] = 36'h08a22012a;
        ang_rom[ 502] = 36'h07d9600f7;
        ang_rom[ 503] = 36'h0710e00c8;
        ang_rom[ 504] = 36'h0647e009e;
        ang_rom[ 505] = 36'h057f20079;
        ang_rom[ 506] = 36'h04b620059;
        ang_rom[ 507] = 36'h03ed6003e;
        ang_rom[ 508] = 36'h032460027;
        ang_rom[ 509] = 36'h025b60016;
        ang_rom[ 510] = 36'h01922000a;
        ang_rom[ 511] = 36'h00c920002;
        ang_rom[ 512] = 36'h000020000;
        ang_rom[ 513] = 36'hff3720002;
        ang_rom[ 514] = 36'hfe6e2000a;
        ang_rom[ 515] = 36'hfda4e0016;
        ang_rom[ 516] = 36'hfcdbe0027;
        ang_rom[ 517] = 36'hfc12e003e;
        ang_rom[ 518] = 36'hfb4a20059;
        ang_rom[ 519] = 36'hfa8120079;
        ang_rom[ 520] = 36'hf9b86009e;
        ang_rom[ 521] = 36'hf8ef600c8;
        ang_rom[ 522] = 36'hf826e00f7;
        ang_rom[ 523] = 36'hf75e2012a;
        ang_rom[ 524] = 36'hf695a0163;
        ang_rom[ 525] = 36'hf5cd201a1;
        ang_rom[ 526] = 36'hf504a01e3;
        ang_rom[ 527] = 36'hf43c6022b;
        ang_rom[ 528] = 36'hf37460277;
        ang_rom[ 529] = 36'hf2ac602c8;
        ang_rom[ 530] = 36'hf1e46031f;
        ang_rom[ 531] = 36'hf11ca037a;
        ang_rom[ 532] = 36'hf054e03da;
        ang_rom[ 533] = 36'hef8d6043f;
        ang_rom[ 534] = 36'heec6204a8;
        ang_rom[ 535] = 36'hedff20517;
        ang_rom[ 536] = 36'hed382058b;
        ang_rom[ 537] = 36'hec7160603;
        ang_rom[ 538] = 36'hebaaa0680;
        ang_rom[ 539] = 36'heae460703;
        ang_rom[ 540] = 36'hea1e2078a;
        ang_rom[ 541] = 36'he95820816;
        ang_rom[ 542] = 36'he892608a6;
        ang_rom[ 543] = 36'he7cca093c;
        ang_rom[ 544] = 36'he707609d7;
        ang_rom[ 545] = 36'he64260a76;
        ang_rom[ 546] = 36'he57d60b1a;
        ang_rom[ 547] = 36'he4b8e0bc3;
        ang_rom[ 548] = 36'he3f4a0c71;
        ang_rom[ 549] = 36'he330a0d23;
        ang_rom[ 550] = 36'he26ce0ddb;
        ang_rom[ 551] = 36'he1a960e97;
        ang_rom[ 552] = 36'he0e620f58;
        ang_rom[ 553] = 36'he0236101e;
        ang_rom[ 554] = 36'hdf60a10e8;
        ang_rom[ 555] = 36'hde9e611b8;
        ang_rom[ 556] = 36'hdddc6128c;
        ang_rom[ 557] = 36'hdd1ae1365;
        ang_rom[ 558] = 36'hdc59a1442;
        ang_rom[ 559] = 36'hdb98a1525;
        ang_rom[ 560] = 36'hdad82160c;
        ang_rom[ 561] = 36'hda17e16f8;
        ang_rom[ 562] = 36'hd957e17e8;
        ang_rom[ 563] = 36'hd898a18de;
        ang_rom[ 564] = 36'hd7d9619d7;
        ang_rom[ 565] = 36'hd71aa1ad6;
        ang_rom[ 566] = 36'hd65c61bd9;
        ang_rom[ 567] = 36'hd59e61ce1;
        ang_rom[ 568] = 36'hd4e0e1dee;
        ang_rom[ 569] = 36'hd423e1eff;
        ang_rom[ 570] = 36'hd36722015;
        ang_rom[ 571] = 36'hd2aae2130;
        ang_rom[ 572] = 36'hd1ef2224f;
        ang_rom[ 573] = 36'hd133a2373;
        ang_rom[ 574] = 36'hd078e249b;
        ang_rom[ 575] = 36'hcfbe625c8;
        ang_rom[ 576] = 36'hcf04626f9;
        ang_rom[ 577] = 36'hce4ae282f;
        ang_rom[ 578] = 36'hcd91e296a;
        ang_rom[ 579] = 36'hccd922aa9;
        ang_rom[ 580] = 36'hcc2122bed;
        ang_rom[ 581] = 36'hcb69a2d35;
        ang_rom[ 582] = 36'hcab2a2e82;
        ang_rom[ 583] = 36'hc9fc22fd3;
        ang_rom[ 584] = 36'hc945e3128;
        ang_rom[ 585] = 36'hc890a3282;
        ang_rom[ 586] = 36'hc7dba33e1;
        ang_rom[ 587] = 36'hc72723544;
        ang_rom[ 588] = 36'hc673636ab;
        ang_rom[ 589] = 36'hc5bfe3817;
        ang_rom[ 590] = 36'hc50d23987;
        ang_rom[ 591] = 36'hc45b23afc;
        ang_rom[ 592] = 36'hc3a963c75;
        ang_rom[ 593] = 36'hc2f863df2;
        ang_rom[ 594] = 36'hc247e3f74;
        ang_rom[ 595] = 36'hc198240fa;
        ang_rom[ 596] = 36'hc0e8e4284;
        ang_rom[ 597] = 36'hc03a24413;
        ang_rom[ 598] = 36'hbf8c245a5;
        ang_rom[ 599] = 36'hbedee473c;
        ang_rom[ 600] = 36'hbe32248d8;
        ang_rom[ 601] = 36'hbd85e4a77;
        ang_rom[ 602] = 36'hbcda64c1b;
        ang_rom[ 603] = 36'hbc2fa4dc3;
        ang_rom[ 604] = 36'hbb8564f6f;
        ang_rom[ 605] = 36'hbadbe5120;
        ang_rom[ 606] = 36'hba32e52d4;
        ang_rom[ 607] = 36'hb98aa548d;
        ang_rom[ 608] = 36'hb8e32564a;
        ang_rom[ 609] = 36'hb83c6580a;
        ang_rom[ 610] = 36'hb796259cf;
        ang_rom[ 611] = 36'hb6f0e5b98;
        ang_rom[ 612] = 36'hb64c25d66;
        ang_rom[ 613] = 36'hb5a825f37;
        ang_rom[ 614] = 36'hb504a610c;
        ang_rom[ 615] = 36'hb462262e5;
        ang_rom[ 616] = 36'hb3c0664c2;
        ang_rom[ 617] = 36'hb31f266a3;
        ang_rom[ 618] = 36'hb27ea6888;
        ang_rom[ 619] = 36'hb1df26a71;
        ang_rom[ 620] = 36'hb14026c5e;
        ang_rom[ 621] = 36'hb0a226e4f;
        ang_rom[ 622] = 36'hb004a7043;
        ang_rom[ 623] = 36'haf682723c;
        ang_rom[ 624] = 36'haecc67438;
        ang_rom[ 625] = 36'hae3167638;
        ang_rom[ 626] = 36'had972783c;
        ang_rom[ 627] = 36'hacfda7a44;
        ang_rom[ 628] = 36'hac64e7c4f;
        ang_rom[ 629] = 36'habcd27e5e;
        ang_rom[ 630] = 36'hab3628071;
        ang_rom[ 631] = 36'haa9fe8288;
        ang_rom[ 632] = 36'haa0a684a2;
        ang_rom[ 633] = 36'ha975e86c0;
        ang_rom[ 634] = 36'ha8e2288e2;
        ang_rom[ 635] = 36'ha84f68b07;
        ang_rom[ 636] = 36'ha7bd68d2f;
        ang_rom[ 637] = 36'ha72c28f5c;
        ang_rom[ 638] = 36'ha69ba918c;
        ang_rom[ 639] = 36'ha60c693bf;
        ang_rom[ 640] = 36'ha57da95f6;
        ang_rom[ 641] = 36'ha4efe9831;
        ang_rom[ 642] = 36'ha46329a6e;
        ang_rom[ 643] = 36'ha3d729cb0;
        ang_rom[ 644] = 36'ha34be9ef5;
        ang_rom[ 645] = 36'ha2c1ea13d;
        ang_rom[ 646] = 36'ha238aa388;
        ang_rom[ 647] = 36'ha1b02a5d7;
        ang_rom[ 648] = 36'ha128aa829;
        ang_rom[ 649] = 36'ha0a22aa7f;
        ang_rom[ 650] = 36'ha01c6acd8;
        ang_rom[ 651] = 36'h9f97aaf34;
        ang_rom[ 652] = 36'h9f13eb193;
        ang_rom[ 653] = 36'h9e912b3f6;
        ang_rom[ 654] = 36'h9e0f2b65c;
        ang_rom[ 655] = 36'h9d8e2b8c5;
        ang_rom[ 656] = 36'h9d0e2bb31;
        ang_rom[ 657] = 36'h9c8f2bda0;
        ang_rom[ 658] = 36'h9c10ec012;
        ang_rom[ 659] = 36'h9b93ec288;
        ang_rom[ 660] = 36'h9b17ac500;
        ang_rom[ 661] = 36'h9a9c6c77c;
        ang_rom[ 662] = 36'h9a222c9fa;
        ang_rom[ 663] = 36'h99a8ecc7c;
        ang_rom[ 664] = 36'h9930acf01;
        ang_rom[ 665] = 36'h98b96d188;
        ang_rom[ 666] = 36'h98432d412;
        ang_rom[ 667] = 36'h97cded6a0;
        ang_rom[ 668] = 36'h9759ad930;
        ang_rom[ 669] = 36'h96e62dbc3;
        ang_rom[ 670] = 36'h9673ede58;
        ang_rom[ 671] = 36'h9602ae0f1;
        ang_rom[ 672] = 36'h9592ae38c;
        ang_rom[ 673] = 36'h95236e62a;
        ang_rom[ 674] = 36'h94b52e8cb;
        ang_rom[ 675] = 36'h94482eb6f;
        ang_rom[ 676] = 36'h93dbeee15;
        ang_rom[ 677] = 36'h9370ef0be;
        ang_rom[ 678] = 36'h9306ef369;
        ang_rom[ 679] = 36'h929def617;
        ang_rom[ 680] = 36'h92362f8c8;
        ang_rom[ 681] = 36'h91cf2fb7b;
        ang_rom[ 682] = 36'h91696fe30;
        ang_rom[ 683] = 36'h9104f00e8;
        ang_rom[ 684] = 36'h90a1303a3;
        ang_rom[ 685] = 36'h903eb0660;
        ang_rom[ 686] = 36'h8fdd3091f;
        ang_rom[ 687] = 36'h8f7cb0be1;
        ang_rom[ 688] = 36'h8f1d70ea5;
        ang_rom[ 689] = 36'h8ebf3116c;
        ang_rom[ 690] = 36'h8e61f1434;
        ang_rom[ 691] = 36'h8e05f16ff;
        ang_rom[ 692] = 36'h8daaf19cd;
        ang_rom[ 693] = 36'h8d5131c9c;
        ang_rom[ 694] = 36'h8cf871f6e;
        ang_rom[ 695] = 36'h8ca0b2242;
        ang_rom[ 696] = 36'h8c4a32517;
        ang_rom[ 697] = 36'h8bf4f27f0;
        ang_rom[ 698] = 36'h8ba0b2aca;
        ang_rom[ 699] = 36'h8b4d72da6;
        ang_rom[ 700] = 36'h8afb73084;
        ang_rom[ 701] = 36'h8aaa73364;
        ang_rom[ 702] = 36'h8a5ab3647;
        ang_rom[ 703] = 36'h8a0bf392b;
        ang_rom[ 704] = 36'h89be73c11;
        ang_rom[ 705] = 36'h897233ef9;
        ang_rom[ 706] = 36'h8926f41e3;
        ang_rom[ 707] = 36'h88dcf44ce;
        ang_rom[ 708] = 36'h8893f47bc;
        ang_rom[ 709] = 36'h884c34aab;
        ang_rom[ 710] = 36'h880574d9c;
        ang_rom[ 711] = 36'h87bff508f;
        ang_rom[ 712] = 36'h877bb5383;
        ang_rom[ 713] = 36'h873875679;
        ang_rom[ 714] = 36'h86f675971;
        ang_rom[ 715] = 36'h86b5b5c6a;
        ang_rom[ 716] = 36'h8675f5f65;
        ang_rom[ 717] = 36'h8637b6262;
        ang_rom[ 718] = 36'h85fa3655f;
        ang_rom[ 719] = 36'h85be3685f;
        ang_rom[ 720] = 36'h858336b60;
        ang_rom[ 721] = 36'h854976e62;
        ang_rom[ 722] = 36'h8510b7166;
        ang_rom[ 723] = 36'h84d97746b;
        ang_rom[ 724] = 36'h84a337771;
        ang_rom[ 725] = 36'h846e37a79;
        ang_rom[ 726] = 36'h843a37d82;
        ang_rom[ 727] = 36'h8407b808d;
        ang_rom[ 728] = 36'h83d638398;
        ang_rom[ 729] = 36'h83a5f86a5;
        ang_rom[ 730] = 36'h8376f89b3;
        ang_rom[ 731] = 36'h8348f8cc2;
        ang_rom[ 732] = 36'h831c78fd2;
        ang_rom[ 733] = 36'h82f0f92e3;
        ang_rom[ 734] = 36'h82c6b95f5;
        ang_rom[ 735] = 36'h829db9909;
        ang_rom[ 736] = 36'h8275f9c1d;
        ang_rom[ 737] = 36'h824f39f32;
        ang_rom[ 738] = 36'h8229ba249;
        ang_rom[ 739] = 36'h8205ba560;
        ang_rom[ 740] = 36'h81e2ba878;
        ang_rom[ 741] = 36'h81c0fab91;
        ang_rom[ 742] = 36'h81a03aeaa;
        ang_rom[ 743] = 36'h8180fb1c5;
        ang_rom[ 744] = 36'h8162fb4e0;
        ang_rom[ 745] = 36'h8145fb7fc;
        ang_rom[ 746] = 36'h812a3bb18;
        ang_rom[ 747] = 36'h810ffbe35;
        ang_rom[ 748] = 36'h80f6bc153;
        ang_rom[ 749] = 36'h80debc472;
        ang_rom[ 750] = 36'h80c7fc791;
        ang_rom[ 751] = 36'h80b23cab1;
        ang_rom[ 752] = 36'h809dfcdd1;
        ang_rom[ 753] = 36'h808afd0f1;
        ang_rom[ 754] = 36'h8078fd412;
        ang_rom[ 755] = 36'h80687d734;
        ang_rom[ 756] = 36'h8058fda56;
        ang_rom[ 757] = 36'h804abdd78;
        ang_rom[ 758] = 36'h803dfe09b;
        ang_rom[ 759] = 36'h80323e3bd;
        ang_rom[ 760] = 36'h8027be6e1;
        ang_rom[ 761] = 36'h801e7ea04;
        ang_rom[ 762] = 36'h80167ed28;
        ang_rom[ 763] = 36'h800fbf04b;
        ang_rom[ 764] = 36'h8009ff36f;
        ang_rom[ 765] = 36'h8005bf693;
        ang_rom[ 766] = 36'h8002bf9b8;
        ang_rom[ 767] = 36'h8000bfcdc;
        ang_rom[ 768] = 36'h800000000;
        ang_rom[ 769] = 36'h800080324;
        ang_rom[ 770] = 36'h800280648;
        ang_rom[ 771] = 36'h80058096d;
        ang_rom[ 772] = 36'h8009c0c91;
        ang_rom[ 773] = 36'h800f80fb5;
        ang_rom[ 774] = 36'h8016412d8;
        ang_rom[ 775] = 36'h801e415fc;
        ang_rom[ 776] = 36'h80278191f;
        ang_rom[ 777] = 36'h803201c43;
        ang_rom[ 778] = 36'h803dc1f65;
        ang_rom[ 779] = 36'h804a82288;
        ang_rom[ 780] = 36'h8058c25aa;
        ang_rom[ 781] = 36'h8068428cc;
        ang_rom[ 782] = 36'h8078c2bee;
        ang_rom[ 783] = 36'h808ac2f0f;
        ang_rom[ 784] = 36'h809dc322f;
        ang_rom[ 785] = 36'h80b20354f;
        ang_rom[ 786] = 36'h80c7c386f;
        ang_rom[ 787] = 36'h80de83b8e;
        ang_rom[ 788] = 36'h80f683ead;
        ang_rom[ 789] = 36'h810fc41cb;
        ang_rom[ 790] = 36'h812a044e8;
        ang_rom[ 791] = 36'h8145c4804;
        ang_rom[ 792] = 36'h8162c4b20;
        ang_rom[ 793] = 36'h8180c4e3b;
        ang_rom[ 794] = 36'h81a005156;
        ang_rom[ 795] = 36'h81c0c546f;
        ang_rom[ 796] = 36'h81e285788;
        ang_rom[ 797] = 36'h820585aa0;
        ang_rom[ 798] = 36'h822985db7;
        ang_rom[ 799] = 36'h824f060ce;
        ang_rom[ 800] = 36'h8275c63e3;
        ang_rom[ 801] = 36'h829d866f7;
        ang_rom[ 802] = 36'h82c686a0b;
        ang_rom[ 803] = 36'h82f0c6d1d;
        ang_rom[ 804] = 36'h831c4702e;
        ang_rom[ 805] = 36'h8348c733e;
        ang_rom[ 806] = 36'h8376c764d;
        ang_rom[ 807] = 36'h83a5c795b;
        ang_rom[ 808] = 36'h83d607c68;
        ang_rom[ 809] = 36'h840787f73;
        ang_rom[ 810] = 36'h843a0827e;
        ang_rom[ 811] = 36'h846e08587;
        ang_rom[ 812] = 36'h84a30888f;
        ang_rom[ 813] = 36'h84d948b95;
        ang_rom[ 814] = 36'h851088e9a;
        ang_rom[ 815] = 36'h85494919e;
        ang_rom[ 816] = 36'h8583094a0;
        ang_rom[ 817] = 36'h85be097a1;
        ang_rom[ 818] = 36'h85fa09aa1;
        ang_rom[ 819] = 36'h863789d9e;
        ang_rom[ 820] = 36'h8675ca09b;
        ang_rom[ 821] = 36'h86b58a396;
        ang_rom[ 822] = 36'h86f64a68f;
        ang_rom[ 823] = 36'h87384a987;
        ang_rom[ 824] = 36'h877b8ac7d;
        ang_rom[ 825] = 36'h87bfcaf71;
        ang_rom[ 826] = 36'h88054b264;
        ang_rom[ 827] = 36'h884c0b555;
        ang_rom[ 828] = 36'h8893cb844;
        ang_rom[ 829] = 36'h88dccbb32;
        ang_rom[ 830] = 36'h8926cbe1d;
        ang_rom[ 831] = 36'h89720c107;
        ang_rom[ 832] = 36'h89be4c3ef;
        ang_rom[ 833] = 36'h8a0bcc6d5;
        ang_rom[ 834] = 36'h8a5a8c9b9;
        ang_rom[ 835] = 36'h8aaa4cc9c;
        ang_rom[ 836] = 36'h8afb4cf7c;
        ang_rom[ 837] = 36'h8b4d4d25a;
        ang_rom[ 838] = 36'h8ba08d536;
        ang_rom[ 839] = 36'h8bf4cd810;
        ang_rom[ 840] = 36'h8c4a0dae9;
        ang_rom[ 841] = 36'h8ca08ddbe;
        ang_rom[ 842] = 36'h8cf84e092;
        ang_rom[ 843] = 36'h8d510e364;
        ang_rom[ 844] = 36'h8daace633;
        ang_rom[ 845] = 36'h8e05ce901;
        ang_rom[ 846] = 36'h8e61cebcc;
        ang_rom[ 847] = 36'h8ebf0ee94;
        ang_rom[ 848] = 36'h8f1d4f15b;
        ang_rom[ 849] = 36'h8f7c8f41f;
        ang_rom[ 850] = 36'h8fdd0f6e1;
        ang_rom[ 851] = 36'h903e8f9a0;
        ang_rom[ 852] = 36'h90a10fc5d;
        ang_rom[ 853] = 36'h9104cff18;
        ang_rom[ 854] = 36'h9169501d0;
        ang_rom[ 855] = 36'h91cf10485;
        ang_rom[ 856] = 36'h923610738;
        ang_rom[ 857] = 36'h929dd09e9;
        ang_rom[ 858] = 36'h9306d0c97;
        ang_rom[ 859] = 36'h9370d0f42;
        ang_rom[ 860] = 36'h93dbd11eb;
        ang_rom[ 861] = 36'h944811491;
        ang_rom[ 862] = 36'h94b511735;
        ang_rom[ 863] = 36'h9523519d6;
        ang_rom[ 864] = 36'h959291c74;
        ang_rom[ 865] = 36'h960291f0f;
        ang_rom[ 866] = 36'h9673d21a8;
        ang_rom[ 867] = 36'h96e61243d;
        ang_rom[ 868] = 36'h9759926d0;
        ang_rom[ 869] = 36'h97cdd2960;
        ang_rom[ 870] = 36'h984312bee;
        ang_rom[ 871] = 36'h98b952e78;
        ang_rom[ 872] = 36'h9930930ff;
        ang_rom[ 873] = 36'h99a8d3384;
        ang_rom[ 874] = 36'h9a2213606;
        ang_rom[ 875] = 36'h9a9c53884;
        ang_rom[ 876] = 36'h9b1793b00;
        ang_rom[ 877] = 36'h9b93d3d78;
        ang_rom[ 878] = 36'h9c10d3fee;
        ang_rom[ 879] = 36'h9c8f14260;
        ang_rom[ 880] = 36'h9d0e144cf;
        ang_rom[ 881] = 36'h9d8e1473b;
        ang_rom[ 882] = 36'h9e0f149a4;
        ang_rom[ 883] = 36'h9e9114c0a;
        ang_rom[ 884] = 36'h9f13d4e6d;
        ang_rom[ 885] = 36'h9f97950cc;
        ang_rom[ 886] = 36'ha01c55328;
        ang_rom[ 887] = 36'ha0a215581;
        ang_rom[ 888] = 36'ha128957d7;
        ang_rom[ 889] = 36'ha1b015a29;
        ang_rom[ 890] = 36'ha23895c78;
        ang_rom[ 891] = 36'ha2c1d5ec3;
        ang_rom[ 892] = 36'ha34bd610b;
        ang_rom[ 893] = 36'ha3d716350;
        ang_rom[ 894] = 36'ha46316592;
        ang_rom[ 895] = 36'ha4efd67cf;
        ang_rom[ 896] = 36'ha57d96a0a;
        ang_rom[ 897] = 36'ha60c56c41;
        ang_rom[ 898] = 36'ha69b96e74;
        ang_rom[ 899] = 36'ha72c170a4;
        ang_rom[ 900] = 36'ha7bd572d1;
        ang_rom[ 901] = 36'ha84f574f9;
        ang_rom[ 902] = 36'ha8e21771e;
        ang_rom[ 903] = 36'ha975d7940;
        ang_rom[ 904] = 36'haa0a57b5e;
        ang_rom[ 905] = 36'haa9fd7d78;
        ang_rom[ 906] = 36'hab3617f8f;
        ang_rom[ 907] = 36'habcd181a2;
        ang_rom[ 908] = 36'hac64d83b1;
        ang_rom[ 909] = 36'hacfd985bc;
        ang_rom[ 910] = 36'had97187c4;
        ang_rom[ 911] = 36'hae31589c8;
        ang_rom[ 912] = 36'haecc58bc8;
        ang_rom[ 913] = 36'haf6818dc4;
        ang_rom[ 914] = 36'hb00498fbd;
        ang_rom[ 915] = 36'hb0a2191b1;
        ang_rom[ 916] = 36'hb140193a2;
        ang_rom[ 917] = 36'hb1df1958f;
        ang_rom[ 918] = 36'hb27e99778;
        ang_rom[ 919] = 36'hb31f1995d;
        ang_rom[ 920] = 36'hb3c059b3e;
        ang_rom[ 921] = 36'hb46219d1b;
        ang_rom[ 922] = 36'hb50499ef4;
        ang_rom[ 923] = 36'hb5a81a0c9;
        ang_rom[ 924] = 36'hb64c1a29a;
        ang_rom[ 925] = 36'hb6f0da468;
        ang_rom[ 926] = 36'hb7961a631;
        ang_rom[ 927] = 36'hb83c5a7f6;
        ang_rom[ 928] = 36'hb8e31a9b6;
        ang_rom[ 929] = 36'hb98a9ab73;
        ang_rom[ 930] = 36'hba32dad2c;
        ang_rom[ 931] = 36'hbadbdaee0;
        ang_rom[ 932] = 36'hbb855b091;
        ang_rom[ 933] = 36'hbc2f9b23d;
        ang_rom[ 934] = 36'hbcda5b3e5;
        ang_rom[ 935] = 36'hbd85db589;
        ang_rom[ 936] = 36'hbe321b728;
        ang_rom[ 937] = 36'hbededb8c4;
        ang_rom[ 938] = 36'hbf8c1ba5b;
        ang_rom[ 939] = 36'hc03a1bbed;
        ang_rom[ 940] = 36'hc0e8dbd7c;
        ang_rom[ 941] = 36'hc1981bf06;
        ang_rom[ 942] = 36'hc247dc08c;
        ang_rom[ 943] = 36'hc2f85c20e;
        ang_rom[ 944] = 36'hc3a95c38b;
        ang_rom[ 945] = 36'hc45b1c504;
        ang_rom[ 946] = 36'hc50d1c679;
        ang_rom[ 947] = 36'hc5bfdc7e9;
        ang_rom[ 948] = 36'hc6735c955;
        ang_rom[ 949] = 36'hc7271cabc;
        ang_rom[ 950] = 36'hc7db9cc1f;
        ang_rom[ 951] = 36'hc8909cd7e;
        ang_rom[ 952] = 36'hc945dced8;
        ang_rom[ 953] = 36'hc9fc1d02d;
        ang_rom[ 954] = 36'hcab29d17e;
        ang_rom[ 955] = 36'hcb699d2cb;
        ang_rom[ 956] = 36'hcc211d413;
        ang_rom[ 957] = 36'hccd91d557;
        ang_rom[ 958] = 36'hcd91dd696;
        ang_rom[ 959] = 36'hce4add7d1;
        ang_rom[ 960] = 36'hcf045d907;
        ang_rom[ 961] = 36'hcfbe5da38;
        ang_rom[ 962] = 36'hd078ddb65;
        ang_rom[ 963] = 36'hd1339dc8d;
        ang_rom[ 964] = 36'hd1ef1ddb1;
        ang_rom[ 965] = 36'hd2aadded0;
        ang_rom[ 966] = 36'hd3671dfeb;
        ang_rom[ 967] = 36'hd423de101;
        ang_rom[ 968] = 36'hd4e0de212;
        ang_rom[ 969] = 36'hd59e5e31f;
        ang_rom[ 970] = 36'hd65c5e427;
        ang_rom[ 971] = 36'hd71a9e52a;
        ang_rom[ 972] = 36'hd7d95e629;
        ang_rom[ 973] = 36'hd8989e722;
        ang_rom[ 974] = 36'hd957de818;
        ang_rom[ 975] = 36'hda17de908;
        ang_rom[ 976] = 36'hdad81e9f4;
        ang_rom[ 977] = 36'hdb989eadb;
        ang_rom[ 978] = 36'hdc599ebbe;
        ang_rom[ 979] = 36'hdd1adec9b;
        ang_rom[ 980] = 36'hdddc5ed74;
        ang_rom[ 981] = 36'hde9e5ee48;
        ang_rom[ 982] = 36'hdf609ef18;
        ang_rom[ 983] = 36'he0235efe2;
        ang_rom[ 984] = 36'he0e61f0a8;
        ang_rom[ 985] = 36'he1a95f169;
        ang_rom[ 986] = 36'he26cdf225;
        ang_rom[ 987] = 36'he3309f2dd;
        ang_rom[ 988] = 36'he3f49f38f;
        ang_rom[ 989] = 36'he4b8df43d;
        ang_rom[ 990] = 36'he57d5f4e6;
        ang_rom[ 991] = 36'he6425f58a;
        ang_rom[ 992] = 36'he7075f629;
        ang_rom[ 993] = 36'he7cc9f6c4;
        ang_rom[ 994] = 36'he8925f75a;
        ang_rom[ 995] = 36'he9581f7ea;
        ang_rom[ 996] = 36'hea1e1f876;
        ang_rom[ 997] = 36'heae45f8fd;
        ang_rom[ 998] = 36'hebaa9f980;
        ang_rom[ 999] = 36'hec715f9fd;
        ang_rom[1000] = 36'hed381fa75;
        ang_rom[1001] = 36'hedff1fae9;
        ang_rom[1002] = 36'heec61fb58;
        ang_rom[1003] = 36'hef8d5fbc1;
        ang_rom[1004] = 36'hf054dfc26;
        ang_rom[1005] = 36'hf11c9fc86;
        ang_rom[1006] = 36'hf1e45fce1;
        ang_rom[1007] = 36'hf2ac5fd38;
        ang_rom[1008] = 36'hf3745fd89;
        ang_rom[1009] = 36'hf43c5fdd5;
        ang_rom[1010] = 36'hf5049fe1d;
        ang_rom[1011] = 36'hf5cd1fe5f;
        ang_rom[1012] = 36'hf6959fe9d;
        ang_rom[1013] = 36'hf75e1fed6;
        ang_rom[1014] = 36'hf826dff09;
        ang_rom[1015] = 36'hf8ef5ff38;
        ang_rom[1016] = 36'hf9b85ff62;
        ang_rom[1017] = 36'hfa811ff87;
        ang_rom[1018] = 36'hfb4a1ffa7;
        ang_rom[1019] = 36'hfc12dffc2;
        ang_rom[1020] = 36'hfcdbdffd9;
        ang_rom[1021] = 36'hfda4dffea;
        ang_rom[1022] = 36'hfe6e1fff6;
        ang_rom[1023] = 36'hff371fffe;
    end
    reg [35:0] ang_q;
    always @(posedge clk) begin
        exp_lo <= exp_pair[exp_addr[7:0]][17:0];
        exp_hi <= exp_pair[exp_addr[7:0]][35:18];
        ang_q  <= ang_rom[ang_addr];
    end
    assign cos_q = ang_q[17:0];
    assign sin_q = ang_q[35:18];
endmodule
