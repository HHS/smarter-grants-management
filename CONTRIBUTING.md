
# How to Contribute as an External Contributor

🎉 First off, thanks for taking the time to contribute! 🎉

We're so thankful you're considering contributing to an [open source project of the U.S. government](https://code.gov/)! If you're unsure about anything, just ask -- or submit the issue or pull request anyway. The worst that can happen is you'll be politely asked to change something. We appreciate all friendly contributions.

We encourage you to read this project's CONTRIBUTING-EXTERNAL policy (you are here), its [LICENSE](LICENSE.md), and its [README](README.md).


## How Can I Contribute?

There are a number of ways to contribute to this project.

### Report a Bug

If you think you have found a bug in the code or static site, [search our issues list](https://github.com/HHS/smarter-grants-management/issues) on GitHub for any similar bugs. If you find a similar bug, please update that issue with your details.

If you do not find your bug in our issues list, file a bug report. When reporting the bug, please follow these guidelines:

- **Please create an issue**
- **Use a clear and descriptive issue title** for the issue to identify the problem.
- **Describe the exact steps to reproduce the problem** in as much detail as possible. For example, start by explaining how you got to the page where you encountered the bug and what you were attempting to do when the bug occurred.
- **Describe the behavior you observed after following the steps** and point out what exactly is the problem with that behavior.
- **Explain which behavior you expected to see instead and why.**
- **Include screenshots and animated GIFs** if possible, which show you following the described steps and clearly demonstrate the problem.
- **If the problem wasn't triggered by a specific action**, describe what you were doing before the problem happened.

### Suggest an Enhancement

If you don't have specific language or code to submit but would like to suggest a change, request a feature, or have something addressed, you can open an issue in this repository.

In this issue, please describe the use case for the feature you would like to see -, what you need, why you need it, and how it should work. Team members will respond to the Feature request as soon as possible. Often, Feature request suggestions undergo a collaborative discussion with the community to help refine the need for the feature and how it can be implemented.

## Code Contributions

The following guidelines are for code contributions. Please see [DEVELOPMENT.md](./DEVELOPMENT.md) for more information about the software development lifecycle on the project.

### Getting Started

This project is monorepo with several apps. Please see the [api](./api/README.md) and [frontend](./frontend/README.md) READMEs for information on spinning up those projects locally. Also see the project [documentation](./documentation) for more info.

### Workflow and Branching

This project follows [trunk-based development](./DEVELOPMENT.md#branching-model), so all contributions are directed toward the `main` branch.

1.  Fork the project
1.  Check out the `main` branch
1.  Create a feature branch using [the naming convention mentioned here](./DEVELOPMENT.md#branch-naming-convention)
1.  Write code and tests for your change
1.  From your branch, make a pull request against `hhs/smarter-grants-management/main` using [the naming convention mentioned here](./DEVELOPMENT.md#pull-request-title)
1.  Work with repo maintainers to get your change reviewed
1.  Wait for your change to be pulled into `hhs/smarter-grants-management/main`

### Testing, Coding Style and Linters

Each application has its own testing and linters. Every commit is tested to adhere to tests and the linting guidelines. It is recommended to run tests and linters locally before committing.

### Issues

External contributors should use the _Bug Report_ or _Feature Request_ [issue templates](https://github.com/HHS/smarter-grants-management/issues/new/choose).

### Pull Requests

Pull requests should follow the conventions in [DEVELOPMENT.md](./DEVELOPMENT.md) with the following changes:

1. Pull requests should be titled with `[Issue N] Description`. However if there is no issue, use `[External] Description` format.
1. External contributors can't merge their own PRs, so an internal team member will pull in after changes are satisfactory.

### Review Assignment

This repository uses a hybrid review assignment model powered by a GitHub Action rather than the traditional CODEOWNERS file.

**For external contributors (community/fork PRs):**
When you open a pull request from a fork, we request that you tag one or all of our designated maintainers to review your PR prior to us merging it.

Current designated maintainers:

- @btabaska
- @mdragon
- @KevinJBoyer

### Commit Signing

**For SGM, all commits must be cryptographically signed using GPG key.**

#### Setup steps

Use **Terminal** (Mac/Linux) or **Git Bash** (Windows) with GPG installed

##### 1. Generate a GPG Key

Open terminal or git bash from any directory, and run:

```bash
gpg --full-generate-key
```

When prompted, enter:
- **Kind of key:** `1` (RSA and RSA)
- **Key size:** `4096`
- **Expiration:** `0` (does not expire) or `1y` (expires in 1 year)
- **Real name:** Your full name
- **Email address:** Your GitHub-verified email (e.g., `your.name@company.com`)
- **Comment:** Optional field, shows up when managing the GPG keys list, input as needed or leave blank
- **Passphrase:** (Pop in a separate window) Create a strong passphrase - required when signing commits

##### 2. Get Your GPG Key ID

List your GPG keys to find the key ID:

```bash
gpg --list-secret-keys --keyid-format=long
```

Example output:
```
sec   rsa4096/B5690EEEBB952194 2026-09-28 [SC]
              ↑ This is your key ID
uid           [ultimate] Your Name <your.email@company.com>
```

Copy the key ID (e.g., `B5690EEEBB952194`)

##### 3. Configure Git to Use Your GPG Key

Tell Git to automatically sign all commits with your key:

```bash
git config --global user.signingkey YOUR_KEY_ID
git config --global commit.gpgsign true
```

Replace `YOUR_KEY_ID` with your actual key ID from step 2.

##### 4. Add Your GPG Public Key to GitHub

Export your public key:

```bash
gpg --armor --export YOUR_KEY_ID
```

This outputs your public key. Copy the entire output, including:
```
-----BEGIN PGP PUBLIC KEY BLOCK-----
...
-----END PGP PUBLIC KEY BLOCK-----
```

Then add it to GitHub:
1. Go to [GitHub Settings > SSH and GPG keys](https://github.com/settings/keys)
2. Click **"New GPG key"**
3. Add a title, and paste your public key
4. Click **"Add GPG key"**

##### 5. Verify Your Email on GitHub

**Important:** GitHub will only show commits as "Verified" if the email in your GPG key is verified on GitHub.

1. Go to [GitHub Settings > Emails](https://github.com/settings/emails)
2. If your email isn't listed, click **"Add email address"** and add it
3. Check your email inbox for a verification link from GitHub
4. Click the link to verify your email

##### 6. Verify Your Setup

Test that commit signing is working:

```bash
# Check your Git config
git config user.signingkey
git config commit.gpgsign

# Make a test commit

# Verify the commit is signed
git log --show-signature -1
```

You should see:
```
gpg: Signature made ...
gpg: Good signature from "Your Name <your.email@company.com>"
```

#### Using Multiple Email Addresses

GPG key accepts multiple email addresses, when you use different emails for Github account and local Git configuration

```bash
# Edit your GPG key
gpg --edit-key YOUR_KEY_ID

# In the GPG prompt, type:
adduid

# Enter your additional email address
# Then type:
save
```

After adding emails, re-export and update your GPG key on GitHub (repeat step 4), and verify all emails on GitHub (step 5).

#### Troubleshooting

**Problem: Push rejected with "Commits must have verified signatures"**

If you still see this issue after adding the key, it could be **email mismatch:** the email in your commit doesn't match your GPG key email
   ```bash
   # Check your Git email
   git config user.email
   
   # Check your GPG key email
   gpg --list-secret-keys --keyid-format=long
   
   # If they don't match, either:
   # - Change Git email to match GPG key: git config --global user.email "email-from-gpg-key"
   # - Or add the Git email to your GPG key (see "Using Multiple Email Addresses")
   ```

For more details, see [GitHub's guide on signing commits](https://docs.github.com/en/authentication/managing-commit-signature-verification/signing-commits).

## Non-Technical Contributions

### Documentation

To contribute to documentation you find in this repository, feel free to use the GitHub user interface to submit a pull request for your changes. Find more information about using the GitHub user interface for PRs here.

### Contribute to community discussions

📧 Reach out for support directly using [simpler@grants.gov](mailto:simpler@grants.gov)

### Sharing your story

Sharing how you or your organization have used the Smarter Grants Management project is an important way for us to raise awareness about the project and its impact. Please tell us your story by [sending us an email at `simpler-grants-gov@hhs.gov`](mailto:simpler-grants-gov@hhs.gov).


## Policies

### Open Source Policy

We adhere to the [HHS Open Source Policy](https://github.com/CMSGov/cms-open-source-policy). If you have any questions, just [shoot us an email](<mailto:simpler@grants.gov?subject=Question About Open Source Policy>).

### Security and Responsible Disclosure Policy

The Department of Health and Human Services is committed to ensuring the security of the American public by protecting their information from
unwarranted disclosure. We want security researchers to feel comfortable reporting vulnerabilities they have discovered so we can fix them and keep our users safe. We developed our disclosure policy to reflect our values and uphold our sense of responsibility to security researchers who share their expertise with us in good faith.

_Submit a vulnerability:_ Unfortunately, we cannot accept secure submissions via email or via GitHub Issues. Please use our website to submit vulnerabilities at [https://hhs.responsibledisclosure.com](https://hhs.responsibledisclosure.com). HHS maintains an acknowledgements page to recognize your efforts on behalf of the American public, but you are also welcome to submit anonymously.

Review the HHS Disclosure Policy and websites in scope:
[https://www.hhs.gov/vulnerability-disclosure-policy/index.html](https://www.hhs.gov/vulnerability-disclosure-policy/index.html).

This policy describes _what systems and types of research_ are covered under this policy, _how to send_ us vulnerability reports, and _how long_ we ask security researchers to wait before publicly disclosing vulnerabilities.

If you have other cybersecurity related questions, please contact us at [csirc@hhs.gov](mailto:csirc@hhs.gov).

## Public domain

This project is in the public domain within the United States, and copyright and related rights in the work worldwide are waived through the [CC0 1.0 Universal public domain dedication](https://creativecommons.org/publicdomain/zero/1.0/).

All contributions to this project will be released under the CC0 dedication. By submitting a pull request or issue, you are agreeing to comply with this waiver of copyright interest.