# Setting up the content manager

The admin lives at **bftdfilms.com/admin**. It edits `content.json` in this
repository through GitHub, so every change is an ordinary commit with history
and rollback.

It will not work until the steps below are done. They are done once, take
about fifteen minutes, and need no command line.

## Quickest route: sign in with a token

You do **not** have to deploy anything. Sveltia offers a **Sign In with Token**
button on the login screen, which needs no backend and no configuration. Use
this to get working today; the OAuth setup below is an improvement you can make
later, and is mainly worth it when someone other than you needs access.

1. Go to **https://github.com/settings/personal-access-tokens/new**
   (Settings → Developer settings → Personal access tokens → **Fine-grained**)
2. Set:
   - **Token name**: `BFTD Content Manager`
   - **Expiration**: 90 days
   - **Resource owner**: `comeallain`
   - **Repository access**: *Only select repositories* → `comeallain/bftd-website`
   - **Permissions** → Repository permissions → **Contents: Read and write**
     (Metadata: Read-only is added automatically and is required)
3. **Generate token** and copy it.
4. Go to **https://bftdfilms.com/admin**, click **Sign In with Token**, paste it.

The token stays in your browser. It is not committed anywhere.

> This is deliberately narrower than the credential that was used by the old
> "BFTD Content Manager": fine-grained, limited to this one repository, able to
> change file contents and nothing else, and it expires. If it ever leaks, the
> blast radius is this repo's files for 90 days rather than your whole account
> indefinitely.
>
> If a fine-grained token is rejected, a classic token with the `repo` scope
> will work, but prefer fine-grained.

### Why bother with OAuth later

Token sign-in means handing a person a credential. For your assistant that is
the thing we are trying to avoid — with OAuth they sign in with their own
GitHub account and you revoke access by removing them as a collaborator. So:
token now, OAuth when a second person needs in.

---

## Why there is a setup step at all

GitHub will not let a purely static page log you in. Completing an OAuth login
requires a server to hold a client secret, and a secret placed in a static page
is not a secret. So a small authenticator sits between the admin and GitHub. It
does nothing except complete the login handshake.

**The client secret lives in Cloudflare. It never enters this repository.**

---

## Step 1 — deploy the authenticator

**1.1** If you do not have a Cloudflare account, create one at
**https://dash.cloudflare.com/sign-up**. The free plan is sufficient; no card
is required.

**1.2** Go to **https://github.com/sveltia/sveltia-cms-auth** and click the
**Deploy to Cloudflare** button in the README.

**1.3** Cloudflare will ask to connect to your GitHub account. Authorise it.

> Expect this to create a copy of the `sveltia-cms-auth` repository in your own
> GitHub account. That is normal — Cloudflare builds the Worker from your copy.
> It is a separate repository and does not touch `bftd-website`.

**1.4** Accept the defaults and let it deploy. It takes a minute or two.

**1.5** When it finishes, go to the Cloudflare dashboard →
**Compute (Workers)** → **Workers & Pages** → select **sveltia-cms-auth**.

**1.6** Copy the Worker's URL from the top of that page. It looks like:

```
https://sveltia-cms-auth.something.workers.dev
```

**Keep this. You need it twice.** Call it `WORKER_URL` below.

---

## Step 2 — register the GitHub OAuth app

**2.1** Go to **https://github.com/settings/applications/new**

**2.2** Fill in exactly:

| Field | Value |
|---|---|
| Application name | `BFTD Content Manager` |
| Homepage URL | `https://bftdfilms.com` |
| Authorization callback URL | `WORKER_URL/callback` |

The callback must have **`/callback`** on the end. So if your Worker URL is
`https://sveltia-cms-auth.abc123.workers.dev`, the callback is
`https://sveltia-cms-auth.abc123.workers.dev/callback`.

Getting this wrong is the single most common cause of the login failing.

**2.3** Click **Register application**.

**2.4** Copy the **Client ID** shown on the next page.

**2.5** Click **Generate a new client secret** and copy it immediately —
GitHub shows it once and never again.

> Do not paste the secret into this repository, into a commit message, or into
> a chat window. It goes into Cloudflare in the next step and nowhere else.

---

## Step 3 — give the Worker its credentials

**3.1** Back in Cloudflare: **Workers & Pages** → **sveltia-cms-auth** →
**Settings** → **Variables and Secrets**.

**3.2** Add these three:

| Name | Value | Type |
|---|---|---|
| `GITHUB_CLIENT_ID` | the Client ID from 2.4 | Text |
| `GITHUB_CLIENT_SECRET` | the secret from 2.5 | **Secret / Encrypt** |
| `ALLOWED_DOMAINS` | `bftdfilms.com` | Text |

`ALLOWED_DOMAINS` is optional in the authenticator's own documentation but you
should set it. Without it, anyone who discovers your Worker URL can use your
authenticator to start a login flow from their own website.

**3.3** Save, then **redeploy the Worker**. Variables do not take effect until
you do. There is a Deploy button on the Worker's page.

---

## Step 4 — point the admin at the Worker

In `admin/config.yml`, under `backend:`, add the Worker URL:

```yaml
backend:
  name: github
  repo: comeallain/bftd-website
  branch: main
  base_url: https://sveltia-cms-auth.something.workers.dev
```

Note: `base_url` is the Worker URL **without** `/callback`. Only the GitHub
OAuth app needs that suffix.

Commit it. Once the site rebuilds, go to **https://bftdfilms.com/admin** and
sign in with GitHub.

---

## If the login fails

| What you see | Almost always |
|---|---|
| GitHub says the redirect URI does not match | The callback URL in step 2.2 is missing `/callback`, or has a trailing slash |
| Login window opens then closes with nothing | `GITHUB_CLIENT_ID` or `GITHUB_CLIENT_SECRET` is wrong, or the Worker was not redeployed after 3.3 |
| "Not allowed" or the flow refuses to start | `ALLOWED_DOMAINS` does not include `bftdfilms.com` |
| Admin loads but shows no content | `base_url` is missing from `config.yml`, or has a trailing slash |
| 404 at /admin | The site has not rebuilt yet — check Actions |

---

## Giving someone else access

Add them as a collaborator on this repository with **write** permission:
Settings → Collaborators. That is all. They sign in at `/admin` with their own
GitHub account. Remove them the same way. Nobody needs a token and nobody
shares a password.

## The one rule

**Every key in `content.json` must be declared in `admin/config.yml`.**

The CMS rewrites the whole file from the fields it knows about, so an
undeclared key is deleted on the first save — silently.
`tools/check_cms_config.py` runs in CI and fails the build if that is ever
true, so you find out from a red tick rather than a blank page.

## Updating the CMS

The Sveltia bundle is committed here rather than loaded from a CDN, because it
has write access to this repository when someone is signed in, and a pinned
copy cannot be swapped underneath you. Current version is in
`.sveltia-version`.

```bash
bash tools/update-cms.sh          # latest
bash tools/update-cms.sh 0.208.1  # a specific version
```
