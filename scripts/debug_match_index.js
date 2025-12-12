// debug_match_index.js
import admin from 'firebase-admin';
import { URL } from 'url';

if (!process.env.GOOGLE_APPLICATION_CREDENTIALS) {
  console.error('Set GOOGLE_APPLICATION_CREDENTIALS before running.');
  process.exit(1);
}
admin.initializeApp();
const db = admin.firestore();

function parseFirebaseStoragePathFromUrl(urlStr) {
  try {
    const url = new URL(urlStr);
    const parts = url.pathname.split('/o/');
    if (parts.length < 2) return null;
    const encodedPath = parts[1].split('?')[0];
    return decodeURIComponent(encodedPath);
  } catch (e) {
    return null;
  }
}

async function showIndex(sampleN = 50) {
  console.log('=== Index keys from collection imagens ===');
  const keys = [];
  const snap = await db.collection('imagens').get();
  snap.forEach(doc => {
    const d = doc.data();
    if (d.storage_path) keys.push(d.storage_path);
    if (Array.isArray(d.paths)) d.paths.forEach(p => keys.push(p));
    // also list filenames
    if (d.storage_path) keys.push(d.storage_path.split('/').pop());
  });
  // unique
  const uniq = [...new Set(keys)];
  console.log(`Total keys indexed (unique sample): ${uniq.length}`);
  console.log(uniq.slice(0, sampleN).join('\n'));
  console.log('--- end index ---\n');
}

async function sampleJornadas(limit = 10) {
  console.log('=== Sample jornadas with imagens field ===');
  const snap = await db.collection('jornadas').orderBy('__name__').limit(limit).get();
  let i=0;
  for (const doc of snap.docs) {
    i++;
    const id = doc.id;
    const data = doc.data();
    const imgs = data.imagens || data.imagens_original || null;
    console.log(`\n>> jornada id: ${id}`);
    if (!imgs) { console.log('  no imagens field'); continue; }
    for (const role of Object.keys(imgs)) {
      const val = imgs[role];
      if (!val) continue;
      const entries = Array.isArray(val) ? val : [val];
      for (const url of entries) {
        const storagePath = parseFirebaseStoragePathFromUrl(url);
        console.log(`  role=${role} url=${String(url).slice(0,200)}`);
        console.log(`    parsed storage_path => ${storagePath}`);
        // also print filename
        try {
          const filename = storagePath ? storagePath.split('/').pop() : (new URL(url).pathname.split('/').pop());
          console.log(`    filename => ${filename}`);
        } catch (e) { /* ignore */ }
      }
    }
    if (i >= limit) break;
  }
}

(async () => {
  try {
    await showIndex(200);
    await sampleJornadas(12);
    process.exit(0);
  } catch (e) {
    console.error(e);
    process.exit(2);
  }
})();
