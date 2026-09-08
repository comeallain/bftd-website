# Setting up the content manager

The admin lives at **bftdfilms.com/admin**. It edits `content.json` in this
repository through GitHub, so every change is an ordinary commit with history
and rollback.

It will not work until the two steps below are done. They are done once.

## Why there is a step at all

GitHub does not allow a purely static page to log you in — that requires a
server to hold the OAuth client secret, because a secret in a static page is
not a secret. So a small authenticator sits between the admin and GitHub. It
is about fifty lines, it is free to run, and it does nothing except complete
the login handshake.

**The client secret goes into Cloudflare, never into this repository.**

## Step 1 — deploy the authenticator

1. Sign in to Cloudflare (or sign up — free).
2. Go to **https://github.com/sveltia/sveltia-cms-auth** and use the
   *Deploy to Cloudflare* button. No command line needed.
3. When it finishes, open Workers & Pages in the Cloudflare dashboard, select
   **sveltia-cms-auth**, and copy its URL. It looks like
   `https://sveltia-cms-auth.something.workers.dev`.

## Step 2 — register the GitHub OAuth app

1. Go to **https://github.com/settings/developers** → *New OAuth App*.
2. Fill in:
   - **Application name**: `BFTD Content Manager`
   - **Homepage URL**: `https://bftdfilms.com`
   - **Authorization callback URL**: your Worker URL from step 1, with
     `/callback` on the end —
     `https://sveltia-cms-auth.something.workers.dev/callback`
3. Register it, then **Generate a new client secret**.
4. Back in Cloudflare, open the **sveltia-cms-auth** Worker →
   Settings → Variables, and add:

   | Variable | Value |
   |---|---|
   | `GITHUB_CLIENT_ID` | from the OAuth app |
   | `GITHUB_CLIENT_SECRET` | from the OAuth app — mark it **encrypted** |
   | `ALLOWED_DOMAINS` | `bftdfilms.com` |

   `ALLOWED_DOMAINS` matters: without it, anyone who finds the Worker URL can
   use your authenticator to start a login flow from their own site.

## Step 3 — point the admin at it

In `admin/config.yml`, under `backend:`, add the Worker URL:

```yaml
backend:
  name: github
  repo: comeallain/bftd-website
  branch: main
  base_url: https://sveltia-cms-auth.something.workers.dev
```

Commit that and you are done. Go to **bftdfilms.com/admin**, sign in with
GitHub, and you should see the content.

## Giving someone else access

Add them as a collaborator on this repository with **write** permission:
Settings → Collaborators. That is the whole of it — they sign in at
`/admin` with their own GitHub account. Remove them the same way. Nobody
needs a token and nobody shares a password.

## The one rule

**Every key in `content.json` must be declared in `admin/config.yml`.**

The CMS rewrites the whole file from the fields it knows about, so an
undeclared key is deleted on the first save — silently. `tools/check_cms_config.py`
runs in CI and fails the build if that is ever true, so you will find out from
a red tick rather than from a blank page.

## Updating the CMS

The Sveltia bundle is committed here rather than loaded from a CDN, because it
has write access to the repository when someone is signed in and a pinned copy
cannot be swapped underneath you. Current version is in `.sveltia-version`.

```bash
bash tools/update-cms.sh          # latest
bash tools/update-cms.sh 0.208.1  # a specific version
```
