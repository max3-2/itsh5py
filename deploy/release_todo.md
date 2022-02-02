Steps to take when releasing a new version:
* Bump version number and enter current date in `itsh5py/__init__.py`.
* Add the release notes to `docs/releases.md`.
* Add a dedicated commit for the version bump.
* Tag the commit with the version number, use git tag -a tagname to specify message
* Push the commit (but not the tag)
* Check that documentation built successfully on Read-the-Docs.
* Publish to PyPI by running `deploy/publish.py`.
* Check that meta information is correct on PyPI.
* Then push the tag
* Create a new release on GitHub and add the release notes.
