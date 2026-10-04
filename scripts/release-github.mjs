import { execFileSync } from 'node:child_process';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { loadBundle, verifySource } from './release-bundle.mjs';

// Injected transport makes every retry and immutability guard testable offline.
export async function ensureDraft(bundle, transport) {
  const { manifest, assets } = bundle;
  let release = await transport.find(manifest.tag);
  const expected = new Map(assets.map(asset => [asset.name, asset]));
  if (release) {
    if (release.tag_name !== manifest.tag) throw new Error('Release tag mismatch');
    if (release.target_commitish !== manifest.commit) throw new Error('Release target differs from verified commit');
    const names = new Set();
    // Read and compare everything before performing any writes. Never clobber.
    for (const asset of release.assets) {
      if (names.has(asset.name) || !expected.has(asset.name) || asset.state !== 'uploaded') throw new Error('Conflicting or incomplete release asset');
      names.add(asset.name);
      const remote = await transport.download(asset);
      if (!remote.equals(expected.get(asset.name).bytes)) throw new Error(`Existing asset differs: ${asset.name}`);
    }
    if (!release.draft) {
      if (names.size !== expected.size) throw new Error('Published release missing expected assets; immutable');
      return { status: 'already-published', url: release.html_url };
    }
    if (release.immutable) throw new Error('Immutable release cannot be modified');
  } else {
    // The production transport uses --verify-tag and --draft, never implicit tags.
    await transport.guard?.();
    await transport.create(manifest);
    release = await transport.find(manifest.tag);
    if (!release || !release.draft || release.tag_name !== manifest.tag || release.target_commitish !== manifest.commit || release.assets.length) throw new Error('Unexpected release after creation; inspect before retry');
  }
  for (const asset of assets) {
    // Detect human publication/edits before each write. GitHub has no atomic
    // "upload only if still draft" operation: publish only after this run ends.
    const current = await transport.find(manifest.tag);
    if (!current?.draft || current.immutable || current.id !== release.id || current.tag_name !== manifest.tag || current.target_commitish !== manifest.commit) throw new Error('Draft changed before upload; inspect before retry');
    const seen = new Set();
    for (const existing of current.assets) {
      if (seen.has(existing.name) || !expected.has(existing.name) || existing.state !== 'uploaded') throw new Error('Draft assets changed before upload');
      seen.add(existing.name);
      if (!(await transport.download(existing)).equals(expected.get(existing.name).bytes)) throw new Error('Draft asset differs before upload');
    }
    if (seen.has(asset.name)) continue;
    await transport.guard?.();
    await transport.upload(release, asset);
  }
  const result = await transport.find(manifest.tag);
  if (!result?.draft || result.tag_name !== manifest.tag || result.target_commitish !== manifest.commit || result.assets.length !== assets.length) throw new Error('Draft changed during upload; inspect before retry');
  for (const local of assets) {
    const remote = result.assets.filter(asset => asset.name === local.name);
    if (remote.length !== 1 || remote[0].state !== 'uploaded' || !(await transport.download(remote[0])).equals(local.bytes)) throw new Error('Post-upload verification failed');
  }
  return { status: 'draft', url: result.html_url };
}

export function githubTransport(repository, execute = args => execFileSync('gh', args, { maxBuffer: 64 * 1024 * 1024 }), guard = () => {}) {
  if (!/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(repository)) throw new Error('Invalid repository');
  const gh = execute;
  return {
    guard,
    find(tag) {
      // Listing includes authenticated drafts. Tag lookup alone can omit drafts.
      const pages = JSON.parse(gh(['api', '--paginate', '--slurp', `repos/${repository}/releases?per_page=100`]).toString('utf8'));
      const matches = pages.flat().filter(release => release.tag_name === tag);
      if (matches.length > 1) throw new Error('Multiple releases for tag');
      return matches[0] ?? null;
    },
    download(asset) { return gh(['api', `repos/${repository}/releases/assets/${asset.id}`, '-H', 'Accept: application/octet-stream']); },
    create(manifest) {
      gh(['release', 'create', manifest.tag, '--repo', repository, '--verify-tag', '--draft', '--target', manifest.commit, '--title', manifest.tag, '--notes', `Verified npm archive for ${manifest.package}@${manifest.version}.\nCommit: ${manifest.commit}\nReview the manifest and SHA256SUMS before publishing this draft.`]);
    },
    upload(release, asset) {
      gh(['release', 'upload', release.tag_name, asset.path, '--repo', repository]);
    },
  };
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const identity = { tag: process.env.GITHUB_REF_NAME, commit: process.env.GITHUB_SHA, repository: process.env.GITHUB_REPOSITORY };
  verifySource(identity);
  const result = await ensureDraft(loadBundle(process.argv[2] ?? 'dist', identity), githubTransport(identity.repository, undefined, () => verifySource(identity)));
  console.log(JSON.stringify(result));
}
