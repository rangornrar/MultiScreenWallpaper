# Release Checklist

## Before publishing
- Confirm that `dist/WallCraft.exe` launches correctly on Windows 10 and Windows 11.
- Check that the README screenshots still match the current interface.
- Update the version number in the release title.
- Write a short changelog using `RELEASE_NOTES_TEMPLATE.md`.
- Verify that the download page in `html/` still points to the correct binary.

## GitHub release
- Push the latest commit to GitHub.
- Open the repository releases page: https://github.com/rangornrar/MultiScreenWallpaper/releases
- Create a new release and attach `WallCraft.exe`.
- Paste the notes from `RELEASE_NOTES_TEMPLATE.md`.
- Publish the release.

## After publishing
- Check that the releases page displays the new version and asset.
- Update any version mention inside the landing pages if needed.
- Share the release URL instead of the direct repository file when possible.
