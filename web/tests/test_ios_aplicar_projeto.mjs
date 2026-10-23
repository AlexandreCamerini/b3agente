// Guardiao de scripts/ios-aplicar-projeto.sh (e, abaixo, do ios-bump-build.sh).
//
// POR QUE EXISTE (incidente de 2026-10-22): web/ios/ e gitignored; o template do
// Capacitor 8 nasce sem DEVELOPMENT_TEAM, sem CODE_SIGN_ENTITLEMENTS e sem
// PrivacyInfo, com build 1 / versao 1.0. Tudo foi refeito a mao em python, e o
// ios-bump-build.sh calculou 0->1 em silencio num pbxproj sem PBXNativeTarget.
// Este teste trava: aplicacao correta, idempotencia, falha acionavel em projeto
// corrompido, bundle id intocado. Guardiao nao se apaga - reversao deliberada
// atualiza o teste com nota.
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

if (process.platform !== 'darwin' || !fs.existsSync('/usr/libexec/PlistBuddy')) {
  console.log('SKIP test_ios_aplicar_projeto (precisa de macOS + PlistBuddy)');
  process.exit(0);
}

const WEB = process.cwd();
const REPO = path.resolve(WEB, '..');
const FIX = path.join(WEB, 'tests', 'fixtures', 'ios-projeto');
const APLICAR = path.join(REPO, 'scripts', 'ios-aplicar-projeto.sh');
const BUMP = path.join(REPO, 'scripts', 'ios-bump-build.sh');
const VERSAO = path.join(REPO, 'resources', 'ios', 'versao.env');
const PRIV = path.join(REPO, 'resources', 'ios', 'PrivacyInfo.xcprivacy');

const parseEnv = (f) => Object.fromEntries(fs.readFileSync(f, 'utf8').split('\n')
  .filter((l) => /^[A-Z_]+=/.test(l)).map((l) => l.split('=')));
const V = parseEnv(VERSAO);
const versaoReal = fs.readFileSync(VERSAO, 'utf8');

const tmps = [];
function novo() {
  const d = fs.mkdtempSync(path.join(os.tmpdir(), 'iosfix-'));
  tmps.push(d);
  fs.cpSync(FIX, d, { recursive: true });
  return d;
}
const pbxOf = (d) => path.join(d, 'App', 'App.xcodeproj', 'project.pbxproj');
const plistOf = (d) => path.join(d, 'App', 'App', 'Info.plist');
const sh = (script, args) => spawnSync('bash', [script, ...args], { cwd: WEB, encoding: 'utf8' });
const aplicar = (d, extra = []) => sh(APLICAR, ['--ios-dir', d, '--sem-verificar', ...extra]);
const count = (s, sub) => s.split(sub).length - 1;
const rd = (f) => fs.readFileSync(f);

try {
  // T1 + T2 + T3 + T4
  {
    const d = novo();
    const antes = fs.readFileSync(pbxOf(d), 'utf8');
    const r = aplicar(d);
    assert.equal(r.status, 0, r.stdout + r.stderr);
    const p = fs.readFileSync(pbxOf(d), 'utf8');
    assert.equal(count(p, '\t\t\t\tDEVELOPMENT_TEAM = LC65399YC9;\n'), 2, 'T1 team');
    assert.equal(count(p, '\t\t\t\tCODE_SIGN_ENTITLEMENTS = App/App.entitlements;\n'), 2, 'T1 entitlements');
    assert.equal(count(p, `\t\t\t\tCURRENT_PROJECT_VERSION = ${V.CURRENT_PROJECT_VERSION};\n`), 2, 'T1 build');
    assert.equal(count(p, `\t\t\t\tMARKETING_VERSION = ${V.MARKETING_VERSION};\n`), 2, 'T1 versao');
    assert.equal(count(p, 'CURRENT_PROJECT_VERSION = 1;'), 0);
    assert.equal(count(p, 'MARKETING_VERSION = 1.0;'), 0);
    assert.equal(count(p, 'DEVELOPMENT_TEAM'), 2, 'configs do PROJETO nao ganham time');
    // T2
    assert.equal(count(p, '465BE8AF305B68D80081DCF5 /* PrivacyInfo.xcprivacy in Resources */'), 2);
    assert.equal(count(p, '465BE8AE305B68D80081DCF5 /* PrivacyInfo.xcprivacy */'), 3);
    const cp = path.join(d, 'App', 'App', 'PrivacyInfo.xcprivacy');
    assert.ok(fs.existsSync(cp) && rd(cp).equals(rd(PRIV)), 'T2 arquivo copiado');
    // T3
    const pl = fs.readFileSync(plistOf(d), 'utf8');
    assert.match(pl, /<key>CFBundleName<\/key>\s*<string>Boris\+<\/string>/);
    assert.match(pl, /<key>CFBundleDisplayName<\/key>\s*<string>Boris\+<\/string>/);
    // T4
    const bid = (s) => s.match(/PRODUCT_BUNDLE_IDENTIFIER = [^;]*;/g);
    assert.deepEqual(bid(p), bid(antes));
    assert.ok(bid(p).every((l) => l.includes('com.alexandrecamerini.bolsia')));
    // T5 idempotencia
    const pbx1 = rd(pbxOf(d)), pl1 = rd(plistOf(d));
    const r2 = aplicar(d);
    assert.equal(r2.status, 0, r2.stdout + r2.stderr);
    assert.ok(rd(pbxOf(d)).equals(pbx1), 'T5 pbxproj');
    assert.ok(rd(plistOf(d)).equals(pl1), 'T5 plist');
  }
  // T6 sem PBXNativeTarget
  {
    const d = novo();
    const f = pbxOf(d);
    const s = fs.readFileSync(f, 'utf8').replace(/\/\* Begin PBXNativeTarget section \*\/[\s\S]*?\/\* End PBXNativeTarget section \*\/\n/, '');
    fs.writeFileSync(f, s);
    const antes = rd(f);
    const r = aplicar(d);
    assert.notEqual(r.status, 0);
    assert.ok((r.stdout + r.stderr).includes('--recriar-ios'));
    assert.ok(rd(f).equals(antes), 'T6 intocado');
  }
  // T7 PrivacyInfo ja referenciado com outros IDs
  {
    const d = novo();
    const f = pbxOf(d);
    let s = fs.readFileSync(f, 'utf8');
    const A = 'A'.repeat(24), B = 'B'.repeat(24);
    s = s.replace('/* End PBXBuildFile section */', `\t\t${B} /* PrivacyInfo.xcprivacy in Resources */ = {isa = PBXBuildFile; fileRef = ${A} /* PrivacyInfo.xcprivacy */; };\n/* End PBXBuildFile section */`)
      .replace('/* End PBXFileReference section */', `\t\t${A} /* PrivacyInfo.xcprivacy */ = {isa = PBXFileReference; lastKnownFileType = text.xml; path = PrivacyInfo.xcprivacy; sourceTree = "<group>"; };\n/* End PBXFileReference section */`)
      .replace('\t\t\t\t504EC3131FED79650016851F /* Info.plist */,\n', `\t\t\t\t504EC3131FED79650016851F /* Info.plist */,\n\t\t\t\t${A} /* PrivacyInfo.xcprivacy */,\n`)
      .replace('\t\t\t\t504EC3121FED79650016851F /* LaunchScreen.storyboard in Resources */,\n', `\t\t\t\t504EC3121FED79650016851F /* LaunchScreen.storyboard in Resources */,\n\t\t\t\t${B} /* PrivacyInfo.xcprivacy in Resources */,\n`);
    fs.writeFileSync(f, s);
    const r = aplicar(d);
    assert.equal(r.status, 0, r.stdout + r.stderr);
    assert.equal(count(fs.readFileSync(f, 'utf8'), '465BE8A'), 0, 'T7 nao duplica');
  }
  // T8 versao.env invalido
  {
    const d = novo();
    const ve = path.join(d, 'versao.env');
    fs.writeFileSync(ve, 'MARKETING_VERSION=2.0\nCURRENT_PROJECT_VERSION=abc\n');
    const antes = rd(pbxOf(d));
    const r = aplicar(d, ['--versao-file', ve]);
    assert.notEqual(r.status, 0);
    assert.ok(rd(pbxOf(d)).equals(antes));
  }
  // T9 ios-dir inexistente
  {
    const r = aplicar(path.join(os.tmpdir(), 'nao-existe-ios-xyz'));
    assert.notEqual(r.status, 0);
    assert.match(r.stderr, /nao existe/);
  }

  // ---- B/S: ios-bump-build.sh e ligacao dos scripts (preenchido na Task 2) ----
  if (fs.existsSync(BUMP)) {
    const prep = () => {
      const d = novo();
      assert.equal(aplicar(d).status, 0);
      const ve = path.join(d, 'versao.env');
      fs.writeFileSync(ve, versaoReal);
      return [d, ve];
    };
    // B1
    {
      const [d, ve] = prep();
      const r = sh(BUMP, ['--ios-dir', d, '--versao-file', ve, '--sem-verificar']);
      assert.equal(r.status, 0, r.stdout + r.stderr);
      const n = Number(V.CURRENT_PROJECT_VERSION) + 1;
      assert.match(fs.readFileSync(ve, 'utf8'), new RegExp(`^CURRENT_PROJECT_VERSION=${n}$`, 'm'));
      assert.equal(count(fs.readFileSync(pbxOf(d), 'utf8'), `CURRENT_PROJECT_VERSION = ${n};`), 2);
    }
    // B2
    {
      const [d, ve] = prep();
      const r = sh(BUMP, ['--ios-dir', d, '--versao-file', ve, '--sem-verificar', V.CURRENT_PROJECT_VERSION]);
      assert.notEqual(r.status, 0);
      assert.equal(fs.readFileSync(ve, 'utf8'), versaoReal);
    }
    // B3 sem CURRENT_PROJECT_VERSION
    {
      const [d, ve] = prep();
      const f = pbxOf(d);
      fs.writeFileSync(f, fs.readFileSync(f, 'utf8').replace(/\t+CURRENT_PROJECT_VERSION = \d+;\n/g, ''));
      const r = sh(BUMP, ['--ios-dir', d, '--versao-file', ve, '--sem-verificar']);
      assert.notEqual(r.status, 0);
      assert.equal(fs.readFileSync(ve, 'utf8'), versaoReal);
    }
    // B4 sem PBXNativeTarget
    {
      const [d, ve] = prep();
      const f = pbxOf(d);
      fs.writeFileSync(f, fs.readFileSync(f, 'utf8').replace(/\/\* Begin PBXNativeTarget section \*\/[\s\S]*?\/\* End PBXNativeTarget section \*\/\n/, ''));
      const r = sh(BUMP, ['--ios-dir', d, '--versao-file', ve, '--sem-verificar']);
      assert.notEqual(r.status, 0);
      assert.ok((r.stdout + r.stderr).includes('--recriar-ios'));
      assert.equal(fs.readFileSync(ve, 'utf8'), versaoReal);
    }
  }
  // S1/S2 estaticos: ligacao dos scripts ao novo fluxo
  {
    const ler = (n) => fs.readFileSync(path.join(REPO, 'scripts', n), 'utf8');
    const vivo = (n) => ler(n).split('\n').filter((l) => !/^\s*#/.test(l));
    const idx = (n, re) => vivo(n).findIndex((l) => re.test(l));
    for (const n of ['instalar-iphone.sh', 'setup-ios.sh', 'ios-testflight.sh']) {
      assert.ok(idx(n, /ios-aplicar-projeto\.sh/) >= 0, `S1 ${n} chama o aplicar`);
    }
    assert.ok(!/arraste/i.test(ler('ios-testflight.sh')), 'S1 sem instrucao manual');
    assert.ok(ler('ios-bump-build.sh').includes('versao.env'), 'S1 bump usa versao.env');
    assert.ok(!ler('ios-bump-build.sh').includes('|| echo 0'), 'S1 sem 0->1 silencioso');
    // S2 ordem
    const ap = idx('instalar-iphone.sh', /ios-aplicar-projeto\.sh/);
    assert.ok(ap > idx('instalar-iphone.sh', /cap sync ios/), 'S2 depois do cap sync');
    assert.ok(ap > idx('instalar-iphone.sh', /ios-patch-appdelegate\.sh/), 'S2 depois do patch-appdelegate');
    const sa = idx('setup-ios.sh', /ios-aplicar-projeto\.sh/);
    assert.ok(sa > idx('setup-ios.sh', /ios-restaurar-entitlements\.sh/), 'S2 setup: depois dos entitlements');
    assert.ok(sa > idx('setup-ios.sh', /add ios/), 'S2 setup: depois do cap add');
  }
  // o teste nunca escreve no versao.env real
  assert.equal(fs.readFileSync(VERSAO, 'utf8'), versaoReal);
  console.log('OK test_ios_aplicar_projeto');
} finally {
  for (const d of tmps) fs.rmSync(d, { recursive: true, force: true });
}
