// migrate_link_images.js
// ECMAScript module. Node 18+ recommended.
// Dependencies: firebase-admin, yargs, csv-writer
//
// Install:
// npm install firebase-admin yargs csv-writer
//
// Usage examples:
//  node migrate_link_images.js --dry-run
//  node migrate_link_images.js --confirm-high
//  node migrate_link_images.js --confirm-threshold 0.75

import admin from 'firebase-admin';
import { createObjectCsvWriter } from 'csv-writer';
import yargs from 'yargs';
import { hideBin } from 'yargs/helpers';
import fs from 'fs';
import path from 'path';
import { URL } from 'url';

const argv = yargs(hideBin(process.argv))
  .option('dry-run', { type: 'boolean', default: true, describe: 'Do not write changes to Firestore' })
  .option('confirm-high', { type: 'boolean', default: false, describe: 'Write only high-confidence matches (>= 0.90)' })
  .option('confirm-threshold', { type: 'number', default: null, describe: 'Write matches with confidence >= threshold (0-1)' })
  .option('page-size', { type: 'number', default: 200, describe: 'Documents per page read from Firestore' })
  .option('batch-size', { type: 'number', default: 200, describe: 'Write batch size (<= 500)' })
  .option('report-file', { type: 'string', default: 'migrations_report.csv', describe: 'CSV report path' })
  .help()
  .argv;

const DRY = argv['dry-run'];
const CONFIRM_HIGH = argv['confirm-high'];
const CONFIRM_THRESHOLD = typeof argv['confirm-threshold'] === 'number' ? argv['confirm-threshold'] : null;
const PAGE_SIZE = parseInt(argv['page-size'], 10);
const BATCH_SIZE = Math.min(500, parseInt(argv['batch-size'], 10));
const REPORT_FILE = argv['report-file'];

if (!process.env.GOOGLE_APPLICATION_CREDENTIALS) {
  console.error('ERROR: environment variable GOOGLE_APPLICATION_CREDENTIALS not set.');
  console.error('Set it to your service account JSON path.');
  process.exit(1);
}

// initialize firebase-admin
admin.initializeApp();
const db = admin.firestore();

// normalizeFilename aprimorada — cole esta função no lugar da atual
function normalizeFilename(name) {
  if (!name) return '';
  // remove query params
  name = String(name).split('?')[0];
  // remove extension
  const dot = name.lastIndexOf('.');
  let base = dot > 0 ? name.slice(0, dot) : name;
  // split tokens por _ - espaço
  const tokens = base.split(/[_\-\s]+/);
  function looksLikeHashOrTimestamp(tok) {
    if (!tok) return false;
    // hex-like (6+ hex chars) OR numeric long (6+ digits)
    if (/^[0-9a-fA-F]{6,}$/.test(tok)) return true;
    if (/^\d{6,}$/.test(tok)) return true;
    return false;
  }
  // remove tokens finais que pareçam hash/timestamp
  let end = tokens.length;
  while (end > 0 && looksLikeHashOrTimestamp(tokens[end - 1])) {
    end--;
  }
  const cleaned = tokens.slice(0, end).join('_').toLowerCase().trim();
  // keep underscores (for 'durante_0'), normalize other non-alnum to space
  const normalized = cleaned.replace(/[^a-z0-9_]+/g, ' ').replace(/\s+/g, ' ').trim();
  return normalized;
}



// levenshtein similarity ratio
function levenshteinSimilarity(a = '', b = '') {
  if (a === b) return 1;
  const la = a.length, lb = b.length;
  if (la === 0 || lb === 0) return 0;
  const dp = Array(la + 1).fill(null).map(() => Array(lb + 1).fill(0));
  for (let i = 0; i <= la; i++) dp[i][0] = i;
  for (let j = 0; j <= lb; j++) dp[0][j] = j;
  for (let i = 1; i <= la; i++) {
    for (let j = 1; j <= lb; j++) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      dp[i][j] = Math.min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost);
    }
  }
  const dist = dp[la][lb];
  return 1 - (dist / Math.max(la, lb));
}

// parse Firebase storage path from download URL
function parseFirebaseStoragePathFromUrl(urlStr) {
  try {
    const url = new URL(urlStr);
    const parts = url.pathname.split('/o/');
    if (parts.length < 2) return null;
    const after = parts[1];
    const encodedPath = after.split('?')[0];
    const decoded = decodeURIComponent(encodedPath);
    return decoded; // e.g., "jornadas/1747958931209/depois.jpg"
  } catch (e) {
    return null;
  }
}

async function buildImagesIndex() {
  console.log("Indexing 'imagens' collection (expanded keys)...");
  const index = new Map(); // key -> { id, doc, keyType }
  const normIndex = new Map(); // normalized filename -> [{id, doc, keyType, origFilename}]
  const snapshot = await db.collection('imagens').get();
  snapshot.forEach(doc => {
    const data = doc.data();
    const id = doc.id;

// Exemplo de trecho dentro do loop snapshot.forEach(doc => { ... })
if (data.storage_path) {
  index.set(data.storage_path, { id, doc: data, keyType: 'storage_path' });
  const fname = data.storage_path.split('/').pop();
  index.set(fname, { id, doc: data, keyType: 'filename' });
  const norm = normalizeFilename(fname);
  if (!normIndex.has(norm)) normIndex.set(norm, []);
  normIndex.get(norm).push({ id, doc: data, keyType: 'norm_filename', origFilename: fname });
}

if (Array.isArray(data.paths)) {
  data.paths.forEach(p => {
    index.set(p, { id, doc: data, keyType: 'paths[]' });
    const fname = p.split('/').pop();
    index.set(fname, { id, doc: data, keyType: 'filename' });
    const norm = normalizeFilename(fname);
    if (!normIndex.has(norm)) normIndex.set(norm, []);
    normIndex.get(norm).push({ id, doc: data, keyType: 'norm_filename', origFilename: fname });
  });
}



    // fallback index by sha256
    if (data.sha256) {
      index.set(data.sha256, { id, doc: data, keyType: 'sha256' });
    }
  });

  console.log(`Indexed keys: ${index.size}. Norm-filename buckets: ${normIndex.size}`);
  return { index, normIndex };
}

function matchImageUrlToIndex(url, indexObj) {
  const { index, normIndex } = indexObj;
  const storagePath = parseFirebaseStoragePathFromUrl(url);
  let filename = null;
  try {
    filename = storagePath ? storagePath.split('/').pop() : (new URL(url).pathname.split('/').pop());
  } catch (e) {
    filename = null;
  }
  const normalized = normalizeFilename(filename || '');

  // 1) exact storage_path
  if (storagePath && index.has(storagePath)) {
    return { hit: index.get(storagePath), confidence: 1.0, reason: 'storage_path_exact', key: storagePath };
  }

  // 2) exact filename key
  if (filename && index.has(filename)) {
    return { hit: index.get(filename), confidence: 0.95, reason: 'filename_exact', key: filename };
  }

  // 3) normalized filename exact bucket
  if (normalized && normIndex.has(normalized)) {
    const hits = normIndex.get(normalized);
    if (hits.length === 1) {
      return { hit: { id: hits[0].id, doc: hits[0].doc, keyType: 'norm_filename' }, confidence: 0.92, reason: 'norm_filename_single', key: hits[0].origFilename };
    } else {
      // choose best by levenshtein against original filenames
      let best = null;
      for (const h of hits) {
        const candNorm = normalizeFilename(h.origFilename);
        const sim = levenshteinSimilarity(candNorm, normalized);
        if (!best || sim > best.sim) best = { h, sim };
      }
      if (best) {
        const conf = 0.85 * best.sim + 0.07; // scale
        return { hit: { id: best.h.id, doc: best.h.doc, keyType: 'norm_filename_best' }, confidence: Math.min(0.9, conf), reason: 'norm_filename_bucket_best', key: best.h.origFilename };
      }
    }
  }

  // 4) fuzzy scan (limited)
  let best = null;
  let scanned = 0;
  for (const [k, v] of index.entries()) {
    // prefer filename only entries (no '/')
    if (k.includes('/')) continue;
    const sim = levenshteinSimilarity(normalizeFilename(k), normalized);
    if (!best || sim > best.sim) best = { k, v, sim };
    scanned++;
    if (scanned > 300) break; // cap
  }
  if (best && best.sim >= 0.75) {
    const conf = 0.55 + (best.sim * 0.4);
    return { hit: best.v, confidence: conf, reason: `fuzzy_best_sim_${best.sim.toFixed(2)}`, key: best.k };
  }

  // no match
  return null;
}

function pathSafeString(s) {
  return s ? String(s).replace(/[\r\n]+/g, ' ') : '';
}

async function migrateBatch(indexObj, { pageSize = PAGE_SIZE, batchSize = BATCH_SIZE } = {}) {
  console.log('Starting migration pass (dry-run=%s) ...', DRY);
  const csvWriter = createObjectCsvWriter({
    path: REPORT_FILE,
    header: [
      { id: 'jornada_id', title: 'jornada_id' },
      { id: 'matched_roles', title: 'matched_roles' },
      { id: 'missing_roles', title: 'missing_roles' },
      { id: 'details', title: 'details' },
      { id: 'status_images', title: 'status_images' },
      { id: 'confidence_summary', title: 'confidence_summary' }
    ],
    append: false
  });

  const rows = [];
  let lastDoc = null;
  let processed = 0, proposed = 0, succeeded = 0, failed = 0, skipped = 0;

  while (true) {
    let q = db.collection('jornadas').orderBy('__name__').limit(pageSize);
    if (lastDoc) q = q.startAfter(lastDoc);
    const snap = await q.get();
    if (snap.empty) break;

    const batchWrites = [];
    let batchOps = 0;

    for (const doc of snap.docs) {
      processed++;
      lastDoc = doc;
      const id = doc.id;
      const data = doc.data();
      const imagensField = data.imagens || data.imagens_original || null;

      if (!imagensField) {
        rows.push({
          jornada_id: id,
          matched_roles: '',
          missing_roles: 'all',
          details: 'no imagens field',
          status_images: 'missing',
          confidence_summary: ''
        });
        skipped++;
        continue;
      }

      const roles = ['antes', 'durante', 'depois'];
      const imagesRefs = {};
      const missing = [];
      const details = [];
      let anyMatch = false;

      for (const role of roles) {
        const oldVal = imagensField[role];
        if (!oldVal) {
          missing.push(role);
          continue;
        }
        const entries = Array.isArray(oldVal) ? oldVal : [oldVal];
        // try each entry
        let matched = null;
        for (const url of entries) {
          const match = matchImageUrlToIndex(url, indexObj);
          if (match) {
            // take first match with highest confidence in this entry list
            if (!matched || match.confidence > matched.confidence) matched = match;
          }
        }
        if (matched) {
          anyMatch = true;
          const hit = matched.hit;
          const storedKey = matched.key || null;
          const docData = hit.doc || hit; // compatibility
          imagesRefs[role] = {
            imagens_doc: hit.id || hit.doc?.id || hit.doc?.documentId || null,
            storage_path: storedKey,
            thumb: docData?.thumbs?.[role] ?? (docData?.images?.[role]?.thumb ?? null),
            original: entries
          };
          details.push(`${role}=>doc:${hit.id || hit.doc?.id || '(unknown)'} conf:${matched.confidence.toFixed(2)} reason:${matched.reason}`);
        } else {
          missing.push(role);
          details.push(`${role}=>MISSING`);
        }
      }

      // compute confidence summary
      const confidences = details.map(d => {
        const m = d.match(/conf:(\d\.\d+)/);
        return m ? parseFloat(m[1]) : null;
      }).filter(Boolean);
      const avgConf = confidences.length ? (confidences.reduce((a,b)=>a+b,0)/confidences.length) : 0;

      const statusImages = missing.length === 0 ? 'linked' : (anyMatch ? 'partial_linked' : 'missing');

      rows.push({
        jornada_id: id,
        matched_roles: Object.keys(imagesRefs).join(';'),
        missing_roles: missing.join(';'),
        details: details.join(' | '),
        status_images: statusImages,
        confidence_summary: avgConf.toFixed(3)
      });

      // Decide whether to propose write
      let shouldWrite = false;
      if (!DRY) {
        // if explicit threshold present
        if (CONFIRM_THRESHOLD !== null) {
          if (avgConf >= CONFIRM_THRESHOLD) shouldWrite = true;
        } else if (CONFIRM_HIGH) {
          if (avgConf >= 0.90) shouldWrite = true;
        } else {
          // default: do not write unless explicitly asked (safe)
          shouldWrite = false;
        }
      }

      if (shouldWrite) {
        proposed++;
        const updates = {};
        if (!data.imagens_original) updates['imagens_original'] = imagensField;
        updates['images_refs'] = imagesRefs;
        updates['status_images'] = statusImages;
        // batch write
        const docRef = db.collection('jornadas').doc(id);
        const batch = db.batch();
        batch.update(docRef, updates);
        batchWrites.push(batch);
        batchOps++;
        // commit batch if reached threshold
        if (batchOps >= batchSize) {
          // commit accumulated batches sequentially
          for (const b of batchWrites) {
            try {
              await b.commit();
              succeeded++;
            } catch (e) {
              failed++;
              console.error('Batch commit error:', e.message || e);
            }
          }
          batchWrites.length = 0;
          batchOps = 0;
        }
      }
    }

    // commit remaining batches after page
    if (!DRY && batchWrites.length > 0) {
      for (const b of batchWrites) {
        try {
          await b.commit();
          succeeded++;
        } catch (e) {
          failed++;
          console.error('Batch commit error:', e.message || e);
        }
      }
    }
    // continue to next page
  } // end while

  // write CSV report
  await csvWriter.writeRecords(rows);
  console.log('CSV report written to', REPORT_FILE);
  console.log({ processed, proposed, succeeded, failed, skipped });
  return { processed, proposed, succeeded, failed, skipped };
}

(async () => {
  try {
    console.log('--- migrate_link_images script started ---');
    console.log(`Options: dry-run=${DRY}, confirm-high=${CONFIRM_HIGH}, confirm-threshold=${CONFIRM_THRESHOLD}`);
    const indexObj = await buildImagesIndex();
    const result = await migrateBatch(indexObj, { pageSize: PAGE_SIZE, batchSize: BATCH_SIZE });
    console.log('--- finished ---', result);
    if (DRY) {
      console.log('DRY RUN completed. No writes were executed.');
      console.log('Inspect', REPORT_FILE, 'and adjust heuristics/threshold before enabling writes.');
    } else {
      console.log('Writes completed. Review audit logs and spot-check documents in Firestore.');
    }
    process.exit(0);
  } catch (err) {
    console.error('Fatal error:', err);
    process.exit(2);
  }
})();
